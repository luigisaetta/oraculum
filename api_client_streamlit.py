"""
Client for API v2
"""

import random
import asyncio
import requests

import streamlit as st

from config_reader import ConfigReader
from streamlit_chat_client import StreamlitChatClient
from utils import get_console_logger

config = ConfigReader("./config.toml")
logger = get_console_logger()

API_PORT = int(config.find_key("port"))
API_URL = f"http://localhost:{API_PORT}"
TIMEOUT = float(config.find_key("api_timeout"))

# Define the available operations
NAMES = ["chat_with_data"]

operations = {NAMES[0]: "/streaming_chat"}

client = StreamlitChatClient(API_URL, logger)


def init_session_state():
    """
    Initialise the session state
    """
    if "request_sent" not in st.session_state:
        st.session_state["request_sent"] = False
    if "conv_id" not in st.session_state:
        st.session_state["conv_id"] = str(random.randint(100000, 999999))
    if "user_query" not in st.session_state:
        st.session_state["user_query"] = ""
    if "sql_query" not in st.session_state:
        st.session_state["sql_query"] = "SQL Query"


def reset_conversation():
    """
    reste the conversation on the API end
    """
    # params fo the API call
    conv_id = st.session_state["conv_id"]
    client.delete_conversation(conv_id)
    st.write("Conversation deleted.")


def handle_sidebar():
    """
    to handle the sidebar
    """
    if st.sidebar.button("Reset chat"):
        logger.info("Reset conversation...")
        reset_conversation()

    selected_operation = st.sidebar.selectbox("Select an API Operation", NAMES)

    return selected_operation


def handle_api_request(selected_operation, request_body):
    """Make the API request and handle response."""
    endpoint = API_URL + operations[selected_operation]

    with st.spinner():
        if selected_operation == NAMES[0]:
            response = requests.post(endpoint, json=request_body, timeout=TIMEOUT)
        else:
            response = requests.get(endpoint, timeout=TIMEOUT)

    return response


def main():
    """
    main
    """
    st.set_page_config(initial_sidebar_state="collapsed")
    st.title("🧠 SQL Agent - Client for API async")

    # Handle sidebar inputs and reset
    selected_operation = handle_sidebar()

    # Initialize session state for request_sent if it doesn't exist
    init_session_state()

    if selected_operation in [NAMES[0]]:
        # chat_with_data
        conv_id = st.text_input("Conversation ID", value=st.session_state["conv_id"])
        user_query = st.text_area("User Query", st.session_state.user_query)

        # Update session state if inputs change
        if (
            conv_id != st.session_state["conv_id"]
            or user_query != st.session_state["user_query"]
        ):
            st.session_state["conv_id"] = conv_id
            st.session_state["user_query"] = user_query
            st.session_state["request_sent"] = (
                False  # Allow a new request if inputs change
            )

        # remove blank at beginning and end
        user_query = user_query.strip()

    # API call
    if st.button("Send Request") and not st.session_state["request_sent"]:
        st.info("⏳ Processing your request, please wait...")

        # Mark the request as sent to avoid multiple submissions
        st.session_state["request_sent"] = True

        # Placeholder for markdown content
        output_placeholder = st.empty()

        # Esegui la coroutine e aggiorna il placeholder
        asyncio.run(client.print_result(conv_id, user_query, output_placeholder))

        # Reset the state to allow a new request to be sent
        st.session_state["request_sent"] = False


# Run the app
if __name__ == "__main__":
    main()
