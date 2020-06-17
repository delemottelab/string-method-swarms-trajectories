import json
from dataclasses import dataclass
from typing import Optional

from stringmethod import VERSION


@dataclass
class Config(object):
    simu_id: Optional[str] = "string_simulation"
    output_dir: Optional[str] = "output"
    n_cvs: Optional[int] = 2
    swarm_size: Optional[int] = 16
    n_points: Optional[int] = 10
    initial_string: Optional[str] = None
    fixed_endpoints: Optional[bool] = True
    version: Optional[str] = None

    def __post_init__(self):
        if self.version is None:
            version = VERSION


def load_config(config_file: str) -> Config:
    with open(config_file) as json_file:
        data = json.load(json_file)
        return Config(**data)
