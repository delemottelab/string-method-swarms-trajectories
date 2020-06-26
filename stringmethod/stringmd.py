import os
from dataclasses import dataclass
from typing import Optional

import numpy as np

from stringmethod import logger, mdtools
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
        self.string = np.loadtxt(self._get_string_filepath())
        if len(self.string) - 2 != mpi.n_ranks:
            raise NotImplementedError("""Number of MPI ranks must be equal to the number of points on the string
             minus the fixed endpoints""")

    def _run_restrained(self):
        grompp_options = dict(
            mdp_file="{}/{}".format(self.config.mdp_dir, "restrained.mdp"),
            index_file="{}/{}".format(self.config.topology_dir, "index.ndx"),
            topology_file="{}/{}".format(self.config.topology_dir, "topol.top"),
            structure_file="{}/{}/{}/confout.gro".format(
                self.config.mdp_dir,
                self.iteration - 1,
                self._get_node_point(),
            ),
            tpr_file=self._get_tpr_file(self._get_node_point())
        )
        mdtools.grompp(grompp_options)
        mdrun_options = string_restraints = dict()  # TODO
        mdtools.mdrun(tpr_files=[self._get_tpr_file(p) for p in range(1, self.string.shape[0] - 1)],
                      mdp_properties=string_restraints)

    def _run_swarms(self):
        prep = mdtools.grompp()
        mdtools.mdrun(prep)
        raise NotImplementedError()

    def _compute_new_string(self) -> bool:
        raise NotImplementedError()

    def _setup_dirs(self) -> bool:
        logger.info("Starting string iteration %s ", self.iteration)
        os.makedirs("{}/{}".format(self.config.output_dir, self.config.string_dir))
        os.makedirs("{}/{}/{}".format(self.config.output_dir, self.config.md_dir, self.iteration))
        if not os.path.exists(self._get_string_filepath()):
            logger.error("File %s does not exist", self._get_string_filepath())
            return False
        return True

    def _get_string_filepath(self) -> str:
        return "{}/{}/string{}.txt".format(self.config.output_dir, self.config.string_dir, self.iteration)

    def _get_node_point(self) -> int:
        return mpi.rank

    def _get_tpr_file(self, point: int) -> str:
        "{}/{}/{}/{}/topol.tpr".format(
            self.config.output_dir,
            self.config.mdp_dir,
            self.iteration,
            point,
        ),
