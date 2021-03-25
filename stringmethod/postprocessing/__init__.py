from stringmethod.config import Config
from .cv_value_extraction import CvValueExtractor
from .free_energy_calculation import FreeEnergyCalculator
from .transition_count_calculation import TransitionCountCalculator


def run(config: Config):
    ce = CvValueExtractor.from_config(config=config, md_dir=config.md_dir)
    ce.run()
    ce.persist()
    tc = TransitionCountCalculator.from_config(
        config=config, cv_coordinates=ce.cv_coordinates
    )
    tc.run()
    tc.persist()
    fc = FreeEnergyCalculator.from_config(
        config=config, transition_count=tc.transition_count, grid=tc.grid
    )
    fc.run()
    fc.persist()


__all__ = [
    "CvValueExtractor",
    "FreeEnergyCalculator",
    "TransitionCountCalculator",
    "run",
]
