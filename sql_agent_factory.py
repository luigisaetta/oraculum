"""
This modul contains the factory method to create the right SQL agent version, 
based on config
"""

from config_reader import ConfigReader
from sql_agent import SQLAgent
from select_ai_sql_agent import SelectAISQLAgent


def sql_agent_factory(_config: ConfigReader) -> SQLAgent:
    """
    get from config the sql_agent type
    """
    agent_type = _config.find_key("sql_agent_type")

    if agent_type == "select_ai":
        # implementation is with ADB Select AI
        return SelectAISQLAgent(_config)

    # if we arrive here: error
    raise ValueError(f"Unknown SQL agent type: {agent_type}")
