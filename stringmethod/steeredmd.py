import os
import shutil
from dataclasses import dataclass
from os.path import abspath
from typing import Optional

import numpy as np

from gmx_jobs import gmx_jobs
from stringmethod import utils, logger
from stringmethod.config import Config


@dataclass
class SteeredRunner(object):
    path: np.array = None
    mdp_file: Optional[str] = "steered.mdp"
    start_coordinates: Optional[str] = "topology/start.gro"
    md_dir: Optional[str] = "md"
    topology_dir: Optional[str] = "topology"
    steered_simulation_length_ps: Optional[float] = None
    mdrun_options_steered: Optional[tuple] = None

    def __post_init__(self):
        if self.steered_simulation_length_ps is None:
            mdp_options = utils.parse_mdp(self.mdp_file)
            self.steered_simulation_length_ps = mdp_options.get(
                "dt", 0.001
            ) * mdp_options.get("nsteps", 0)
        if self.steered_simulation_length_ps <= 0:
            raise ValueError(
                "Simulation length for steered MD was set to {} picoseconds. Did you set 'nsteps' to a reasonable value?".format(
                    self.steered_simulation_length_ps
                )
            )

    def run(self):
        """
        Run piecewise steered MD simulations between adjacent points on the path
        :return:
        """
        self._create_dir(0)
        shutil.copy(
            self.start_coordinates, self._get_md_dir(0) + "/confout.gro"
        )
        for i in range(len(self.path) - 1):
            self._steer_between_points(i, i + 1)

    def _steer_between_points(self, start_point_idx, end_point_idx):
        """
        :param point0:
        :param point1:
        :return:
        """
        # Prepare files
        output_dir = self._get_md_dir(end_point_idx)
        self._create_dir(end_point_idx)
        start_point, end_point = (
            self.path[start_point_idx],
            self.path[end_point_idx],
        )
        pull_rates = (
            end_point - start_point
        ) / self.steered_simulation_length_ps
        modified_mdp_file = output_dir + "/grompp.mdp"
        shutil.copy(self.mdp_file, modified_mdp_file)
        with open(modified_mdp_file, "a") as f:
            f.write(
                "\n\n;--------automatically injected properties from python below----\n\n"
            )
            for cv_idx, rate in enumerate(pull_rates):
                f.write(
                    "pull-coord{}-init={}\n".format(
                        cv_idx + 1, start_point[cv_idx]
                    )
                )
                f.write("pull-coord{}-rate={}\n".format(cv_idx + 1, rate))

        # Submit jobs
        # TODO: code duplication from stringmethod.md below. Refactor into common functionality
        tpr_file = "{}/topol.tpr".format(output_dir)
        if os.path.isfile(tpr_file):
            logger.debug(
                "File %s already exists. Not running grompp again", tpr_file
            )
        else:
            in_file = self._get_md_dir(start_point_idx) + "/confout.gro"
            if not os.path.exists(in_file):
                raise IOError(
                    "File {} does not exist. Cannot continue steered MD. Check the logs for errors".format(
                        in_file
                    )
                )
            grompp_args = dict(
                mdp_file=modified_mdp_file,
                index_file="{}/index.ndx".format(self.topology_dir),
                topology_file="{}/topol.top".format(self.topology_dir),
                structure_file=in_file,
                tpr_file=tpr_file,
                mdp_output_file="{}/mdout.mdp".format(output_dir),
            )
            gmx_jobs.submit(
                tasks=[("grompp", grompp_args)],
                step="steered_grompp_point{}".format(end_point_idx),
            )

        # Pick up checkpoint files if available
        check_point_file = abspath("{}/state.cpt".format(output_dir))
        if not os.path.isfile(check_point_file):
            check_point_file = None
        mdrun_confout = "{}/confout.gro".format(output_dir)
        if os.path.isfile(mdrun_confout):
            logger.debug(
                "File %s already exists. Not running mdrun again",
                mdrun_confout,
            )
        else:
            # Pick up checkpoint files if available
            mdrun_args = dict(
                output_dir=output_dir,
                tpr_file=tpr_file,
                check_point_file=check_point_file,
                mdrun_options=self.mdrun_options_steered,
            )
            gmx_jobs.submit(
                tasks=[("mdrun", mdrun_args)],
                step="steered_mdrun_point{}".format(end_point_idx),
            )

    def _create_dir(self, point_idx):
        sdir = self._get_md_dir(point_idx)
        if not os.path.exists(sdir):
            os.makedirs(sdir)

    def _get_md_dir(self, point_idx):
        return abspath(self.md_dir) + "/0/" + str(point_idx) + "/restrained/"

    @classmethod
    def from_config(clazz, config: Config, **kwargs):
        return clazz(
            path=np.loadtxt(config.steered_md_target_path),
            mdp_file=config.mdp_dir + "/steered.mdp",
            md_dir=config.md_dir,
            topology_dir=config.topology_dir,
            mdrun_options_steered=config.mdrun_options_steered,
            **kwargs
        )
