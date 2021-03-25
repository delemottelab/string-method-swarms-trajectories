"""
Module to add custom functions for the user to modify cvs on the fly.
"""


def custom_function(data):
    """
    Custom function that takes in the array of swarms cvs at a after iteration and does some custom transformation on them preserving the shape of the array.
    
    This allows for example to make linnear combinations of distances the cvs. This de facto compensates for the limitations of the pull-code of gmx as of 2021.
    """
    from numpy import ndarray

    def take_mean_pairs(data):
        for i in range(0, data.shape[1], 2):
            m = 0.5 * (data[:, i] + data[:, i + 1])
            data[:, i] = m
            data[:, i + 1] = m
        return data

    shape = data.shape

    data = take_mean_pairs(data)

    assert data.shape == shape, "function changed shape of array"
    assert isinstance(data, ndarray), "function changed shape of array"

    return data
