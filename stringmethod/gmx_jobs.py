import time
from typing import List, Tuple

from mpi_master_slave import WorkQueue, Master, Slave
from stringmethod import mpi, mdtools, logger

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
        self.running = False

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
                    print('Master: slave finished is task and says "%s"' % message)

            time.sleep(0.03)


class GmxSlave(Slave):
    """
    A slave process extends Slave class, overrides the 'do_work' method
    and calls 'Slave.run'. The Master will do the rest
    """

    def __init__(self):
        super(GmxSlave, self).__init__()

    def do_work(self, data):
        try:
            operation, args = data
            if operation == 'grompp':
                mdtools.grompp(**args)
            elif operation == 'mdrun':
                mdtools.mdrun(**args)
            else:
                raise ValueError('Unknown task {}'.format(operation))
            return True, 'SUCCESS'
        except Exception as ex:
            logger.exception(ex)
            return False, str(ex)


def run(tasks: List[Tuple[str, dict]], step=None):
    global _instance
    if mpi.is_root():
        # TODO should start a slave on this rank as well to best utilize computational resources
        _instance = GmxMaster(slaves=range(1, mpi.n_ranks))
        _instance.run(tasks)
        _instance.terminate_slaves()
        logger.info("Stopping all workers for step %s", step)
    else:
        _instance = GmxSlave()
        _instance.run()
