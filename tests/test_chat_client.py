import httpx
import asyncio
from config_reader import ConfigReader

config = ConfigReader("../config.toml")

class ChatClient:
    """
    Client per interagire con l'API AI Assistant con supporto streaming.
    """
    def __init__(self, base_url: str):
        """
        Inizializza il client.

        Args:
            base_url (str): L'URL base dell'API.
        """
        self.base_url = base_url

    async def stream_chat(self, user_request: str):
        """
        Esegue una richiesta di chat e gestisce lo streaming della risposta.

        Args:
            user_request (str): La richiesta testuale dell'utente.

        Yields:
            str: Parti della risposta ricevute in streaming.
        """
        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=30.0)) as client:
            url = f"{self.base_url}/streaming_chat"
            payload = {"request": user_request}

            try:
                async with client.stream("POST", url, json=payload) as response:
                    if response.status_code != 200:
                        raise ValueError(
                            f"Error in server response: {response.status_code} {await response.aread()}"
                        )

                    # Legge il contenuto del flusso riga per riga
                    async for chunk in response.aiter_bytes():
                        yield chunk.decode("utf-8")
            except httpx.RequestError as exc:
                print(f"Error in connection: {exc}")
            except Exception as e:
                print(f"Error during processing request: {e}")


# Funzione di esempio per utilizzare il client
async def main():
    """
    Funzione principale per testare il client.
    """
    # URL base dell'API
    port = int(config.find_key("port"))

    base_url = f"http://localhost:{port}"

    # Inizializza il client
    client = ChatClient(base_url)

    # Richiesta testuale
    user_request = "Delete all sales."

    async for response_part in client.stream_chat(user_request):
        print(f"{response_part}", end='', flush=True)

# Avvio del client
if __name__ == "__main__":
    asyncio.run(main())
