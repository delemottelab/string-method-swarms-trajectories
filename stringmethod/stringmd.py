import os
from dataclasses import dataclass
from typing import Optional

import numpy as np

from stringmethod import logger, mdtools, gmx_jobs
from stringmethod.config import Config
from . import mpi


@dataclass
class StringIterationRunner(object):
    config: Config
    append: bool
    iteration: int
    """Coordinates of the current numpy array"""
    string: Optional[np.array] = None

    def run(self):

        while self.iteration <= self.config.max_iterations:
            self._init()
            self._run_restrained()
            self._run_swarms()
            mpi.run_on_root_then_broadcast(lambda: self._compute_new_string()(), 'postprocessing')

    def _init(self):
        mpi.run_on_root_then_broadcast(lambda: self._setup_dirs(), 'iteration_init')
        self.string = np.loadtxt(self._get_string_filepath(self.iteration - 1))
        # if len(self.string) - 2 != mpi.n_ranks:
        #     raise NotImplementedError("""Number of MPI ranks must be equal to the number of points on the string
        #      minus the fixed endpoints""")

    def _setup_dirs(self) -> bool:
        logger.info("Starting string iteration %s ", self.iteration)
        os.makedirs("{}".format(self.config.string_dir))
        os.makedirs("{}/{}".format(self.config.md_dir, self.iteration))
        if not os.path.exists(self._get_string_filepath()):
            logger.error("File %s does not exist", self._get_string_filepath())
            return False
        return True

    def _run_restrained(self):
        grompp_tasks, mdrun_tasks = [], []
        if mpi.is_root():
            for idx, point in enumerate(self.string):
                tpr_file = self._get_tpr_file(point)
                grompp_args = dict(
                    mdp_file="{}/{}".format(self.config.mdp_dir, "restrained.mdp"),
                    index_file="{}/{}".format(self.config.topology_dir, "index.ndx"),
                    topology_file="{}/{}".format(self.config.topology_dir, "topol.top"),
                    structure_file="{}/{}/{}/confout.gro".format(
                        self.config.mdp_dir,
                        self.iteration - 1,
                        idx
                    ),
                    tpr_file=tpr_file,
                )
                string_restraints = dict()
                for cv_idx, position in enumerate(point):
                    string_restraints['pull-coord{}-init'.format(cv_idx)] = position
                mdrun_args = dict(
                    tpr_file=tpr_file,
                    mdp_properties=string_restraints
                )
                grompp_tasks.append(('grompp', grompp_args))
                mdrun_tasks.append(('mdrun', mdrun_args))
        gmx_jobs.run(tasks=grompp_tasks, step="restrained_grompp")
        gmx_jobs.run(tasks=mdrun_tasks, step="restrained_mdrun")

    def _run_swarms(self):
        prep = mdtools.grompp()
        mdtools.mdrun(prep)
        raise NotImplementedError("TODO similar logic as run_restrained. Remove any restraints")

    def _compute_new_string(self) -> bool:
        raise NotImplementedError()

    def _get_string_filepath(self, iteration: int) -> str:
        return "{}/string{}.txt".format(self.config.string_dir, iteration)

    def _get_tpr_file(self, point: int) -> str:
        "{}/{}/{}/topol.tpr".format(
            self.config.mdp_dir,
            self.iteration,
            point,
        ),
