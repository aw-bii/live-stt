import sys
from pathlib import Path
from loguru import logger

LOG_PATH = Path.home() / ".livesttt" / "logs"
LOG_FILE = "livesttt.log"

logger.remove()

logger.add(
    sys.stderr,
    format="<level>{level}</level> <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO",
)

LOG_PATH.mkdir(parents=True, exist_ok=True)
logger.add(
    LOG_PATH / LOG_FILE,
    rotation="10 MB",
    retention="7 days",
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}",
)