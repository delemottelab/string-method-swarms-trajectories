import sys
from dataclasses import dataclass
from typing import Optional

import numpy as np

from stringmethod import logger
from .base import AbstractPostprocessor
from .index_conversion import IndexConverter


@dataclass
class FreeEnergyCalculator(AbstractPostprocessor):
    """
    Takes the transition count between bins and computes the probability distribution and free energy
    """

    """Input from previous step"""
    transition_count: np.array
    """Input from previous step"""
    grid: np.array
    """detailed_balance regularizes the transition matrix while computing the stationary distribution"""
    method: Optional[str] = "detailed_balance"
    """
    Boltzmann's constant. The default value is in kcal/(mol*K)
    """
    kB: Optional[float] = 0.0019872041
    """
    System temperature
    """
    T: Optional[float] = 300.0
    probability_distribution: Optional[np.array] = None
    free_energy: Optional[np.array] = None
    _index_converter: Optional[IndexConverter] = None

    def __post_init__(self):
        if len(self.grid.shape) == 1:
            self.grid = self.grid[:, np.newaxis]
        self._index_converter = IndexConverter(
            n_dim=self.grid.shape[1], n_grid_points=self.grid.shape[0]
        )

    def _do_run(self) -> bool:
        self.probability_distribution = self.compute_probability_distribution()
        self.free_energy = self.compute_free_energy()
        return True

    def _do_persist(self):
        np.save(
            "{}/probability_distribution".format(self._get_out_dir()),
            self.probability_distribution,
        )
        np.save("{}/free_energy".format(self._get_out_dir()), self.free_energy)

    def compute_probability_distribution(self) -> np.array:
        if self.method == "detailed_balance":
            prob = self._compute_probability_distribution_detailed_balance()
        else:
            prob = self._compute_probability_distribution_eigenvector()
        prob = prob.squeeze()
        prob = self._index_converter.convert_to_grid(prob)
        return prob[:, np.newaxis] if len(prob.shape) == 1 else prob

    def compute_free_energy(self):
        fe = np.empty(self.probability_distribution.shape)
        for row_idx, p_row in enumerate(self.probability_distribution):
            for col_idx, p in enumerate(p_row):
                if p is None or np.isnan(p):  # or p <= 1e-7:
                    fe[row_idx, col_idx] = sys.float_info.max  # np.nan
                else:
                    fe[row_idx, col_idx] = -self.kB * self.T * np.log(p)
        fe -= fe.min()
        return fe

    def _compute_probability_distribution_eigenvector(self):
        """
        Find the eigenvector (s) of the transition matrix
        :param transition_count:
        :return:
        """
        transition_probability = np.zeros(self.transition_count.shape)
        transition_count = self._remove_transitions_to_isolated_bins(
            self.transition_count
        )
        for rowidx, row in enumerate(transition_count):
            # transition_probability[rowidx, rowidx] = 0
            rowsum = np.sum(row)
            if rowsum > 0:
                transition_probability[rowidx] = row / rowsum
        eigenvalues, eigenvectors = np.linalg.eig(transition_probability.T)
        stationary_solution = None
        unit_eigenval = None  # The eigenvalue closest to 1
        for idx, eigenval in enumerate(eigenvalues):
            vec = eigenvectors[:, idx]
            # logger.debug("Eigenvec for eigenvalue %s:\n%s", eigenval, vec)
            if np.isclose(1.0, eigenval, rtol=1e-2):
                neg_vec, pos_vec = vec[vec < 0], vec[vec > 0]
                if len(pos_vec) == 0:
                    # No positive entries. All must be negative. We can multiply the eigenvector by a factor of -1
                    vec = -1 * vec
                elif len(neg_vec) > 0:
                    logger.warning(
                        "Found a vector with eigenvalue ~1(%s) but with negative entries in its eigenvector",
                        eigenval,
                    )
                    continue
                if stationary_solution is not None:
                    raise Exception(
                        "Multiple stationary solutions found. Perhaps there were no transitions between states. Eigenvalues:\n%s"
                        % eigenvalues
                    )
                vec = np.real(vec)
                stationary_solution = vec / np.sum(vec)
                unit_eigenval = eigenval
        relaxation_eigenval = (
            None  # corresponds to the largest eigenvalue less than 1
        )
        for idx, eigenval in enumerate(eigenvalues):
            if eigenval < 1 and eigenval != unit_eigenval:
                if (
                    relaxation_eigenval is None
                    or eigenval > relaxation_eigenval
                ):
                    relaxation_eigenval = eigenval
        if stationary_solution is None:
            raise Exception(
                "No stationary solution found. Eigenvalues:\n%s", eigenvalues
            )
        if relaxation_eigenval is not None:
            logger.info(
                "Relaxation time for system: %s [units of lag time]. Eigenval=%s",
                -np.log(relaxation_eigenval),
                relaxation_eigenval,
            )
        return stationary_solution

    def _compute_probability_distribution_detailed_balance(self):
        nbins = self.transition_count.shape[0]
        transition_probability = np.zeros(self.transition_count.shape)
        rho = np.zeros((nbins,))
        inaccessible_states, nonstarting_states = 0, 0
        transition_count = self._remove_transitions_to_isolated_bins(
            self.transition_count
        )
        for rowidx, row in enumerate(transition_count):
            # transition_probability[rowidx, rowidx] = 0
            rowsum = np.sum(row)
            if rowsum > 0:
                # transition_probability[rowidx, rowidx] = 0
                transition_probability[rowidx] = row / rowsum
                # transition_probability[rowidx, rowidx] = -rowsum
            else:
                rho[rowidx] = np.nan

        if inaccessible_states > 0 or nonstarting_states > 0:
            logger.warning(
                "Found %s inaccessible states and %s states with no starting points.",
                inaccessible_states,
                nonstarting_states,
            )
        # Set up starting guess for distribution: all accessible states equal
        for i, rhoi in enumerate(rho):
            if np.isnan(rhoi):
                rho[i] = 0
            else:
                rho[i] = 1
        rho = rho / np.sum(rho)
        convergences = []
        convergence = 100
        while convergence > 1e-6:
            last = rho  # np.copy(rho)
            for k, rhok in enumerate(rho):
                if rhok == 0:
                    continue
                crossterm = np.dot(rho, transition_probability[:, k]) - np.sum(
                    rhok * transition_probability[k, :]
                )
                # crossterm = 0
                # for l, rhol in enumerate(rho):
                #     if l != k:
                #         crossterm += rhol * transition_probability[l, k] - rhok * transition_probability[k, l]
                if rhok == 0 and crossterm > 0:
                    logger.warning(
                        "NOOOO for index %s. Crossterm %s rhok %s",
                        k,
                        crossterm,
                        rhok,
                    )
                rho[k] = rhok + crossterm
            rho = rho / np.sum(rho)
            if last is not None:
                convergence = np.linalg.norm(rho - last)
                convergences.append(convergence)
        logger.debug(
            "Converged with master equation after %s iterations",
            len(convergences),
        )
        # plt.plot(convergences, label="Convergence")
        # plt.show()
        if len(rho[rho == 0]) < inaccessible_states:
            raise Exception(
                "Something went wrong. Number inaccessible states differ %s vs. %s"
                % (len(rho[rho == 0]), inaccessible_states)
            )
        return rho

    def _remove_transitions_to_isolated_bins(self, transition_count):
        """Remove all transitions which moves from a bin with no starting points"""
        last_inaccessible_states, last_nonstarting_states = -1, -1
        inaccessible_states, nonstarting_states = 1, 1
        while (
            inaccessible_states != last_inaccessible_states
            or nonstarting_states != last_nonstarting_states
        ):
            last_inaccessible_states, last_nonstarting_states = (
                inaccessible_states,
                nonstarting_states,
            )
            inaccessible_states, nonstarting_states, accessible_states = (
                0,
                0,
                0,
            )
            for rowidx, row in enumerate(transition_count):
                rowsum = np.sum(row)
                if rowsum == 0:
                    # transition_probability[rowidx] = 0
                    if np.sum(transition_count[:, rowidx]) == 0:
                        # logger.warning("Found inaccessible state at index %s ", rowidx)
                        inaccessible_states += 1
                        # rho[rowidx] = np.nan
                    else:
                        # logger.warning("Found non-starting states")
                        nonstarting_states += 1
                    # TODO see if this makes sense: to set all transition into this state to zero to completely isolate it!
                    transition_count[:, rowidx] = 0
                else:
                    accessible_states += 1
        if inaccessible_states > 0 or nonstarting_states > 0:
            logger.warning(
                "Found %s accessible states, %s inaccessible states and %s states with no starting points.",
                accessible_states,
                inaccessible_states,
                nonstarting_states,
            )
        return transition_count
