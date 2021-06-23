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
        for i in [
            0,
            6,
            8,
            10,
        ]:
            m = 0.5 * (data[:, i] + data[:, i + 1])
            data[:, i] = m
            data[:, i + 1] = m
        for i in [2, 12, 16, 20, 24, 28, 32]:
            m = 0.25 * (
                data[:, i] + data[:, i + 1] + data[:, i + 2] + data[:, i + 3]
            )
            data[:, i] = m
            data[:, i + 1] = m
            data[:, i + 2] = m
            data[:, i + 3] = m
        return data

    shape = data.shape

    data = take_mean_pairs(data)

    assert data.shape == shape, "function changed shape of array"
    assert isinstance(data, ndarray), "function changed shape of array"

    return data
