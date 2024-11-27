# Oraculum
**Oraculum** is an open source project designed to create an AI assistant that connects to an **Oracle Database** and provides answers to questions about the data. The assistant is designed to evolve modularly, making data exploration intuitive, efficient, and scalable.

## Design Principles
* **REST API** built with FastAPI
* Asynchronous API with support for **streaming** responses

## Asynchronous and Streaming Capabilities
The original SQL agent project had a significant limitation: its REST API was synchronous. Because SQL generation can take several seconds, this approach resulted in long periods with no feedback sent to the user interface, leading to a poor user experience.

In **Oraculum**, the API has been re-engineered from the ground up to be **asynchronous**. This allows for real-time progress updates, significantly reducing perceived wait times and improving responsiveness.



