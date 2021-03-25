import unittest

import numpy as np

from stringmethod.config import Config
from stringmethod.postprocessing import *


def create_constant_probability_distribution(n_grid_points, n_transitions=1):
    prob = np.zeros((n_grid_points, n_grid_points))
    prob += 1.0 / prob.size
    minx, maxx = 0, n_grid_points - 1
    miny, maxy = 1, n_grid_points
    grid = np.array(
        [
            np.linspace(minx, maxx, n_grid_points),
            np.linspace(miny, maxy, n_grid_points),
        ]
    ).T
    # Create transition points from every grid point to all other
    delta = grid[1, 0] * 0.49  # Some noise smaller than the grid size
    vals = []
    for startx in grid[:, 0]:
        for starty in grid[:, 1]:
            for endx in grid[:, 0]:
                for endy in grid[:, 1]:
                    transition = np.empty((2, 2))
                    transition[0, 0] = startx
                    transition[0, 1] = starty
                    transition[1, 0] = endx
                    transition[1, 1] = endy
                    for n in range(n_transitions):
                        if (
                            maxx > startx > minx
                            and maxy > starty > miny
                            and maxx > endx > minx
                            and maxy > endy > miny
                        ):
                            # Displace atoms slightly as long as we don't mess up the grid boundaries
                            r = (np.random.rand() - 0.5) * delta
                            vals.append(transition + r)
                        else:
                            vals.append(transition)

    vals = np.array(vals)
    return prob, grid, vals


class TestPostProcessing(unittest.TestCase):
    def setUp(self):
        self.config = Config()

    def test_correct_transition_count(self):
        n_grid_points = 10
        n_transitions = 3
        (
            in_prob,
            grid,
            cv_coordinates,
        ) = create_constant_probability_distribution(
            n_grid_points=n_grid_points, n_transitions=n_transitions
        )
        tc = TransitionCountCalculator(
            config=self.config,
            n_grid_points=n_grid_points,
            cv_coordinates=cv_coordinates,
        )
        tc.run()
        self.assertEqual(grid.shape, tc.grid.shape)
        self.assertAlmostEqual(
            abs(grid - tc.grid).max(), 0, places=4, msg="Grids differ"
        )
        print(tc.transition_count)
        self.assertTrue(
            np.all(tc.transition_count == n_transitions),
            "Transition count is constant",
        )

    def test_correct_probability_distribution(self):
        n_grid_points = 10
        (
            in_prob,
            grid,
            cv_coordinates,
        ) = create_constant_probability_distribution(
            n_grid_points=n_grid_points
        )
        tc = TransitionCountCalculator(
            config=self.config,
            n_grid_points=n_grid_points,
            cv_coordinates=cv_coordinates,
        )
        tc.run()
        fc = FreeEnergyCalculator(
            config=self.config,
            grid=tc.grid,
            transition_count=tc.transition_count,
        )
        fc.run()
        out_prob = fc.probability_distribution
        self.assertEqual(in_prob.shape, out_prob.shape)
        for row_idx, p_row in enumerate(in_prob):
            for col_idx, p_in in enumerate(p_row):
                p_out = out_prob[row_idx, col_idx]
                self.assertAlmostEqual(
                    p_out,
                    p_in,
                    places=4,
                    msg="Probability not equal at index %s, %s"
                    % (row_idx, col_idx),
                )
        self.assertAlmostEqual(
            1.0,
            out_prob.sum(),
            places=4,
            msg="Total probability should equal 1",
        )

    def test_two_state_1d_probability_distribution(self):
        n_grid_points = 2
        in_prob = np.array([[2 / 3], [1 / 3]])
        cv_coordinates = np.array(
            [[0, 0], [0, 0], [0, 1], [1, 1], [1, 0], [1, 0]]
        )
        in_transition_count = np.array([[2, 1], [2, 1]])
        tc = TransitionCountCalculator(
            config=self.config,
            n_grid_points=n_grid_points,
            cv_coordinates=cv_coordinates,
        )
        tc.run()
        self.assertAlmostEqual(
            abs(in_transition_count - tc.transition_count).max(),
            0,
            places=4,
            msg="Transition count differs",
        )
        fc = FreeEnergyCalculator(
            config=self.config,
            grid=tc.grid,
            transition_count=tc.transition_count,
        )
        fc.run()
        out_prob = fc.probability_distribution
        self.assertEqual(in_prob.shape, out_prob.shape)
        for row_idx, p_row in enumerate(in_prob):
            for col_idx, p_in in enumerate(p_row):
                p_out = out_prob[row_idx, col_idx]
                self.assertAlmostEqual(
                    p_out,
                    p_in,
                    places=4,
                    msg="Probability not equal at index %s, %s"
                    % (row_idx, col_idx),
                )
        self.assertAlmostEqual(
            1.0,
            out_prob.sum(),
            places=4,
            msg="Total probability should equal 1",
        )


if __name__ == "__main__":
    unittest.main()
