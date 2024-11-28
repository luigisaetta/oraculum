"""
SQL agent based on Select AI
"""

import oracledb
from sql_agent import SQLAgent
from config_private import DB_USER, DB_PWD, DSN, WALLET_DIR, WALLET_PWD

CONNECT_ARGS = {
    "user": DB_USER,
    "password": DB_PWD,
    "dsn": DSN,
    "config_dir": WALLET_DIR,
    "wallet_location": WALLET_DIR,
    "wallet_password": WALLET_PWD,
}


class SelectAISQLAgent(SQLAgent):
    """
    Implementation of the SQL Agent based on Select AI
    """

    def get_db_connection(self):
        """
        get a connection to data DB
        """
        return oracledb.connect(**CONNECT_ARGS)

    def generate_sql(self, nl_request: str) -> str:
        # Simula un modello AI che genera SQL
        return f"SELECT * FROM data WHERE description LIKE '%{nl_request}%'"

    def execute_sql(self, sql: str) -> list[dict]:
        # Simula l'esecuzione SQL e il ritorno dei risultati
        return [
            {"name": "Alice", "age": 25, "city": "New York"},
            {"name": "Bob", "age": 30, "city": "San Francisco"},
            {"name": "Charlie", "age": 35, "city": "Chicago"},
        ]
