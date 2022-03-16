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

VERSION = "2.0.1"

__all__ = [
    "config",
    "simulations",
    "utils",
    "logger",
    "VERSION",
    "postprocessing",
]
