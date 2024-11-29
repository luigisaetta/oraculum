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
from typing import Any
from langchain_core.messages import HumanMessage, SystemMessage
from config_reader import ConfigReader
from llm_manager import LLMManager
from conversation_manager import ConversationManager
from sql_agent import SQLAgent
from select_ai_sql_agent import SelectAISQLAgent
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


def sql_agent_factory(_config: ConfigReader) -> SQLAgent:
    """
    get from config the sql_agent type
    """
    agent_type = _config.find_key("sql_agent_type")

    if agent_type == "select_ai":
        # implementation is with Select AI
        return SelectAISQLAgent(config)

    # if we arrive here: error
    raise ValueError(f"Unknown SQL agent type: {agent_type}")


async def handle_generate_sql(user_request: Any):
    """
    Handle SQL generation requests.

    user_request: request in NL
    """
    # get the agent
    sql_agent = sql_agent_factory(config)

    yield f"SQL generation for: {user_request.request_text}\n\n"
    gen_sql = sql_agent.generate_sql(user_request.request_text)
    yield f"SQL:\n{gen_sql}\n\n"

    # result must be a list of dict
    yield "SQL results: \n\n"
    rows = sql_agent.execute_sql(gen_sql)

    # add the data retrieved in the conversation, as system message
    rows_as_str = "\n".join(str(item) for item in rows)
    msg_text = (
        f"Data retrieved for request: {user_request.request_text}:\n{rows_as_str}"
    )

    conversation_manager.add_message(
        user_request.conv_id, SystemMessage(content=msg_text)
    )

    # streaming, results are sent as markdown
    async for markdown_line in stream_markdown_table(rows):
        yield markdown_line


async def handle_analyze_data(user_request: Any):
    """
    Handle text analysis requests.
    """
    verbose = bool(config.find_key("verbose"))
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
