import logging
import os
from pythonjsonlogger import jsonlogger

# Create a logger
logger = logging.getLogger("job_state_manager")
log_level = os.getenv("LOG_LEVEL", "INFO").upper()  # Default to INFO if LOG_LEVEL is not set
logger.setLevel(getattr(logging, log_level, logging.INFO))

# Create a log handler
handler = logging.StreamHandler()

# Use JSON formatter for structured logs
formatter = jsonlogger.JsonFormatter(
    "%(asctime)s %(levelname)s %(name)s %(message)s"
)
handler.setFormatter(formatter)

# Add handler to logger
logger.addHandler(handler)
