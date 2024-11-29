"""
File name: router_with_disptacher.py
Author: Luigi Saetta
Date last modified: 2024-11-29
Python Version: 3.11

Description:
    Extend the router to use the dispatcher

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

from typing import Any
from dispatcher import Dispatcher
from llm_manager import LLMManager
from router import Router
from prompt_routing import AllowedValues


class RouterWithDispatcher(Router):
    """
    Extension of the router to use the dispatcher
    """

    def __init__(self, config, llm_manager: LLMManager, dispatcher: Dispatcher):
        super().__init__(config, llm_manager)
        self.dispatcher = dispatcher

    async def route_request(self, user_request: Any):
        """
        Route the user request after classification.

        Args:
            user_request (str): User's input request.

        Returns:
            Stream: Streaming response from the dispatcher.
        """
        classification = self.classify(user_request.request_text)

        if classification == AllowedValues.NOT_DEFINED.value:
            return "Unable to classify the request."

        return await self.dispatcher.dispatch(classification, user_request)
