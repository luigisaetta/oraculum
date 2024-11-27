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
from typing import List
from langchain_core.messages import HumanMessage, SystemMessage
from config_reader import ConfigReader
from llm_manager import LLMManager
from prompts_models import PREAMBLE_ANSWER_DIRECTLY
from config_private import COMPARTMENT_OCID
from utils import get_console_logger


logger = get_console_logger()
config = ConfigReader("./config.toml")
llm_manager = LLMManager(
    config,
    compartment_id=COMPARTMENT_OCID,
    logger=logger,
)

# 0.1 sec
SMALL_STIME = 0.1


async def handle_generate_sql(user_request: str, message_history: List = None):
    """
    Handle SQL generation requests.
    """
    # simulate
    yield f"SQL generation for: {user_request}\n"

    await asyncio.sleep(5)
    yield "SQL generated:\n"
    for i in range(3):
        await asyncio.sleep(0.1)
        yield f"SQL Part {i + 1}\n"

    # here we should simulate the table of results
    await asyncio.sleep(3)
    yield "\n"
    yield "SQL results\n"


async def handle_analyze_data(user_request: str, message_history: List = None):
    """
    Handle text analysis requests.
    """
    # simulate
    await asyncio.sleep(2)
    yield f"Report generated for: {user_request}\n"
    for i in range(3):
        await asyncio.sleep(0.1)
        yield f"Analysis Part {i + 1}\n"


async def handle_not_allowed(user_request: str, message_history: List = None):
    """
    Handle response for not allowed requests.
    """
    await asyncio.sleep(0.1)
    yield f"Request: {user_request} not allowed\n"
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


async def handle_answer_directly(user_request: str, message_history: List = None):
    """
    Handle direct request to Chat model.
    """
    verbose = bool(config.find_key("verbose"))
    model_index = config.find_key("index_model_answer_directly")

    # Start with preamble
    all_messages = [SystemMessage(content=PREAMBLE_ANSWER_DIRECTLY)]
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
    yield f"Request: {user_request}\n"
    await asyncio.sleep(SMALL_STIME)
    yield "Answer in preparation...\n\n"

    # call the model
    generator = llm_manager.get_llm_model(model_index).stream(all_messages)

    # need to correctly manage async response
    async for chunk in _wrap_generator(generator):
        yield str(chunk.content)
