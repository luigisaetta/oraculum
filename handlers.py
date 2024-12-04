"""
File name: handlers.py
Author: Luigi Saetta
Date last modified: 2024-11-26
Python Version: 3.11

Description:
    Implements the handling logic for the various
    routing options

Inspired by:
   
Usage:
    Import this module into other scripts to use its functions. 
    Example:

Dependencies:
    langChain

License:
    This code is released under the MIT License.

Notes:
    This is a part of a set of demos showing how to build a SQL Agent
    for Text2SQL tasks

Warnings:
    This module is in development, may change in future versions.
"""

import asyncio
from time import time
from typing import Any
from langchain_core.messages import HumanMessage, SystemMessage
from config_reader import ConfigReader
from llm_manager import LLMManager
from conversation_manager import ConversationManager
from sql_agent_factory import sql_agent_factory
from sql_cache import SQLCache
from prompts_models import PREAMBLE_ANSWER_DIRECTLY, PREAMBLE_ANALYZE_DATA
from config_private import COMPARTMENT_OCID
from utils import get_console_logger

logger = get_console_logger()
config = ConfigReader("./config.toml")

VERBOSE = bool(config.find_key("verbose"))
MAX_MSGS = config.find_key("max_msgs")

llm_manager = LLMManager(
    config,
    compartment_id=COMPARTMENT_OCID,
    logger=logger,
)
# it is a singleton
conversation_manager = ConversationManager(max_msgs=MAX_MSGS, verbose=VERBOSE)

# it is a singleton
sql_cache = SQLCache(max_size=1000)

# 0.1 sec
SMALL_STIME = 0.1


async def stream_markdown_table(rows):
    """
    Stream rows of data as a Markdown table with padded columns.
    """
    if not rows:
        return

    # Get headers and calculate maximum column widths
    headers = rows[0].keys()
    column_widths = {key: len(key) for key in headers}  # Start with header widths

    # Update column widths based on row contents
    for row in rows:
        for key, value in row.items():
            column_widths[key] = max(column_widths[key], len(str(value)))

    # Generate the header row with padding
    header_row = (
        "| " + " | ".join(f"{key:<{column_widths[key]}}" for key in headers) + " |"
    )
    separator_row = (
        "| " + " | ".join(f"{'-' * column_widths[key]}" for key in headers) + " |"
    )
    yield header_row + "\n"
    yield separator_row + "\n"

    # Stream each row with padded columns
    for row in rows:
        await asyncio.sleep(0.1)  # Simulate delay
        data_row = (
            "| "
            + " | ".join(
                f"{str(row.get(key, '')):<{column_widths[key]}}" for key in headers
            )
            + " |"
        )
        yield data_row + "\n"


async def handle_generate_sql(user_request: Any):
    """
    Handle SQL generation requests.

    user_request: request in NL
    """
    # if we want to return the txt of the generated SQL
    return_sql = bool(config.find_key("return_sql"))
    # the threshold for distance. Below two req are considered the same
    zero_distance = float(config.find_key("zero_distance"))

    # get the SQL agent defined by config
    sql_agent = sql_agent_factory(config)

    # send a first progress update to the client
    yield f"✨ Generating SQL for: {user_request.request_text} ✨\n\n"

    # check if the request is already in cache
    _sql_from_cache, _ = sql_cache.get(user_request.request_text)

    if _sql_from_cache is not None:
        # exact match
        logger.info("Find request in cache, exact match...")
        gen_sql = _sql_from_cache
    else:
        # try to find one very close
        _sql_from_cache = sql_cache.find_closer_with_threshold(
            user_request.request_text, zero_distance
        )

        if _sql_from_cache is not None:
            # found in cache
            gen_sql = _sql_from_cache
        else:
            # generate
            time_start = time()
            gen_sql = sql_agent.generate_sql(user_request.request_text)
            time_elapsed = round(time() - time_start, 1)

            # add in cache
            sql_cache.set(user_request.request_text, gen_sql, time_elapsed)

    if return_sql:
        # return the text of SQL
        yield f"SQL:\n{gen_sql}\n\n"

    # execute the sql and return results
    # result must be a list of dict
    yield "SQL results: \n\n"
    rows = sql_agent.execute_sql(gen_sql)

    # add the data retrieved in the conversation, as system message
    rows_as_str = "\n".join(str(item) for item in rows)
    msg_text = (
        f"Data retrieved for request: {user_request.request_text}:\n{rows_as_str}"
    )

    # data retrieved are added to the conversation history as a SYSTEM message
    conversation_manager.add_message(
        user_request.conv_id, SystemMessage(content=msg_text)
    )

    # streaming, results are sent as markdown
    async for markdown_line in stream_markdown_table(rows):
        yield markdown_line
    yield "\n"


async def handle_analyze_data(user_request: Any):
    """
    Handle text analysis requests.
    """
    verbose = bool(config.find_key("verbose"))
    # the model to be used
    model_index = config.find_key("index_model_analyze_data")

    # Start with preamble
    all_messages = [SystemMessage(content=PREAMBLE_ANALYZE_DATA)]
    message_history = conversation_manager.get_conversation(user_request.conv_id)
    for msg in message_history:
        all_messages.append(msg)
    all_messages.append(HumanMessage(content=user_request.request_text))

    if verbose:
        logger.info(
            "calling Model %s...",
            llm_manager.get_llm_model_name(model_index),
        )
        logger.info("")

    await asyncio.sleep(SMALL_STIME)
    yield f"Request: {user_request.request_text}\n"
    await asyncio.sleep(SMALL_STIME)
    yield "Answer in preparation...\n\n"

    # call the model
    generator = llm_manager.get_llm_model(model_index).stream(all_messages)

    # need to correctly manage async response
    async for chunk in _wrap_generator(generator):
        yield str(chunk.content)


async def handle_not_allowed(user_request: Any):
    """
    Handle response for not allowed requests.
    """
    await asyncio.sleep(0.1)
    yield f"Request: {user_request.request_text} not allowed\n"
    await asyncio.sleep(0.1)
    yield "DDL/DML request are not allowed! \n"


async def _wrap_generator(generator):
    """
    Convert a normal generator in an asynch generator
    to be used bu answer directly

    Args:
        generator: Generatore normale.

    Yields:
        Value from generator
    """
    for item in generator:
        # make the cycle cooperative
        await asyncio.sleep(0)
        yield item


async def handle_answer_directly(user_request: Any):
    """
    Handle direct request to Chat model.
    """
    verbose = bool(config.find_key("verbose"))
    model_index = config.find_key("index_model_answer_directly")

    # Start with preamble
    all_messages = [SystemMessage(content=PREAMBLE_ANSWER_DIRECTLY)]
    message_history = conversation_manager.get_conversation(user_request.conv_id)
    for msg in message_history:
        all_messages.append(msg)
    all_messages.append(HumanMessage(content=user_request))

    if verbose:
        logger.info(
            "calling Model %s...",
            llm_manager.get_llm_model_name(model_index),
        )
        logger.info("")

    await asyncio.sleep(SMALL_STIME)
    yield f"Request: {user_request.request_text}\n"
    await asyncio.sleep(SMALL_STIME)
    yield "Answer in preparation...\n\n"

    # call the model
    generator = llm_manager.get_llm_model(model_index).stream(all_messages)

    # need to correctly manage async response
    async for chunk in _wrap_generator(generator):
        yield str(chunk.content)
