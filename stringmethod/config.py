import json
from dataclasses import dataclass
from typing import Optional

from stringmethod import VERSION


@dataclass
class Config(object):
    simu_id: Optional[str] = "string_simulation"
    string_dir: Optional[str] = "strings"
    md_dir: Optional[str] = "md"
    mdp_dir: Optional[str] = "mdp"
    topology_dir: Optional[str] = "topology"
    n_cvs: Optional[int] = None
    swarm_size: Optional[int] = 16
    n_points: Optional[int] = 10
    max_iterations: Optional[int] = 100
    fixed_endpoints: Optional[bool] = True
    version: Optional[str] = None
    log_level: Optional[str] = 'INFO'

    def __post_init__(self):
        if self.version is None:
            self.version = VERSION

    def validate(self):
        if not self.fixed_endpoints:
            raise NotImplementedError("Endpoints must be fixed")
        if self.n_cvs is None:
            raise ValueError("n_cvs must be set in config file")


def load_config(config_file: str) -> Config:
    with open(config_file) as json_file:
        data = json.load(json_file)
        c = Config(**data)
        c.validate()
        return c
