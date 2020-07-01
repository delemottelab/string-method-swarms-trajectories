import sys

import matplotlib.pyplot as plt
import numpy as np

sys.path.append("../../../")
from stringmethod.config import *
from stringmethod.postprocessing import *


def show(grid, free_energy, string, fe_cut_off=10):
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
                          cmap=plt.cm.rainbow)
        cbar = plt.colorbar(im)
        cbar.set_label("[kcal/mol]")
        if string is not None:
            plt.plot(string[:, 0], string[:, 1], '--o', label="String")
            plt.legend()
        plt.ylabel("$\psi$")
    plt.xlabel("$\phi$")
    plt.tight_layout()
    plt.savefig("free_energy.png")
    plt.show()


def compute():
    config = load_config("config.json")
    cv_coordinates = np.load("postprocessing/cv_coordinates.npy")
    string = np.loadtxt("strings/string0.txt")
    # Handle periodic boundary conditions
    # Two options are shown below. Using modulus or taking the sine value
    offset = -np.pi / 4  # you may play around with an offset to make the plot more continuous
    cv_coordinates = offset + cv_coordinates % (2 * np.pi)
    string = offset + string % (2 * np.pi)
    # Note that simply taking the sine value reduces dimensionality. Use with care
    # cv_coordinates = np.sin(cv_coordinates)
    # string = np.sin(string)

    # Select only phi
    # cv_coordinates = cv_coordinates[:, :, 0]
    tc = TransitionCountCalculator(config=config,
                                   n_grid_points=10,
                                   cv_coordinates=cv_coordinates)
    tc.run()
    tc.persist()
    fc = FreeEnergyCalculator(config=config,
                              grid=tc.grid,
                              transition_count=tc.transition_count)
    fc.run()
    fc.persist()
    return tc.grid, fc.free_energy, string


if __name__ == "__main__":
    grid, free_energy, string = compute()
    show(grid, free_energy, string)
