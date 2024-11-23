"""
File name: llm_manager.py
Author: Luigi Saetta
Date last modified: 2024-10-21
Python Version: 3.11

Description:
    Encapsulate the managemnt of LLM models

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

from langchain_community.chat_models.oci_generative_ai import ChatOCIGenAI
from config_reader import ConfigReader

# get onfiguration
config = ConfigReader("config.toml")
AUTH_TYPE = config.find_key("auth_type")
MAX_TOKENS = config.find_key("max_tokens")


class LLMManager:
    """
    The class handle all the LLM-related tasks
    """

    def __init__(
        self, model_list, model_endpoints, compartment_id, temperature, logger
    ):
        self.model_list = model_list
        self.model_endpoints = model_endpoints
        self.compartment_id = compartment_id
        self.temperature = temperature
        self.logger = logger
        self.llm_models = self.initialize_models()

    def initialize_models(self):
        """
        Initialise the list of ChatModels to be used to generate SQL
        """
        self.logger.info("LLMManager: Initialising the list of models...")

        models = []
        for model, endpoint in zip(self.model_list, self.model_endpoints):
            self.logger.info("Model: %s", model)

            models.append(
                ChatOCIGenAI(
                    # modified to support non-default auth (inst_princ..)
                    auth_type=AUTH_TYPE,
                    model_id=model,
                    service_endpoint=endpoint,
                    compartment_id=self.compartment_id,
                    model_kwargs={
                        "temperature": self.temperature,
                        "max_tokens": MAX_TOKENS,
                    },
                )
            )
        return models

    def get_llm_models(self):
        """
        return the list of initialised models
        """
        return self.llm_models
