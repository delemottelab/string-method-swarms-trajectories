import glob
import sys, os
from dataclasses import dataclass
from typing import Optional

import numpy as np
import re
from stringmethod import logger
import mdtools
from stringmethod.config import Config
from .base import AbstractPostprocessor


@dataclass
class CvValueExtractor(AbstractPostprocessor):
    md_dir: Optional[str] = "md"
    """
    Loads all swarms' start and end CV coordinates and puts them in an array for further postprocessing
    """
    first_iteration: Optional[int] = 1
    last_iteration: Optional[int] = sys.maxsize
    """"
    First index corresponds to a trajectory.
    Second index sets the frame in that trajectory.
    Third index sets the CV values in that frame.
    """
    cv_coordinates: Optional[np.array] = None
    use_plumed: Optional[bool] = False

    def __post_init__(self):
        pass
    
    def _natural_sort(self, l):
        convert = lambda text: int(text) if text.isdigit() else text.lower()
        alphanum_key = lambda key: [convert(c) for c in re.split("([0-9]+)", key)]
        return sorted(l, key=alphanum_key)

    def _do_run(self) -> bool:
        self.cv_coordinates = self.compute_cv_coordinates()
        return True

    def compute_cv_coordinates(self) -> np.array:
        logger.info("Remember to remove unfinished strings")
        if not os.path.isdir(self._get_out_dir()):
            os.mkdir(self._get_out_dir())
        cv_coordinates = None
        for it in range(self.first_iteration, self.last_iteration + 1):
            logger.info("Processing iteration {}".format(it))
            iter_data = "{}/cv_iter{}.npy".format(self._get_out_dir(), it)
            if os.path.isfile(iter_data):
                values = np.load(iter_data)
            else:
                if not self.use_plumed:
                    iteration_md_dir = "{}/{}/*/s*/*xvg".format(self.md_dir, it)
                else:
                    iteration_md_dir = "{}/{}/*/s*/colvar".format(self.md_dir, it)
                xvg_files = self._natural_sort(glob.glob(iteration_md_dir))
                if len(xvg_files) == 0:
                    logger.info(
                        "No output files found for iteration %s. Not looking further",
                        it,
                    )
                    return cv_coordinates
                values = None
                for file_idx, xf in enumerate(xvg_files):
                    data = mdtools.load_xvg(file_name=xf)
                    # Skip first column which contains the time and include only first and last frame
                    data = data[[0, -1], 1:]
                    if values is None:
                        n_cvs = data.shape[1]
                        values = np.empty((len(xvg_files), 2, n_cvs))
                    values[file_idx, :, :] = data
                if it < self.last_iteration:
                    np.save(iter_data, values)
            if cv_coordinates is None:
                cv_coordinates = values
            else:
                cv_coordinates = np.append(cv_coordinates, values, axis=0)
        return cv_coordinates

    def _do_persist(self):
        np.save(
            "{}/cv_coordinates".format(self._get_out_dir()),
            self.cv_coordinates,
        )
