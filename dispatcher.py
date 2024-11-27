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

from typing import List

from prompt_routing import AllowedValues

from handlers import (
    handle_generate_sql,
    handle_analyze_data,
    handle_not_allowed,
    handle_answer_directly,
)
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
            AllowedValues.GENERATE_SQL.value: handle_generate_sql,
            AllowedValues.ANALYZE_DATA.value: handle_analyze_data,
            AllowedValues.ANSWER_DIRECTLY.value: handle_answer_directly,
            AllowedValues.NOT_ALLOWED.value: handle_not_allowed,
            # Add more mappings as needed
        }

    async def dispatch(
        self, classification: str, user_request: str, message_history: List = None
    ):
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

        return handler(user_request, message_history)
