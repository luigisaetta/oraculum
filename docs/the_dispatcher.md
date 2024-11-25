## The Dispatcher

### Handlers
Handlers for the different classification outcomes must be defined in the **Dispatcher** class using the 
following template:

```
async def handle_generate_sql(self, user_request: str):
        """
        Handle SQL generation requests.

        Args:
            user_request (str): User's input request.

        Yields:
            str: Partial responses for streaming.
        """
        # simulate streaming response
        for i in range(5):  
            await asyncio.sleep(0.4)
            yield f"SQL Part {i + 1} for: {user_request}"
```