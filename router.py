"""
File name: router.py
Author: Luigi Saetta
Date last modified: 2024-11-16
Python Version: 3.11

Description:
    This file provide a class to handle the routing of user requests
    This class provides the logic (based on LLM) to identify a request 
    and route for right action

Inspired by:
   

Usage:
    Import this module into other scripts to use its functions. 
    Example:


License:
    This code is released under the MIT License.

Notes:
    This is a part of a set of demos showing how to build a SQL Agent
    for Text2SQL taks

Warnings:
    This module is in development, may change in future versions.
"""

from langchain_core.prompts import PromptTemplate

from llm_manager import LLMManager
from prompt_routing import ALLOWED_VALUES, generate_prompt_routing
from prompt_routing import AllowedValues

from config_reader import ConfigReader
from utils import get_console_logger


# this is the JSON schema for the output
json_schema = {
    "title": "classification",
    "description": "the classification of the request.",
    "type": "object",
    "properties": {
        "classification": {
            "type": "string",
            # allowed values
            "enum": ALLOWED_VALUES,
            "description": "the class of the request",
        },
    },
    "required": ["classification"],
}

# get onfiguration
config = ConfigReader("./config.toml")
DEBUG = bool(config.find_key("debug"))
INDEX_MODEL_FOR_ROUTING = config.find_key("index_model_for_routing")


class Router:
    """
    Wraps all the code needed to decide
    what is the type of user request
    """

    def __init__(self, llm_manager: LLMManager):
        """
        Initialize the Router class.

        Args:
            llm_manager (LLMManager): Manager for handling LLM models.
        """
        self.llm_manager = llm_manager
        self.logger = get_console_logger()

    def _is_request_valid(self, request):
        """
        check request is a string, non empty
        """
        if not isinstance(request, str) or not request.strip():
            self.logger.warning("Invalid user_request: must be a non-empty string")

            return False
        return True

    def _get_classification_chain(self):
        """
        create the chain
        """
        prompt_routing = generate_prompt_routing()

        classify_prompt = PromptTemplate.from_template(prompt_routing)

        llm_c = self.llm_manager.llm_models[
            INDEX_MODEL_FOR_ROUTING
        ].with_structured_output(json_schema)

        return classify_prompt | llm_c

    def classify(self, user_request: str) -> str:
        """
        classify in one of this categories:
            generate_sql
            analyze_text
            ...
        """
        if not self._is_request_valid(user_request):
            return AllowedValues.NOT_DEFINED.value

        # the chain
        classification_chain = self._get_classification_chain()

        # invoke the LLM, output is a dict
        try:
            result = classification_chain.invoke({"question": user_request})

            if DEBUG:
                self.logger.info("Router:classify, JSON: %s", result)

            classification_value = result["classification"]
        except KeyError as e:
            self.logger.error(
                "KeyError in Router:classify: Missing key in result: %s", e
            )
            classification_value = None
        except Exception as e:
            self.logger.error("Unexpected error in Router:classify %s", e)
            classification_value = None

        # check that the value is in enum
        if classification_value not in ALLOWED_VALUES:
            self.logger.warning(
                "Classification value not in allowed values: %s", classification_value
            )
            return AllowedValues.NOT_DEFINED.value

        return classification_value

    def get_classification_list(self):
        """
        return the list of allowed values
        """
        return ALLOWED_VALUES
