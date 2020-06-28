import os
from dataclasses import dataclass
from os.path import abspath
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
        input_string_path = self._get_string_filepath(self.iteration - 1)
        if not os.path.exists(input_string_path):
            logger.error(input_string_path)
            return False
        self.string = np.loadtxt(input_string_path)
        mpi.run_on_root_then_broadcast(lambda: self._setup_dirs(), 'iteration_init')

    def _setup_dirs(self) -> bool:
        logger.info("creating directories for string iteration %s ", self.iteration)
        os.makedirs("{}".format(self.config.string_dir), exist_ok=True)
        for point_idx in range(self.string.shape[0]):
            if self.config.fixed_endpoints and point_idx in [0, self.string.shape[0] - 1]:
                continue
            point_path = "{}/{}/{}/".format(self.config.md_dir, self.iteration, point_idx)
            os.makedirs(point_path, exist_ok=True)
            for s in range(self.config.swarm_size):
                os.makedirs("{}/s{}".format(point_path, s), exist_ok=True)
        return True

    def _run_restrained(self):
        grompp_tasks, mdrun_tasks = [], []
        if mpi.is_root():
            for point_idx, point in enumerate(self.string):
                if self.config.fixed_endpoints and point_idx in [0, self.string.shape[0] - 1]:
                    continue
                tpr_file = abspath("{}/{}/{}/topol.tpr".format(
                    self.config.md_dir,
                    self.iteration,
                    point_idx,
                ))
                grompp_args = dict(
                    mdp_file=abspath("{}/{}".format(self.config.mdp_dir, "restrained.mdp")),
                    index_file=abspath("{}/{}".format(self.config.topology_dir, "index.ndx")),
                    topology_file=abspath("{}/{}".format(self.config.topology_dir, "topol.top")),
                    structure_file=abspath("{}/{}/{}/confout.gro".format(
                        self.config.md_dir,
                        self.iteration - 1,
                        point_idx
                    )),
                    tpr_file=tpr_file,
                    mdp_output_file=abspath("{}/{}/{}/mdout.mdp".format(
                        self.config.md_dir,
                        self.iteration,
                        point_idx,
                    )),
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
