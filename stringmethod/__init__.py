import logging
import sys
from logging import Logger

logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="%(asctime)s %(name)s-%(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger: Logger = logging.getLogger("stringmethod")

VERSION = "1.0.0"

__all__ = [
    "config",
    "steeredmd",
    "stringmd",
    "utils",
    "logger",
    "VERSION",
    "postprocessing",
]
