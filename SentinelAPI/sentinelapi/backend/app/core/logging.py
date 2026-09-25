from logging import getLogger, StreamHandler, Formatter, INFO, DEBUG, ERROR, FileHandler
import os

logger = getLogger("SentinelAPI")
logger.setLevel(DEBUG)

# Create console handler
console_handler = StreamHandler()
console_handler.setLevel(INFO)

# Create file handler
log_file = os.path.join(os.path.dirname(__file__), "sentinelapi.log")
file_handler = FileHandler(log_file)
file_handler.setLevel(DEBUG)

# Create formatter
formatter = Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# Add handlers to the logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)