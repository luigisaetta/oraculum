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


class LLMManager:
    """
    The class handle all the LLM-related tasks
    """

    def __init__(self, config, compartment_id, logger):
        # save the config
        self.config = config
        self.compartment_id = compartment_id
        self.logger = logger
        self.llm_models = self.initialize_models()

    def initialize_models(self):
        """
        Initialise the list of ChatModels to be used to generate SQL
        """
        verbose = bool(self.config.find_key("verbose"))

        if verbose:
            self.logger.info("LLMManager: Initialising the list of models...")

        models_list = self.config.find_key("models_list")
        models_endpoints = self.config.find_key("models_endpoints")

        models = []
        for model, endpoint in zip(models_list, models_endpoints):
            if verbose:
                self.logger.info("Model: %s", model)

            models.append(
                ChatOCIGenAI(
                    # modified to support non-default auth (inst_princ..)
                    auth_type=self.config.find_key("auth_type"),
                    model_id=model,
                    service_endpoint=endpoint,
                    compartment_id=self.compartment_id,
                    model_kwargs={
                        "temperature": self.config.find_key("temperature"),
                        "max_tokens": self.config.find_key("max_tokens"),
                    },
                )
            )
        return models

    def get_llm_models(self):
        """
        return the list of initialised models
        """
        return self.llm_models

    def get_llm_model_name(self, model_index):
        """
        get the name of a model (see config.toml)
        """
        models_list = self.config.find_key("models_list")

        return models_list[model_index]

    def get_llm_model_endpoint(self, model_index):
        """
        get the endpoint of a model (see config.toml)
        """
        models_endpoints = self.config.find_key("models_endpoints")

        return models_endpoints[model_index]

    def get_llm_model(self, model_index):
        """
        added to see if it solves the problem with connections
        """
        model_name = self.get_llm_model_name(model_index)
        endpoint = self.get_llm_model_endpoint(model_index)

        chat = ChatOCIGenAI(
            # modified to support non-default auth (inst_princ..)
            auth_type=self.config.find_key("auth_type"),
            model_id=model_name,
            service_endpoint=endpoint,
            compartment_id=self.compartment_id,
            model_kwargs={
                "temperature": self.config.find_key("temperature"),
                "max_tokens": self.config.find_key("max_tokens"),
            },
        )

        return chat
