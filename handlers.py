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


async def handle_generate_sql(user_request: str, message_history: list = None):
    """
    Handle SQL generation requests.
    """
    for i in range(5):
        await asyncio.sleep(0.4)
        yield f"SQL Part {i + 1} for: {user_request}\n"


async def handle_analyze_data(user_request: str, message_history: list = None):
    """
    Handle text analysis requests.
    """
    for i in range(3):
        await asyncio.sleep(0.4)
        yield f"Analysis Part {i + 1} for: {user_request}\n"


async def handle_not_allowed(user_request: str, message_history: list = None):
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

    Args:
        generator: Generatore normale.

    Yields:
        Value from generator
    """
    for item in generator:
        # make the cycle cooperative
        await asyncio.sleep(0)
        yield item


async def handle_answer_directly(user_request: str, message_history: list = None):
    """
    Handle direct request to Chat model.
    """
    verbose = bool(config.find_key("verbose"))
    index_model_answer_directly = config.find_key("index_model_answer_directly")

    # Start with preamble
    all_messages = [SystemMessage(content=PREAMBLE_ANSWER_DIRECTLY)]
    for msg in message_history:
        all_messages.append(msg)
    all_messages.append(HumanMessage(content=user_request))

    if verbose:
        logger.info(
            "calling Model %s...",
            llm_manager.get_llm_model_name(index_model_answer_directly),
        )
        logger.info("")

    await asyncio.sleep(0.4)
    yield f"Request: {user_request}\n"
    await asyncio.sleep(0.8)
    yield "Answer in preparation...\n\n"

    generator = llm_manager.get_llm_model(index_model_answer_directly).stream(
        all_messages
    )

    async for chunk in _wrap_generator(generator):
        yield str(chunk.content)
