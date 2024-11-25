"""
File name: dispatcher.py
Author: Luigi Saetta
Date last modified: 2024-11-24
Python Version: 3.11

Description:
    Implements the dispatching logic

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
from prompt_routing import AllowedValues
from prompts_models import PREAMBLE_ANSWER_DIRECTLY
from utils import get_console_logger


class Dispatcher:
    """
    Dispatcher to route classified requests to the appropriate handler/tool.
    """

    def __init__(self, config, llm_manager):
        self.logger = get_console_logger()
        self.config = config
        self.llm_manager = llm_manager

        # Mapping classification values to handler functions
        self.tool_map = {
            AllowedValues.GENERATE_SQL.value: self.handle_generate_sql,
            AllowedValues.ANALYZE_DATA.value: self.handle_analyze_data,
            AllowedValues.ANSWER_DIRECTLY.value: self.handle_answer_directly,
            AllowedValues.NOT_ALLOWED.value: self.handle_not_allowed,
            # Add more mappings as needed
        }

    async def dispatch(self, classification: str, user_request: str):
        """
        Route the request to the appropriate handler.

        Args:
            classification (str): Classification from the Router.
            user_request (str): User's input request.

        Returns:
            str: Response from the selected tool or an error message.
        """
        verbose = bool(self.config.find_key("verbose"))

        handler = self.tool_map.get(classification)

        if not handler:
            self.logger.error("No handler found for classification: %s", classification)
            return "Sorry, I don't know how to handle this request."

        if verbose:
            self.logger.info("Dispatching request to handler for: %s", classification)

        return handler(user_request)

    async def handle_generate_sql(self, user_request: str):
        """
        Handle SQL generation requests.

        Args:
            user_request (str): User's input request.

        Yields:
            str: Partial responses for streaming.
        """
        # simulate streaming response
        for i in range(5):
            await asyncio.sleep(0.4)
            yield f"SQL Part {i + 1} for: {user_request}\n"

    async def handle_analyze_data(self, user_request: str):
        """
        Handle text analysis requests.

        Args:
            user_request (str): User's input request.

        Yields:
            str: Partial responses for streaming.
        """
        # simulate streaming response
        for i in range(3):
            await asyncio.sleep(0.4)
            yield f"Analysis Part {i + 1} for: {user_request}\n"

    async def handle_not_allowed(self, user_request: str):
        """
        Handle reponse for not allowed requests
        """
        await asyncio.sleep(0.1)
        yield f"Request: {user_request} not allowed\n"
        await asyncio.sleep(0.1)
        yield "DDL/DML request are not allowed! \n"

    async def _wrap_generator(self, generator):
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

    async def handle_answer_directly(self, user_request: str):
        """
        Handle direct request to Chat model

        Args:
            user_request (str): User's input request.

        Yields:
            str: Partial responses for streaming.
        """
        verbose = bool(self.config.find_key("verbose"))
        index_model_answer_directly = self.config.find_key(
            "index_model_answer_directly"
        )

        messages = [
            # we should add here the conversation history
            SystemMessage(content=PREAMBLE_ANSWER_DIRECTLY),
            HumanMessage(content=user_request),
        ]

        if verbose:
            self.logger.info(
                "calling Model %s...",
                self.llm_manager.get_llm_model_name(index_model_answer_directly),
            )
            self.logger.info("")

        # simulate partial response
        await asyncio.sleep(0.4)
        yield f"Request: {user_request}\n"
        await asyncio.sleep(0.8)
        yield "answer in preparation...\n\n"

        generator = self.llm_manager.get_llm_model(index_model_answer_directly).stream(
            messages
        )

        async for chunk in self._wrap_generator(generator):
            yield str(chunk.content)
