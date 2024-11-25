"""
Module: conversation_manager.py
Author: Luigi Saetta
Date last modified: 2024-11-25
Python Version: 3.11

Description:
    This module provides a class-based implementation for managing conversation history 
    in a database-independent format, preparing for external storage while returning
    BaseMessage objects when required.

License:
    This code is released under the MIT License.
"""

from typing import Dict, List, Union
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage
from utils import get_console_logger


class ConversationManager:
    """
    A class to manage conversation history for an AI Assistant.

    Stores messages as dictionaries but reconstructs BaseMessage objects
    when fetching conversation history.

    Attributes:
        verbose (bool): Flag to enable verbose logging.
        max_msgs (int): Maximum number of messages to retain in a conversation.
        logger: Logger instance for logging messages.
    """

    def __init__(self, max_msgs: int, verbose: bool = False):
        """
        Initializes the conversation manager.

        Args:
            max_msgs (int): Maximum number of messages to retain in a conversation.
            verbose (bool): Flag to enable verbose logging. Default is False.
        """
        self.conversations: Dict[str, List[Dict[str, Union[str, None]]]] = {}
        self.max_msgs = max_msgs
        self.verbose = verbose
        self.logger = get_console_logger()

    def _get_role(self, msg):
        """
        get the role from the message type
        """
        if isinstance(msg, HumanMessage):
            role = "human"
        elif isinstance(msg, SystemMessage):
            role = "system"
        elif isinstance(msg, AIMessage):
            role = "ai"
        else:
            role = "unknown"

        return role

    def _message_to_dict(self, msg: BaseMessage) -> Dict[str, Union[str, None]]:
        """
        Converts a BaseMessage to a dictionary format.

        Args:
            msg (BaseMessage): The message object to convert.

        Returns:
            Dict[str, Union[str, None]]: A dictionary with `role` and `content`.
        """
        role = self._get_role(msg)

        return {
            "role": role,
            "content": msg.content,
        }

    def _dict_to_message(self, msg_dict: Dict[str, Union[str, None]]) -> BaseMessage:
        """
        Converts a dictionary back to a BaseMessage based on the role.

        Args:
            msg_dict (Dict[str, Union[str, None]]): The message dictionary.

        Returns:
            BaseMessage: A reconstructed BaseMessage object of the correct type.
        """
        role = msg_dict.get("role")
        content = msg_dict.get("content", "")

        if role == "human":
            return HumanMessage(content=content)
        if role == "system":
            return SystemMessage(content=content)
        if role == "ai":
            return AIMessage(content=content)

        self.logger.warning("Unknown role '%s' encountered in message.", role)
        return BaseMessage(content=content)  # Fallback to generic BaseMessage

    def add_message(self, conv_id: str, msg: BaseMessage):
        """
        Adds a message to the specified conversation.

        If the conversation doesn't exist, it will be created.
        If the conversation exceeds the max_msgs limit, the oldest message is removed.

        Args:
            conv_id (str): The unique identifier for the conversation.
            msg (BaseMessage): The message to add.
        """
        if conv_id not in self.conversations:
            if self.verbose:
                self.logger.info("Creating new conversation with ID: %s", conv_id)
            self.conversations[conv_id] = []

        # Convert the BaseMessage to a dictionary and add it
        # msgs are stored in a format that is independent of LangChain
        conversation = self.conversations[conv_id]
        conversation.append(self._message_to_dict(msg))

        # Trim conversation to maximum allowed messages
        if len(conversation) > self.max_msgs:
            if self.verbose:
                self.logger.info("Trimming conversation with ID: %s", conv_id)
            conversation.pop(0)

    def get_conversation(self, conv_id: str) -> List[BaseMessage]:
        """
        Retrieves the conversation history for a given ID.

        Args:
            conv_id (str): The unique identifier for the conversation.

        Returns:
            List[BaseMessage]: The list of messages reconstructed as BaseMessage objects.
        """
        messages = self.conversations.get(conv_id, [])
        return [self._dict_to_message(msg_dict) for msg_dict in messages]

    def clear_conversation(self, conv_id: str):
        """
        Clears the conversation history for the specified ID.

        Args:
            conv_id (str): The unique identifier for the conversation.
        """
        if conv_id in self.conversations:
            if self.verbose:
                self.logger.info("Clearing conversation with ID: %s", conv_id)
            del self.conversations[conv_id]
