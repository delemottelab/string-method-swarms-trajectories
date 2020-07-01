import sys

import matplotlib.pyplot as plt
import numpy as np

sys.path.append("../../../")
from stringmethod.config import *
from stringmethod.postprocessing import *
from matplotlib import ticker, colors


def show(grid: np.array, free_energy: np.array, string: np.array = None, fe_cut_off: float = 10):
    free_energy[free_energy > fe_cut_off] = np.nan
    phi = grid[:, 0]
    if free_energy.shape[1] == 1:
        plt.plot(phi, free_energy, '--o')
        plt.ylabel("Free Energy [kcal/mol]")
    else:
        psi = grid[:, 1]
        im = plt.contourf(phi,
                          psi,
                          free_energy.T,  # TODO should we take the transform of the matrix or not?
                          levels=20,
                          norm=colors.PowerNorm(gamma=1 / 3),
                          cmap=plt.cm.rainbow)
        cbar = plt.colorbar(im)
        cbar.set_label("[kcal/mol]")
        if string is not None:
            plt.plot(string[:, 0], string[:, 1], '--o', label="String")
            plt.legend()
    plt.tight_layout()
    plt.savefig("free_energy.png")
    plt.show()


def handle_periodicity(cv_coordinates: np.array, dpca: bool = True):
    """
    # Handle periodic boundary conditions by taking modules 2pi or performing dihedral-PCA
    :param dpca: if True, perform dPCA onto the input and convert it into two components
    :param cv_coordinates:
    :return:
    """

    offset = -np.pi / 4  # you may play around with an offset to make the plot more continuous
    cv_coordinates = offset + cv_coordinates % (2 * np.pi)

    if dpca:
        from sklearn.decomposition import PCA
        new_coords = np.empty((len(cv_coordinates), cv_coordinates.shape[1], 4))
        new_coords[:, :, 0] = np.sin(cv_coordinates[:, :, 0])
        new_coords[:, :, 1] = np.cos(cv_coordinates[:, :, 0])
        new_coords[:, :, 2] = np.sin(cv_coordinates[:, :, 1])
        new_coords[:, :, 3] = np.cos(cv_coordinates[:, :, 1])
        pca = PCA(n_components=2)
        pca.fit(new_coords.reshape((2 * len(new_coords), 4)))
        for idx, nc in enumerate(new_coords):
            cv_coordinates[idx] = pca.transform(nc)

    return cv_coordinates


def compute():
    config = load_config("config.json")
    cv_coordinates = np.load("postprocessing/cv_coordinates.npy")
    cv_coordinates = handle_periodicity(cv_coordinates)

    # Uncomment to only select one CV
    # cv_coordinates = cv_coordinates[:, :, 0]
    tc = TransitionCountCalculator(config=config,
                                   n_grid_points=13,
                                   cv_coordinates=cv_coordinates)
    tc.run()
    tc.persist()
    fc = FreeEnergyCalculator(config=config,
                              grid=tc.grid,
                              transition_count=tc.transition_count)
    fc.run()
    fc.persist()
    return tc.grid, fc.free_energy


if __name__ == "__main__":
    grid, free_energy = compute()
    show(grid, free_energy)