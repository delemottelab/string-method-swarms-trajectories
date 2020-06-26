from typing import Callable

from mpi4py import MPI

from stringmethod import logger

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
n_ranks = comm.Get_size()


def is_root():
    return rank == 0


def run_on_root_then_broadcast(func: Callable, step: str):
    if is_root():
        data = dict(message=None)
        try:
            success = func()
        except Exception as ex:
            logger.exception(ex)
            success = False
            data['message'] = str(ex)
        data[step] = success
    else:
        # Wait for root to do postprocessing
        data = None
    data = comm.bcast(data, root=0)
    if not data.get(step, False):
        logger.error("Root failed for step %s", step)


def init():
    if is_root():
        logger.info("Using %s MPI ranks ", n_ranks)


init()
