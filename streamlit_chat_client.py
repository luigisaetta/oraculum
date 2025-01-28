"""
    Client per interagire con l'API AI Assistant con supporto streaming.
"""

import os
from httpx import AsyncClient, Timeout, RequestError
import requests

import streamlit as st
from config_reader import ConfigReader

current_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(current_dir, "config.toml")
config = ConfigReader(config_path)
TIMEOUT = Timeout(float(config.find_key("api_timeout")))


class StreamlitChatClient:
    """
    Client per interagire con l'API AI Assistant con supporto streaming.
    """

    def __init__(self, base_url: str, logger):
        """
        Inizializza il client.

        Args:
            base_url (str): L'URL base dell'API.
        """
        self.base_url = base_url
        self.logger = logger

    async def stream_chat(self, conv_id: str, user_request: str):
        """
        Esegue una richiesta di chat e gestisce lo streaming della risposta.

        Args:
            user_request (str): La richiesta testuale dell'utente.

        Yields:
            str: Parti della risposta ricevute in streaming.
        """

        async with AsyncClient(timeout=TIMEOUT) as client:
            url = f"{self.base_url}/streaming_chat"
            payload = {"conv_id": conv_id, "request_text": user_request}

            try:
                async with client.stream("POST", url, json=payload) as response:
                    if response.status_code != 200:
                        raise ValueError(
                            f"""Error in server response: {response.status_code} 
                                {await response.aread()}"""
                        )

                    # Legge il contenuto del flusso riga per riga
                    async for chunk in response.aiter_bytes():
                        yield chunk.decode("utf-8")
            except RequestError as exc:
                err_msg = f"Connection error: {exc}"
                self.logger.error(err_msg)
                st.error(err_msg)
            except Exception as e:
                err_msg = f"Unexpected error: {e}"
                self.logger.error(err_msg)
                st.error(err_msg)

    def delete_conversation(self, conv_id: str):
        """
        Deletes a conversation by ID from the server.

        Args:
            conv_id (str): The unique identifier of the conversation to delete.
            base_url (str): The base URL of the API.

        Returns:
            dict: The server's response as a dictionary.
        """
        url = f"{self.base_url}/conversation/{conv_id}"
        try:
            response = requests.delete(
                url, timeout=float(config.find_key("api_timeout"))
            )

            # Check the HTTP status code
            if response.status_code == 200:
                self.logger.info("Conversation deleted successfully!")
                return response.json()
            if response.status_code == 404:
                self.logger.info("Conversation not found.")
                return response.json()

            self.logger.info("Error: %s", response.status_code)
            return response.json()
        except requests.RequestException as e:
            self.logger.info("Request failed: %s", e)
            return {"error": str(e)}

    async def print_result(self, conv_id, user_request, output_placeholder):
        """
        Modificato per usare il markdown per una migliore visualizzazione.
        """
        response_text = ""
        async for response_part in self.stream_chat(conv_id, user_request):
            response_text += response_part
            # Aggiorna il contenuto formattandolo con markdown
            output_placeholder.markdown(response_text, unsafe_allow_html=True)
