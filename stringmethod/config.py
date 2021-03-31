import json
from dataclasses import dataclass
from typing import Optional

from stringmethod import VERSION


class ConfigError(Exception):
    pass


@dataclass
class Config(object):
    """Label for your simulation"""

    simu_id: Optional[str] = "string_simulation"
    """Input/output location for strings"""
    string_dir: Optional[str] = "strings"
    """Input/output location for files generated during simulations"""
    md_dir: Optional[str] = "md"
    """Input/output location for strings. Should contain restrained.mdp and swarms.mdp"""
    mdp_dir: Optional[str] = "mdp"
    """Input location for the topology. Should contain index.ndx and topol.top"""
    topology_dir: Optional[str] = "topology"
    """Directory to save swarm transitions"""
    postprocessing_dir: Optional[str] = "postprocessing"
    """Number of trajectories in a swarm."""
    swarm_size: Optional[int] = 32
    """Maximum number of string iterations"""
    max_iterations: Optional[int] = 100
    """Keeping the endpoints of the strings fixed between iterations (True/False)"""
    fixed_endpoints: Optional[bool] = True
    """Input/output location for the steered MD input path"""
    steered_md_target_path: Optional[str] = "strings/string0.txt"
    """Steered MD start coordinates"""
    steered_md_start_coordinates: Optional[str] = "confout.gro"
    """gmx mdrun additional options for steered simulations"""
    mdrun_options_steered: Optional[tuple] = None
    """gmx mdrun additional options for swarm simulations"""
    mdrun_options_swarms: Optional[tuple] = None
    """gmx mdrun additional options for restrained simulations"""
    mdrun_options_restrained: Optional[tuple] = None
    """Number of gpus per node (if using GPU cluster)."""
    gpus_per_node: Optional[int] = None
    """Use a function to combine cvs"""
    use_function: Optional[bool] = False
    """
    Version of the software code, defined as stringmethod.version.
    Might be used in the future to ensure backwards compatibility.
    """
    version: Optional[str] = None
    """
    Python log level for the stringmethod package
    """
    log_level: Optional[str] = "INFO"

    def __post_init__(self):
        if self.version is None:
            self.version = VERSION

    def validate(self):
        """
        Throws exceptions if the config is invalid
        :return:
        """
        if self.swarm_size is None or self.swarm_size < 0:
            raise ConfigError("swarm_size must be >= 0")


def load_config(config_file: str) -> Config:
    if config_file is None:
        c = Config()
    else:
        with open(config_file) as json_file:
            data = json.load(json_file)
            c = Config(**data)
    c.validate()
    return c
