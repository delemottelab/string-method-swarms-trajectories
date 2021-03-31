import time
from typing import List, Tuple

import mdtools
from gmx_jobs.mpi_master_slave import Master, Slave, WorkQueue
from gmx_jobs.mpi_master_slave.exceptions import JobFailedException
from stringmethod import logger, mpi

_instance = None


class GmxMaster(object):
    """
    This is my application that has a lot of work to do so it gives work to do
    to its slaves until all the work is done

    see https://github.com/luca-s/mpi-master-slave
    """

    def __init__(self, slaves):
        # when creating the Master we tell it what slaves it can handle
        self.master = Master(slaves)
        # WorkQueue is a convenient class that run slaves on a tasks queue
        self.work_queue = WorkQueue(self.master)

    def terminate_slaves(self):
        """
        Call this to make all slaves exit their run loop
        """
        self.master.terminate_slaves()

    def run(self, tasks: List[Tuple[str, dict]]):
        """
        This is the core of my application, keep starting slaves
        as long as there is work to do
        """
        #
        # let's prepare our work queue. This can be built at initialization time
        # but it can also be added later as more work become available
        #
        for t in tasks:
            # 'data' will be passed to the slave and can be anything
            self.work_queue.add_work(t)

        #
        # Keeep starting slaves as long as there is work to do
        #
        while not self.work_queue.done():

            #
            # give more work to do to each idle slave (if any)
            #
            self.work_queue.do_work()

            #
            # reclaim returned data from completed slaves
            #
            for slave_return_data in self.work_queue.get_completed_work():
                done, message = slave_return_data
                if done:
                    logger.debug(
                        'Master: slave finished its task with message "%s"',
                        message,
                    )
                else:
                    raise JobFailedException(
                        "Slave failed job with message '%s'." % message
                    )
            time.sleep(0.03)


class GmxSlave(Slave):
    """
    A slave process extends Slave class, overrides the 'do_work' method
    and calls 'Slave.run'. The Master will do the rest
    """

    def __init__(self):
        super(GmxSlave, self).__init__()

    def run_all(self, tasks: List[Tuple[str, dict]]):
        for t in tasks:
            done, message = self.do_work(t)
            if done:
                logger.debug('Finished task with message "%s"', message)
            else:
                raise JobFailedException(
                    "Slave failed job with message '%s'." % message
                )

    def do_work(self, task: Tuple[str, dict]):
        try:
            operation, args = task
            logger.debug(
                "slave performing operation %s with args %s",
                operation,
                args,
            )
            if operation == "grompp":
                mdtools.grompp(**args)
            elif operation == "mdrun":
                mdtools.mdrun(mpi.rank, **args)
            else:
                raise ValueError("Unknown task operation {}".format(operation))
            return True, "SUCCESS"
        except Exception as ex:
            logger.exception(ex)
            return False, str(ex)


def submit(tasks: List[Tuple[str, dict]], step=None):
    global _instance
    if mpi.n_ranks == 1:
        # We're running this on a single MPI rank. No need for a master-slave setup
        logger.info("Running all jobs on a single rank")
        _instance = GmxSlave()
        _instance.run_all(tasks)
        logger.info("Finished with step %s on a single MPI rank", step)
    elif mpi.is_master():
        logger.info("Distributing all jobs to %s ranks", mpi.n_ranks - 1)
        # TODO should start a slave on this rank as well to best utilize computational resources
        _instance = GmxMaster(slaves=range(1, mpi.n_ranks))
        try:
            _instance.run(tasks)
        finally:
            logger.info("Stopping all workers for step %s", step)
            _instance.terminate_slaves()
    else:
        _instance = GmxSlave()
        _instance.run()
