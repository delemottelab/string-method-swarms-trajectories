from dataclasses import dataclass
from typing import Optional

import numpy as np


class NotInstantiatedError(Exception):
    pass


@dataclass
class MinMaxScaler(object):
    """
    Class mimicking sklearn's MinMaxScaler
    Used for normalizing the string
    """

    _scale: Optional[np.array] = None
    _offset: Optional[np.array] = None

    def fit_transform(self, arr: np.array) -> np.array:
        self.fit(arr)
        return self.transform(arr)

    def inverse_transform(self, arr: np.array) -> np.array:
        if self._scale is None or self._offset is None:
            raise NotInstantiatedError()
        return arr * self._scale + self._offset

    def fit(self, arr: np.array) -> None:
        self._offset = arr.min(axis=0)
        self._scale = arr.max(axis=0) - self._offset

    def transform(self, arr: np.array) -> np.array:
        if self._scale is None or self._offset is None:
            raise NotInstantiatedError()
        return (arr - self._offset) / self._scale
