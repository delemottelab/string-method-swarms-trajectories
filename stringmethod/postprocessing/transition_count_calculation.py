from dataclasses import dataclass
from typing import Optional

import numpy as np

from stringmethod import logger
from .base import AbstractPostprocessor
from .index_conversion import IndexConverter


@dataclass
class TransitionCountCalculator(AbstractPostprocessor):
    """
    Takes CV input output values, discretizes the CV space and computes the transition count between bins
    """

    """
    Input from previous step. 
    First index corresponds to a trajectory.
    Second index sets the frame in that trajectory.
    Third index sets the CV values in that frame.
    """
    cv_coordinates: np.array
    method: Optional[str] = "detailed_balance"
    n_grid_points: Optional[int] = 30
    transition_count: Optional[np.array] = None
    grid: Optional[np.array] = None
    _index_converter: Optional[IndexConverter] = None

    def __post_init__(self):
        if len(self.cv_coordinates.shape) < 3:
            # A single CV, just add an extra dimension
            self.cv_coordinates = self.cv_coordinates[:, :, np.newaxis]
        self._index_converter = IndexConverter(
            n_dim=self.cv_coordinates.shape[2],
            n_grid_points=self.n_grid_points,
        )

    def _do_run(self) -> bool:
        self.grid = self.setup_grid()
        self.transition_count = self.compute_transition_count()
        return True

    def _do_persist(self):
        np.save(
            "{}/transition_count".format(self._get_out_dir()),
            self.transition_count,
        )
        np.save("{}/grid".format(self._get_out_dir()), self.grid)

    def setup_grid(self) -> np.array:
        n_cvs = self.cv_coordinates.shape[2]
        grid = np.empty((self.n_grid_points, n_cvs))
        for cv in range(n_cvs):
            vals = self.cv_coordinates[:, :, cv]
            grid[:, cv] = np.linspace(
                vals.min(), vals.max(), self.n_grid_points
            )
        return grid

    def compute_transition_count(self) -> np.array:
        n_cvs = self.cv_coordinates.shape[2]
        nbins = self.n_grid_points ** n_cvs
        transition_count = np.zeros((nbins, nbins))  # Transition per bin
        for t in self.cv_coordinates:
            if np.any(np.isnan(t) | np.isinf(t)):
                logger.warning("Found NaN or Inf transition. Ignoring it.")
                continue
            start_grid = self._find_grid_coordinates(t[0])
            end_grid = self._find_grid_coordinates(t[-1])
            start_bin = self._index_converter.convert_to_bin_idx(start_grid)
            end_bin = self._index_converter.convert_to_bin_idx(end_grid)
            transition_count[start_bin, end_bin] += 1
        return transition_count

    def _find_grid_coordinates(self, cv_values: np.array):
        return np.array(
            [
                (np.abs(cv_values[cv_idx] - self.grid[:, cv_idx])).argmin()
                for cv_idx in range(self.grid.shape[1])
            ]
        )
