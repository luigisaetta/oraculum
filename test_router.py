"""
Test the router
"""

from config_reader import ConfigReader
from router import Router
from llm_manager import LLMManager
from utils import get_console_logger, create_banner

from config_private import COMPARTMENT_OCID

#
# Main
#
logger = get_console_logger()

# read the configuration
config = ConfigReader("config.toml")
models_list = config.find_key("models_list")
models_endpoints = config.find_key("models_endpoints")

llm_manager = LLMManager(
    model_list=models_list,
    model_endpoints=models_endpoints,
    compartment_id=COMPARTMENT_OCID,
    temperature=0,
    logger=logger,
)

router = Router(llm_manager)

#
# here we do all the tests
#
LIST_QUERIES = [
    "Show me the list of all sales",
    "Create a report based on the provided data",
    "Create a calendar",
    "I don't know what to ask for",
    "I need a list with all the sales, with product, customer and total amount",
    "drop table EMP",
    "Delete all the sales",
    "Read the data and tell me what is the country with highest sales?",
]

create_banner("Test routing")

for QUERY in LIST_QUERIES:
    logger.info("Query:         %s", QUERY)

    classification = router.classify(QUERY)

    logger.info("Classified as: %s", classification)
    logger.info("")
