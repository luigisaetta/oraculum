"""
Test the router
"""
import json
from config_reader import ConfigReader
from router_with_dispatcher import RouterWithDispatcher
from dispatcher import Dispatcher
from llm_manager import LLMManager
from utils import get_console_logger, create_banner

from config_private import COMPARTMENT_OCID

def read_json(file_path):
    try:
        with open(file_path, "r") as file:
            data = json.load(file)  # Load JSON data into a Python object
            return data
    except FileNotFoundError:
        print(f"Error: The file {file_path} does not exist.")
    except json.JSONDecodeError:
        print(f"Error: The file {file_path} is not a valid JSON.")
    return None
#
# Main
#
logger = get_console_logger()

# read the configuration
config = ConfigReader("../config.toml")

create_banner("Test routing")

llm_manager = LLMManager(
    config,
    compartment_id=COMPARTMENT_OCID,
    logger=logger,
)

dispatcher = Dispatcher()
router = RouterWithDispatcher(config, llm_manager, dispatcher)

#
# here we do all the tests
#
queries_and_classifications = read_json("./test_router.json")

n_ok = 0
KEEP = 2

for i, item in enumerate(queries_and_classifications):
    query = item["query"]
    expected = item["expected"]

    logger.info("Query:         %s", query)

    classification = router.classify(query)

    logger.info("Classified as: %s", classification)
    logger.info("")

    if expected == classification:
        n_ok += 1
    else:
        logger.info("Expected: %s", expected)

    # test dispatching
    
    if (i+1) > KEEP:
        break

logger.info("")
logger.info("Results:")
logger.info("   N. test: %d", len(queries_and_classifications))
logger.info("   N. OK: %d", n_ok)
logger.info("")
