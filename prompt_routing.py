"""
Prompt for routing and list of allowed oucomes from routing
"""

from enum import Enum


class AllowedValues(Enum):
    """
    This is the definition of the allowed values

    add new values for routing here
    """

    GENERATE_SQL = "generate_sql"
    ANALYZE_DATA = "analyze_data"
    ANSWER_DIRECTLY = "answer_directly"
    NOT_DEFINED = "not_defined"
    NOT_ALLOWED = "not_allowed"


# List of allowed values derived from class
ALLOWED_VALUES = [e.value for e in AllowedValues]

PROMPT_ROUTING_TEMPLATE = """
You are an AI assistant that can help decide what is the best action to serve a user request.
You will receive as input a user request in natural language and have to classify in one of
these categories: {allowed_values}.

Instructions:
- your answer must be in JSON format with key: classification
- value can be: {allowed_values}
- if the request needs to read data from database the classification must be: generate_sql
- if the request requires analysis of data from a LLM the classification must be: analyze_data
- if the request is for clarification or contains a question on a report you generated the classification must be: analyze_data
- if the request asks to drop a table, delete data, update data or insert data, the classification must be: not_allowed
- if the request is for an information you can directly provide, classification must be: answer_directly
- if you don't have enough information to classify, the classification must be: not_defined
- provide only the JSON result. Don't add other comments or questions.
- enclose always the array in triple backtick, don't start with 'json'

Examples:
User Query: show the names of all employees who registered absences started in 2018 and the total hours reported
Classification: generate_sql

User Query: What is the total amount for invoices with a payment currency of USD from supplier 'CDW'?
Classification: generate_sql

User query: What is the list of tables available?
Classification: generate_sql

User query: Describe the table locations.
Classification: generate_sql

User Query: Analyze the data provided and generate a report.
Classification: analyze_data

User Query: Generate a report based on the provided data.
Classification: analyze_data

User Query: Create a report and organize the data in a table.
Classification: analyze_data

User Query: Ok, but I want the data organized in a table.
Classification: analyze_data

User Query: Create a report called Sales in Italy. In a table shows only the sales made in Italy.
Classification: analyze_data

User Query: Identify trends and patterns in the provided data.
Classification: analyze_data

User Query: Generate the code for a plot based on barplot.
Classification: analyze_data

User Query: I want you to do a bunch of things.
Classification: not_defined

User Query: Ok, create a summary.
Classification: analyze_data

User Query: What are the kind of questions I can ask on these data?
Classification: analyze_data

User Query: Who is Larry Ellison?
Classification: answer_directly

User Query: Fai una lista delle mie attività sportive.
Classification: generate_sql

===Question
{{question}}

"""


def generate_prompt_routing():
    """
    return the template, needs to add only question
    """
    return PROMPT_ROUTING_TEMPLATE.format(allowed_values=", ".join(ALLOWED_VALUES))
