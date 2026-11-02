"""Application logging configuration."""

import logging


def get_logger(name="weatherlab"):
    """Return a named logger with a basic console handler if needed."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logging.basicConfig(level=logging.INFO)
    return logger
