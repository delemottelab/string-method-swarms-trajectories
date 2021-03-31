import numpy as np

# This converts a numpy file where the string was scaled back to its values in radians
string = np.loadtxt("string0-scaled.txt")
scales = np.array([6.283, 6.283])
offsets = np.array([-3.142, -3.142])
string = string * scales + offsets
print("Range of values: ", string.max() - string.min(), " [rad]")
np.savetxt("string0.txt", string)
