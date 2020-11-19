import os
import sys

sys.path.append("../../../")
import matplotlib.pyplot as plt
import numpy as np


def show(max_iter=int(1e10), strings_per_average=20):
    strings = []
    start_iteration = 1  # First iteration of the averaged string. Used for label-making
    for it in range(0, max_iter + 1):
        file = "strings/string{}.txt".format(it)
        end_reached = False
        if not os.path.isfile(file):
            print("File '%s' not found. Not looking for more iterations." % file)
            end_reached = True
        else:
            s = np.loadtxt(file)
            strings.append(s)
        if len(strings) > 0 and (it % strings_per_average == 0 or end_reached):
            savg = np.mean(strings, axis=0)
            serr = np.std(strings, axis=0) / np.sqrt(len(strings))
            label = 'initial string' if it == 0 else 'iteration {}-{}'.format(start_iteration, it)
            plt.errorbar(savg[:, 0], savg[:, 1], fmt='--', yerr=serr[:, 1], xerr=serr[:, 0], label=label, alpha=0.75)
            strings = []
            start_iteration = it + 1
        if end_reached:
            break
    plt.xlabel("$\phi$ [degrees]")
    plt.ylabel("$\psi$ [degrees]")
    plt.legend()
    plt.tight_layout()
    plt.savefig("strings.png")
    plt.show()


if __name__ == "__main__":
    show()
