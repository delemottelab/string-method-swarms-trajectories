import numpy as np


class IndexConverterException(Exception):
    pass


class IndexConverter(object):
    """
    Helper class to convert grid indicies to bin indices for constructing the transition matrix.

    Written a long, long time ago.
    """

    def __init__(self, n_dim: int, n_grid_points: int):
        self.n_dim = n_dim
        self.n_grid_points = n_grid_points
        self._modulus = [
            n_grid_points ** (n_dim - j - 1) for j in range(n_dim)
        ]
        self._zero_dim = np.zeros((self.n_dim,))
        self.n_bins = n_grid_points ** n_dim

    def convert_to_vector(self, grid):
        if grid.shape[0] != self.n_grid_points:
            raise IndexConverterException(
                "Wrong dimension of grid. Expect length of %s got %s"
                % (self.n_grid_points, grid.shape[0])
            )
        vector = np.empty((self.n_bins,))
        for bin_idx in range(self.n_bins):
            vector[bin_idx] = grid[tuple(self.convert_to_grid_idx(bin_idx))]
        return vector

    def convert_to_grid(self, vector):
        grid_shape = tuple(
            np.zeros(self.n_dim).astype(int) + self.n_grid_points
        )
        if len(vector.shape) > 1:
            grids = np.empty((len(vector),) + grid_shape)
            for idx, v in enumerate(vector):
                grids[idx] = self.convert_to_grid(v)
            return grids
        else:
            grid = np.zeros(grid_shape)
            for idx in range(len(vector)):
                grid[tuple(self.convert_to_grid_idx(idx))] = vector[idx]
            return grid

    def convert_to_grid_idx(self, bin_idx):
        if bin_idx >= self.n_bins or bin_idx < 0:
            print(self.n_bins, self.n_dim, self.n_bins ** self.n_dim)
            raise IndexConverterException(
                "Invalid index %s. You are probably outside the grid..."
                % bin_idx
            )
        grid_idx = (
            (self._zero_dim + bin_idx) / self._modulus
        ) % self.n_grid_points
        return grid_idx.astype(int)

    def convert_to_bin_idx(self, grid_idx):
        bin_idx = int(np.rint(np.sum(grid_idx * self._modulus)))
        if bin_idx >= self.n_bins or bin_idx < 0:
            raise IndexConverterException(
                "Invalid bin index %s. You are probably outside the grid. Size:%s"
                % (bin_idx, self.n_bins)
            )
        return bin_idx
