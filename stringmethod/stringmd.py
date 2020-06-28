import os
import shutil
from dataclasses import dataclass
from os.path import abspath
from typing import Optional, Dict, Any

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
            os.makedirs(point_path + "restrained", exist_ok=True)
            for s in range(self.config.swarm_size):
                os.makedirs("{}s{}".format(point_path, s), exist_ok=True)
        return True

    def _run_restrained(self):
        grompp_tasks, mdrun_tasks = [], []
        if mpi.is_root():
            for point_idx, point in enumerate(self.string):
                if self.config.fixed_endpoints and point_idx in [0, self.string.shape[0] - 1]:
                    continue
                string_restraints = dict()
                for cv_idx, position in enumerate(point):
                    string_restraints['pull-coord{}-init'.format(cv_idx + 1)] = position
                mdp_file = self._create_restrained_mdp_file(point_idx, string_restraints)
                output_dir = abspath("{}/{}/{}/restrained/".format(
                    self.config.md_dir,
                    self.iteration,
                    point_idx
                ))
                tpr_file = abspath("{}/topol.tpr".format(output_dir))
                grompp_args = dict(
                    mdp_file=mdp_file,
                    index_file="{}/index.ndx".format(self.config.topology_dir),
                    topology_file="{}/topol.top".format(self.config.topology_dir),
                    structure_file=abspath("{}/{}/{}/restrained/confout.gro".format(
                        self.config.md_dir,
                        self.iteration - 1,
                        point_idx
                    )),
                    tpr_file=tpr_file,
                    mdp_output_file="{}/mdout.mdp".format(output_dir)
                )
                mdrun_args = dict(
                    output_dir=output_dir,
                    tpr_file=tpr_file,
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

    def _create_restrained_mdp_file(self, point_idx: int, string_restraints: Dict[str, Any]) -> str:
        # TODO use gmxapi#mdrun#override_input when it supports supports pull-coord1-init
        mdp_template_file = abspath("{}/{}".format(self.config.mdp_dir, "restrained.mdp"))
        mdp_file = abspath("{}/{}/{}/restrained/restrained.mdp".format(
            self.config.md_dir,
            self.iteration,
            point_idx,
        ))
        shutil.copy(mdp_template_file, mdp_file)
        with open(mdp_file, 'a') as f:
            f.write("\n\n;--------automatically injected properties from python below----\n\n")
            for k, v in string_restraints.items():
                f.write("{}={}\n".format(k, v))
        return mdp_file
