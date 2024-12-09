"""
File name: api_main.py
Author: Luigi Saetta
Date last modified: 2024-11-24
Python Version: 3.11

Description:
    REST API for the AI Assistant

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

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import uvicorn

from conversation_manager import ConversationManager
from llm_manager import LLMManager
from dispatcher import Dispatcher
from router_with_dispatcher import RouterWithDispatcher
from config_reader import ConfigReader
from sql_agent_factory import sql_agent_factory
from utils import get_console_logger

from config_private import COMPARTMENT_OCID
from config_private import DB_USER, DB_PWD, DSN, WALLET_DIR, WALLET_PWD

# create the struct from params in config_private
CONNECT_ARGS = {
    "user": DB_USER,
    "password": DB_PWD,
    "dsn": DSN,
    "config_dir": WALLET_DIR,
    "wallet_location": WALLET_DIR,
    "wallet_password": WALLET_PWD,
}

# media types
TEXT_PLAIN = "text/plain"


class UserRequest(BaseModel):
    """
    Encapsulate the user request
    """

    # Unique conversation ID
    conv_id: str
    request_text: str


logger = get_console_logger()
config = ConfigReader("./config.toml")

VERBOSE = bool(config.find_key("verbose"))
MAX_MSGS = config.find_key("max_msgs")

# Initialize router and dispatcher
llm_manager = LLMManager(
    config,
    compartment_id=COMPARTMENT_OCID,
    logger=logger,
)
dispatcher = Dispatcher(config)
router_w = RouterWithDispatcher(config, llm_manager, dispatcher)

app = FastAPI()

# Initialize ConversationManager
conversation_manager = ConversationManager(max_msgs=MAX_MSGS, verbose=VERBOSE)


@app.post("/streaming_chat")
async def streaming_chat(user_request: UserRequest):
    """
    handle the streaming chat
    """
    # only the text of the request
    request_text = user_request.request_text

    if not request_text.strip():
        raise HTTPException(status_code=400, detail="Request cannot be empty.")

    if VERBOSE:
        logger.info("streaming_chat, received request: %s", request_text)

    # create the conversation, if not exists
    conversation = conversation_manager.get_conversation(user_request.conv_id)

    try:
        response_stream = await router_w.route_request(user_request)

        # TODO add response to history
        return StreamingResponse(response_stream, media_type=TEXT_PLAIN)

    except Exception as e:
        logger.error("Error in streaming_chat: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error") from e


@app.delete("/conversation/{conv_id}")
def delete_conversation(conv_id: str):
    """
    Deletes the conversation history for a given conversation ID.

    Args:
        conv_id (str): The unique identifier for the conversation.

    Returns:
        dict: A message confirming the deletion.
    """
    if conv_id not in conversation_manager.conversations:
        raise HTTPException(status_code=404, detail="Conversation not found.")

    conversation_manager.clear_conversation(conv_id)

    return {
        "message": f"Conversation with ID '{conv_id}' has been deleted successfully."
    }


#
# main
#
if __name__ == "__main__":
    HOST = config.find_key("host")
    PORT = int(config.find_key("port"))

    # tst DB connection is ok
    sql_agent = sql_agent_factory(config)
    sql_agent.get_db_connection()
    logger.info("")
    logger.info(
        "DB connection as %s to DSN: %s OK...",
        CONNECT_ARGS["user"],
        CONNECT_ARGS["dsn"],
    )
    logger.info("")

    uvicorn.run(app, host=HOST, port=PORT)
