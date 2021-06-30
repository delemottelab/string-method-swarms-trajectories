from typing import List, Tuple

import mdtools
from stringmethod import logger

_instance = None


class SimulationJob:
    def run_all(self, tasks: List[Tuple[str, dict]]):
        if not tasks:
            return
        elif tasks[0][0] == "grompp":
            mdtools.grompp_all([t[1] for t in tasks])
        elif tasks[0][0] == "mdrun":
            if len(tasks) > 1:
                mdtools.mdrun_all([t[1] for t in tasks])
            else:
                mdtools.mdrun_one(tasks[0][1])
        else:
            raise ValueError("Unknown task operation {}".format(tasks[0][0]))


def submit(tasks: List[Tuple[str, dict]], step=None):
    global _instance
    _instance = SimulationJob()
    _instance.run_all(tasks)
    logger.info("Finished with step %s.", step)
