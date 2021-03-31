from typing import Callable

from mpi4py import MPI

from stringmethod import logger

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
n_ranks = comm.Get_size()
_master_rank = 0


def is_master():
    return rank == _master_rank


def run_on_root_then_broadcast(func: Callable, step: str):
    if is_master():
        data = dict(message=None)
        try:
            success = func()
        except Exception as ex:
            logger.exception(ex)
            success = False
            data["message"] = str(ex)
        data[step] = success
    else:
        # Wait for root to do work
        data = None
    data = comm.bcast(data, root=_master_rank)
    if not data.get(step, False):
        raise Exception("Master failed for step %s" % step)


def init():
    if is_master():
        logger.info("Using %s MPI ranks ", n_ranks)


init()
