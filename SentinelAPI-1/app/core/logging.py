from __future__ import annotations

import logging
import sys

LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_LEVEL = logging.INFO

def setup_logging() -> None:
    logging.basicConfig(
        stream=sys.stdout,
        level=LOG_LEVEL,
        format=LOG_FORMAT,
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("uvicorn").setLevel(logging.WARNING)

setup_logging()