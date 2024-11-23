"""
General utils
"""

import logging
from decimal import Decimal
from sqlalchemy.inspection import inspect


def get_console_logger():
    """
    To get a logger to print on console
    """
    logger = logging.getLogger("ConsoleLogger")

    # to avoid duplication of logging
    if not logger.handlers:
        logger.setLevel(logging.INFO)

        handler = logging.StreamHandler()
        handler.setLevel(logging.INFO)

        formatter = logging.Formatter("%(asctime)s - %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    logger.propagate = False

    return logger


# these 2 functions are needed to serialize rows returnd from query in json
def decimal_to_float(value):
    """
    convert a Decimal to float
    """
    if isinstance(value, Decimal):
        return float(value)
    return value


def to_dict(obj):
    """
    convert a row to a dict
    """
    if hasattr(obj, "__dict__"):
        # this handles an ORM object
        return {
            c.key: decimal_to_float(getattr(obj, c.key))
            for c in inspect(obj).mapper.column_attrs
        }

    # Oggetto Row tramite .mappings() (query SQL), non serve usare dict() qui
    return {key: decimal_to_float(value) for key, value in obj.items()}


def create_banner(message, char="*", width=50):
    """
    Create a styled banner with the specified message.

    :param message: The message to display in the banner
    :param char: The character to use for the banner border
    :param width: The total width of the banner
    :return: None
    """
    logger = get_console_logger()

    message = message.upper()  # Convert message to uppercase
    border = char * width
    centered_message = f" {message} ".center(width, char)
    logger.info("")
    logger.info(border)
    logger.info(centered_message)
    logger.info(border)
    logger.info("")
