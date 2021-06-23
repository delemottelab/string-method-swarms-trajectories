"""
String method in python using gmxapi

See https://github.com/delemottelab/string-method-gmxapi for more info.

"""
import logging
import sys
from logging import Logger

logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="%(asctime)s %(name)s-%(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
from mpi4py import MPI

logger: Logger = logging.getLogger(
    "stringmethod-{}".format(MPI.COMM_WORLD.Get_rank())
)
try:
    import gmxapi

    gmxapi.logger.setLevel(logging.WARNING)
except:
    pass
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
