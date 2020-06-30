import sys

import matplotlib.pyplot as plt
import numpy as np

sys.path.append("../../../")
from stringmethod.config import *
from stringmethod.postprocessing import *


def show(grid, free_energy, string, fe_cut_off=10):
    n_grid = grid.shape[0]
    phi = grid[:, 0]
    psi = grid[:, 1]
    free_energy = free_energy.reshape((n_grid, n_grid))
    free_energy[free_energy > fe_cut_off] = np.nan
    im = plt.contourf(phi,
                      psi,
                      free_energy.T,  # TODO should we take the transform of the matrix or not?
                      levels=20,
                      cmap=plt.cm.rainbow)
    cbar = plt.colorbar(im)
    cbar.set_label("[kcal/mol]")
    plt.plot(string[:, 0], string[:, 1], '--o', label="String")
    plt.xlabel("$\sin(2\phi)$")
    plt.ylabel("$\sin(2\psi)$")
    plt.legend()
    plt.show()
    plt.savefig("free_energy.png")


def compute():
    config = load_config("../config.json")
    cv_coordinates = np.load("cv_coordinates.npy")
    string = np.loadtxt("../strings/string0.txt")
    string = string

    # Handle periodic boundary conditions
    # Two options are shown below. Using modulus or taking the sine value
    cv_coordinates = cv_coordinates % (2 * np.pi)
    string = string % (2 * np.pi)
    cv_coordinates = np.sin(2 * cv_coordinates)
    string = np.sin(2 * string)

    tc = TransitionCountCalculator(config=config,
                                   n_grid_points=10,
                                   cv_coordinates=cv_coordinates)
    tc.run()
    tc.persist()
    fc = FreeEnergyCalculator(config=config,
                              transition_count=tc.transition_count)
    fc.run()
    fc.persist()
    return tc.grid, fc.free_energy, string


if __name__ == "__main__":
    grid, free_energy, string = compute()
    show(grid, free_energy, string)
