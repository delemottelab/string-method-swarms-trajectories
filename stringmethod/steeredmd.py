from dataclasses import dataclass

from stringmethod.config import Config


@dataclass
class SteeredRunner(object):
    config: Config

    def __post_init__(self):
        raise NotImplementedError("Steered MD not implemented")

    def run(self):
        pass
