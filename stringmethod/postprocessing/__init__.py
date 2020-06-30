from stringmethod.config import Config
from .cv_value_extraction import CvValueExtractor
from .free_energy_calculation import FreeEnergyCalculator
from .transition_count_calculation import TransitionCountCalculator


def run(config: Config):
    ce = CvValueExtractor(config=config)
    ce.run()
    ce.persist()
    tc = TransitionCountCalculator(config=config, cv_coordinates=ce.cv_coordinates)
    tc.run()
    tc.persist()
    fc = FreeEnergyCalculator(config=config, transition_count=tc.transition_count)
    fc.run()
    fc.persist()


__all__ = ['CvValueExtractor', 'FreeEnergyCalculator', 'TransitionCountCalculator', 'run']
