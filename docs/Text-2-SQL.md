## Text-2-SQL

### Pluggable modules
The idea is that the API can plug-in different modules to generate SQL.
The base structure is defined in `sql_agent.py` and we have a first implementation 
based on ADB Select AI `select_ai_sql_agent.py`