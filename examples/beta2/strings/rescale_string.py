import numpy as np
# This convertsa numpy file where the string was scaled back to its values in radians
input_string = np.loadtxt("string0-scaled.txt")
scales = np.array([
	0.5661925673484802,
	1.7603273391723633,
	1.1804057359695435,
	0.7458944320678711,
	1.2011606693267822
])
offsets = np.array([
	0.9345757365226746,
	1.6520638465881348,
	1.7898653745651245,
	2.010006904602051,
	0.6673485636711121,
])
string = input_string*scales + offsets
print("Input string range of values: ", input_string.max()- input_string.min(), " [nm]")
print("Output string range of values: ", string.max()- string.min(), " [nm]")
np.savetxt("string0.txt", string)