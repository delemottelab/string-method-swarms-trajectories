import os
import shutil
from dataclasses import dataclass
from os.path import abspath
from typing import Optional, Dict, Any

import numpy as np

import mdtools
from gmx_jobs import *
from stringmethod import utils
from stringmethod.config import Config
from stringmethod.utils.scaling import MinMaxScaler
from . import mpi


@dataclass
class StringIterationRunner(object):
    config: Config
    append: bool
    iteration: int
    """Coordinates of the current numpy array"""
    string: Optional[np.array] = None
    max_iterations: Optional[int] = 100
    swarm_size: Optional[int] = 32
    fixed_endpoints: Optional[bool] = True
    string_dir: Optional[str] = "strings"
    md_dir: Optional[str] = "md"
    topology_dir: Optional[str] = "topology"
    mdp_dir: Optional[str] = "mdp"

    def run(self):

        while self.iteration <= self.max_iterations:
            self._init()
            self._run_restrained()
            self._run_swarms()
            mpi.run_on_root_then_broadcast(lambda: self._compute_new_string(), 'postprocessing')
            self.iteration += 1

    def _init(self):
        input_string_path = self._get_string_filepath(self.iteration - 1)
        if not os.path.exists(input_string_path):
            raise IOError("File %s does not exist" % input_string_path)
        self.string = np.loadtxt(input_string_path)
        mpi.run_on_root_then_broadcast(lambda: self._setup_dirs(), 'iteration_init')

    def _setup_dirs(self) -> bool:
        logger.info("creating directories for string iteration %s ", self.iteration)
        os.makedirs("{}".format(self.string_dir), exist_ok=True)
        for point_idx in range(self.string.shape[0]):
            if self.fixed_endpoints and point_idx in [0, self.string.shape[0] - 1]:
                continue
            point_path = "{}/{}/{}/".format(self.md_dir, self.iteration, point_idx)
            os.makedirs(point_path + "restrained", exist_ok=True)
            for s in range(self.swarm_size):
                os.makedirs("{}s{}".format(point_path, s), exist_ok=True)
        return True

    def _run_restrained(self):
        grompp_tasks, mdrun_tasks = [], []
        if mpi.is_master():
            for point_idx, point in enumerate(self.string):
                if self.fixed_endpoints and point_idx in [0, self.string.shape[0] - 1]:
                    continue
                string_restraints = dict()
                for cv_idx, position in enumerate(point):
                    string_restraints['pull-coord{}-init'.format(cv_idx + 1)] = position
                mdp_file = self._create_restrained_mdp_file(point_idx, string_restraints)
                output_dir = abspath("{}/{}/{}/restrained/".format(
                    self.md_dir,
                    self.iteration,
                    point_idx
                ))
                tpr_file = abspath("{}/topol.tpr".format(output_dir))
                if os.path.isfile(tpr_file):
                    logger.debug("File %s already exists. Not running grompp again", tpr_file)
                else:
                    grompp_args = dict(
                        mdp_file=mdp_file,
                        index_file="{}/index.ndx".format(self.topology_dir),
                        topology_file="{}/topol.top".format(self.topology_dir),
                        structure_file=abspath("{}/{}/{}/restrained/confout.gro".format(
                            self.md_dir,
                            self.iteration - 1,
                            point_idx
                        )),
                        tpr_file=tpr_file,
                        mdp_output_file="{}/mdout.mdp".format(output_dir)
                    )
                    grompp_tasks.append(('grompp', grompp_args))
                # SPC Pick up checkpoint files if available
                check_point_file = abspath("{}/state.cpt".format(output_dir))
                if not os.path.isfile(check_point_file):
                    check_point_file = None
                mdrun_confout = "{}/confout.gro".format(output_dir)
                if os.path.isfile(mdrun_confout):
                    logger.debug("File %s already exists. Not running mdrun again", mdrun_confout)
                else:
                    # Pick up checkpoint files if available
                    mdrun_args = dict(
                        output_dir=output_dir,
                        tpr_file=tpr_file,
                        check_point_file=check_point_file,
                    )
                    mdrun_tasks.append(('mdrun', mdrun_args))
        gmx_jobs.submit(tasks=grompp_tasks, step="restrained_grompp")
        gmx_jobs.submit(tasks=mdrun_tasks, step="restrained_mdrun")

    def _run_swarms(self):
        grompp_tasks, mdrun_tasks = [], []
        if mpi.is_master():
            for point_idx, point in enumerate(self.string):
                if self.fixed_endpoints and point_idx in [0, self.string.shape[0] - 1]:
                    continue
                for swarm_idx in range(self.swarm_size):
                    mdp_file = abspath("{}/swarms.mdp".format(self.mdp_dir))
                    output_dir = abspath("{}/{}/{}/s{}/".format(
                        self.md_dir,
                        self.iteration,
                        point_idx,
                        swarm_idx
                    ))
                    tpr_file = abspath("{}/topol.tpr".format(output_dir))
                    if os.path.isfile(tpr_file):
                        logger.debug("File %s already exists. Not running grompp again", tpr_file)
                    else:
                        grompp_args = dict(
                            mdp_file=mdp_file,
                            index_file="{}/index.ndx".format(self.topology_dir),
                            topology_file="{}/topol.top".format(self.topology_dir),
                            structure_file=abspath("{}/{}/{}/restrained/confout.gro".format(
                                self.md_dir,
                                self.iteration,
                                point_idx
                            )),
                            tpr_file=tpr_file,
                            mdp_output_file="{}/mdout.mdp".format(output_dir)
                        )
                        grompp_tasks.append(('grompp', grompp_args))
                    # Pick up checkpoint files if available
                    check_point_file = abspath("{}/state.cpt".format(output_dir))
                    if not os.path.isfile(check_point_file):
                        check_point_file = None
                    mdrun_confout = "{}/confout.gro".format(output_dir)
                    if os.path.isfile(mdrun_confout):
                        logger.debug("File %s already exists. Not running mdrun again", mdrun_confout)
                    else:
                        # SPC Pick up checkpoint files if available
                        mdrun_args = dict(
                            output_dir=output_dir,
                            tpr_file=tpr_file,
                            check_point_file=check_point_file,
                        )
                        mdrun_tasks.append(('mdrun', mdrun_args))
        gmx_jobs.submit(tasks=grompp_tasks, step="swarms_grompp")
        gmx_jobs.submit(tasks=mdrun_tasks, step="swarms_mdrun")

    def _compute_new_string(self) -> bool:
        drifted_string = self.string.copy()
        n_cvs = self.string.shape[1]
        if self.swarm_size > 0:
            for point_idx, point in enumerate(self.string):
                if self.fixed_endpoints and point_idx in [0, self.string.shape[0] - 1]:
                    continue
                swarm_drift = np.empty((self.swarm_size, n_cvs))
                for swarm_idx in range(self.swarm_size):
                    output_dir = abspath("{}/{}/{}/s{}/".format(
                        self.md_dir,
                        self.iteration,
                        point_idx,
                        swarm_idx
                    ))
                    pull_xvg_out = "{}/pullx.xvg".format(output_dir)
                    data = mdtools.load_xvg(file_name=pull_xvg_out)
                    # Skip first column which contains the time and exclude any columns which come after the CVs
                    # This could be e.g. other restraints not part of the CV set
                    data = data[:, 1:(n_cvs + 1)]
                    if swarm_idx == 0:
                        # Set the actual start coordinates here, in case they differ from the reference values
                        # Can happen due to e.g. a too weak potential
                        drifted_string[point_idx] = data[0]
                    swarm_drift[swarm_idx] = data[-1] - drifted_string[point_idx]
                drift = swarm_drift.mean(axis=0)
                drifted_string[point_idx] += drift
        # scale CVs
        # This is required to emphasize both small scale and large scale displacements
        scaler = MinMaxScaler()
        scaled_string = scaler.fit_transform(drifted_string)
        # TODO better scaling, let user control it via config
        new_scaled_string = utils.reparametrize_path_iter(scaled_string,
                                                          # TODO compute arc weights based on transition between points
                                                          arclength_weight=None)
        new_string = scaler.inverse_transform(new_scaled_string)
        np.savetxt(self._get_string_filepath(self.iteration), new_string)

        # Compute convergence
        # Note that this convergence does not take periodic boundary conditions into account.
        # To handle that you need to compute your own metric. See the alanine dipeptide example
        scaled_current_string = scaler.transform(self.string)
        mean_norm = (np.linalg.norm(new_scaled_string) + np.linalg.norm(scaled_current_string)) / 2
        convergence = np.linalg.norm(new_scaled_string - scaled_current_string) / mean_norm
        logger.info("Convergence between iteration %s and %s: %s", self.iteration - 1, self.iteration, convergence)
        return True

    def _get_string_filepath(self, iteration: int) -> str:
        return "{}/string{}.txt".format(self.string_dir, iteration)

    def _create_restrained_mdp_file(self, point_idx: int, string_restraints: Dict[str, Any]) -> str:
        # TODO use gmxapi#mdrun#override_input when it supports supports pull-coord1-init
        mdp_template_file = abspath("{}/{}".format(self.mdp_dir, "restrained.mdp"))
        mdp_file = abspath("{}/{}/{}/restrained/restrained.mdp".format(
            self.md_dir,
            self.iteration,
            point_idx,
        ))
        shutil.copy(mdp_template_file, mdp_file)
        with open(mdp_file, 'a') as f:
            f.write("\n\n;--------automatically injected properties from python below----\n\n")
            for k, v in string_restraints.items():
                f.write("{}={}\n".format(k, v))
        return mdp_file

    @classmethod
    def from_config(clazz, config: Config, **kwargs):
        return clazz(
            path=np.loadtxt(config.steered_md_target_path),
            mdp_file=config.mdp_dir + "/steered.mdp",
            md_dir=config.md_dir,
            **kwargs
        )
