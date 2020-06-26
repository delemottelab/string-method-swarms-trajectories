"""
String method in python using gmxapi

See https://github.com/delemottelab/string-method-gmxapi for more info.

"""
import logging
from logging import Logger

from . import mpi

logger: Logger = logging.getLogger("stringmethod-{}".format(mpi.rank))
VERSION = "1.0.0"

__all__ = ['config', 'steeredmd', 'stringmd', 'mdtools', 'logger']
