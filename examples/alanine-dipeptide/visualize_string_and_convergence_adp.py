import os
import sys

sys.path.append("../../../")
import matplotlib.pyplot as plt
import numpy as np


def show(max_iter=int(1e10), stride=50):
    last = None
    convergence = []
    iterations = []
    for it in range(0, max_iter + 1, stride):
        file = "strings/string{}.txt".format(it)
        if not os.path.isfile(file):
            print("File '%s' not found. Not looking for more iterations." % file)
            break
        s = np.loadtxt(file)
        # Taking the modulus of 2pi fixes PBC's somewhat
        s = s % 360
        plt.plot(s[:, 0], s[:, 1], '-o', label=str(it), alpha=0.75)
        if last is not None:
            mean_norm = (np.linalg.norm(s) + np.linalg.norm(last)) / 2
            c = np.linalg.norm(s - last) / mean_norm
            convergence.append(c)
            iterations.append(it)
        last = s
    plt.xlabel("$\phi [degrees]$")
    plt.ylabel("$\psi [degrees]$")
    plt.legend()
    plt.tight_layout()
    plt.savefig("strings.png")
    plt.show()

    plt.plot(iterations, convergence, '-*')
    plt.xlabel("Iteration")
    plt.ylabel("Convergence")
    plt.tight_layout()
    plt.savefig("convergence.png")
    plt.show()


if __name__ == "__main__":
    show()
