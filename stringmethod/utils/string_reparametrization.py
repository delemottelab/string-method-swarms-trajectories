import numpy as np

from stringmethod import logger


def compute_path_length(path, S=None):
    L = 0  # total curve length
    for i in range(0, len(path) - 1):
        point1, point2 = path[i], path[i + 1]
        if S is not None:
            point1 = np.append(point1, S(point1))
            point2 = np.append(point2, S(point2))
        L += np.linalg.norm(point2 - point1)
    return L


def _linear_reparametrization(
    path, epsilon, arclength_weight, check_correctness=True
):
    """One iteration of linear reparametrization"""
    # global failing_path
    arc_count = len(path) - 1
    L = compute_path_length(path)
    # arc_length = L / arc_count  # point to point distance
    new_path = np.empty(path.shape)
    dl = 0  # extra length remaining from previous arc step
    # endpoints fixes
    new_path[0] = path[0]
    new_path[arc_count] = path[arc_count]
    next_old_point_idx, new_point_idx = 1, 1
    current_point = path[0]
    veclength = 0  # Define here for better trouble shooting
    while new_point_idx < len(path) - 1:
        arc_length = L * arclength_weight[new_point_idx - 1]
        displacement = arc_length - dl  # displacement along unitvector
        if len(path) == next_old_point_idx:
            # failing_path = path
            logger.debug("Failing path: %s", path)
            logger.warning(
                "Index too big.. displacement=%s, new_point_idx=%s, next_old_point_idx=%s, dl=%s, arc_length=%s, L=%s, veclength=%s",
                displacement,
                new_point_idx,
                next_old_point_idx,
                dl,
                arc_length,
                L,
                veclength,
            )
        next_point = path[next_old_point_idx]
        vector = next_point - current_point  # vector to next point
        # We should place our point along this vector if the vector is long enough
        veclength = np.linalg.norm(vector)
        if (
            displacement > veclength + epsilon
        ):  # Note that to avoid troubles with double precision we consider points to be equal if they are within 'epsilon' precision
            # Step forward to next point in the old path since no new point fits on this vector
            dl += veclength
            current_point = next_point
            next_old_point_idx += 1
        else:
            # Create a point in the new path and step forward towards intermediate point along unit vector
            unitvec = vector / veclength
            current_point = current_point + unitvec * displacement
            new_path[new_point_idx] = current_point
            new_point_idx += 1
            dl = 0
            # Here we do not step forward in the old path since more points might fit along that vector
    if check_correctness:
        if new_point_idx != arc_count or dl > arc_length / 100:
            logger.warning(
                "Did not reparametrize correctly. new_point_idx=%s, dl=%s, arc_length=%s, arc_count=%s, L=%s",
                new_point_idx,
                dl,
                arc_length,
                arc_count,
                L,
            )
        for i in range(0, arc_count):
            d = np.linalg.norm(new_path[i] - new_path[i + 1])
            if abs(d - arc_length) > epsilon:
                logger.warning(
                    "Arc length wrong, %s instead of %s for points %s-%s",
                    d,
                    arc_length,
                    i,
                    i + 1,
                )
    return new_path


def reparametrize_path_iter(
    path,
    check_correctness=False,
    epsilon=1e-5,
    max_iterations=999,
    convergence=1e-2,
    arclength_weight=None,
):
    """
    Given initial points on a path, realign the points equidistantly along the same path
    :param path: an np array with points along the string as rows and dimensions as columns
    :param check_correctness:
    :param epsilon: small number on which two doubles are considered equal
    :param max_iterations:
    :param convergence: when the string has been considered to converge. Measured as norm(newpath-oldpath)/norm(oldpath)
    :param arclength_weight: How far apart the arcs (distance between two points) should be relative each othter. If =None, points will be equidistant. This does not need to be normalized, but keep the entries > 0
    :return:
    """
    len_path = len(path)
    if arclength_weight is None:
        arclength_weight = np.zeros((len_path - 1,)) + 1 / (
            len_path - 1
        )  # Equal weights for all
    elif len(arclength_weight) != len_path - 1:
        raise Exception(
            "Expected arclength weights to be of length %s. Got %s"
            % (len_path - 1, len(arclength_weight))
        )
    else:
        # Normalize weight
        arclength_weight = arclength_weight / sum(arclength_weight)
    previous_path = path
    new_path = path
    for itr in range(0, max_iterations):
        new_path = _linear_reparametrization(
            previous_path,
            epsilon,
            arclength_weight,
            check_correctness=check_correctness,
        )
        dist = np.linalg.norm(new_path - previous_path) / np.linalg.norm(
            previous_path
        )
        if dist <= convergence:
            break
        previous_path = new_path
    return new_path


def reparametrize_path_grid(path, resolution=30000):
    """
    Given initial points on a path, realign the points equidistantly along the same path.
    Originally from https://stackoverflow.com/questions/19117660/how-to-generate-equispaced-interpolating-values
    The resolution ngrid sets the number of grid points between two points on the string.
    """
    # find lots of points on the piecewise linear curve defined by x and y
    if len(path.shape) == 1:
        dim = 1
        path2 = np.empty((len(path), 1))
        path2[:, 0] = path
        path = path2
    else:
        dim = path.shape[1]
    arc_count = len(path) - 1
    L = compute_path_length(path)
    arc_length = L / arc_count  # point to point distance
    ngrid = resolution * arc_count
    grid = np.empty((dim, ngrid))
    t = np.linspace(0, len(path), ngrid)
    for i in range(dim):
        grid[i] = np.interp(t, np.arange(len(path)), path[:, i])
    i, idx = 0, [0]
    while i < ngrid:
        total_dist = 0
        for j in range(i + 1, ngrid):
            total_dist += np.linalg.norm(grid[:, j] - grid[:, j - 1])
            if total_dist >= arc_length:
                # TODO not that we always overestimate the arc_length here.
                # A slightly more accurate approximation is to take the point that gives the closest arc_length,
                # i.e. an arc_length which can be too short.
                idx.append(j)
                break
        i = j + 1
    if total_dist > 0:
        # We missed the last point since we overestimate the arc_length a bit at each step
        logger.debug(
            "Remaining total dist %s for arc length %s", total_dist, arc_length
        )
        idx.append(ngrid - 1)
    new_path = grid[:, idx].T
    if len(path) != len(new_path):
        raise Exception(
            "Number of path points differ after reparametrization, something must have gone wrong. Previous: "
            + str(len(path))
            + ", new: "
            + str(len(new_path))
        )
    return new_path


def change_string_length(stringpath, new_length):
    """
    :param stringpath:
    :param new_length:
    :return: a reparametrized string of that length
    """
    new_length = int(np.rint(new_length))
    old_length = len(stringpath)
    if new_length < 2:
        raise Exception(
            "Not valid new length {} and/or old length {}".format(
                new_length, old_length
            )
        )
    if len(stringpath.shape) == 1:
        ndim = 1
    else:
        ndim = stringpath.shape[1]
    if new_length == old_length:
        return stringpath

    if new_length < old_length:
        orig_new_length = new_length
        reduce_length = True
        # A trick: multiply the number of points with X and then take every X point
        frac = np.ceil(old_length / new_length) + 1
        frac = int(frac)
        new_length = int(
            frac * new_length - 1
        )  # minus one since we want the endpoints to be the same
    else:
        frac = None
        reduce_length = False
    new_path = np.empty((new_length, ndim)).squeeze()
    # prepend additional points at the beginning of the stringpath
    new_path[0 : (new_length - old_length)] = stringpath[0]
    new_path[(new_length - old_length) : new_length] = stringpath
    old_arclengths = compute_arclengths(stringpath)
    # The weight is proportional to the length of the arcs between points on the string
    new_arclength_weight = np.empty((new_length - 1,))
    new_arclength_weight[0 : (new_length - old_length)] = old_arclengths[0]
    # We still want the length of the first arc to be approximately the same
    new_arclength_weight[
        (new_length - old_length) : (new_length - 1)
    ] = old_arclengths
    new_path = reparametrize_path_iter(
        new_path, arclength_weight=new_arclength_weight
    )
    if reduce_length:
        new_path, new_arclength_weight = (
            new_path[::frac],
            new_arclength_weight[::frac],
        )
        new_path[-1] = stringpath[
            -1
        ]  # Just to make sure last point is the same
        if len(new_arclength_weight) >= len(new_path):
            new_arclength_weight = new_arclength_weight[
                0 : orig_new_length - 1
            ]
        new_path = reparametrize_path_iter(
            new_path, arclength_weight=new_arclength_weight
        )
    return new_path


def compute_arclengths(stringpath):
    arclengths = np.empty((len(stringpath) - 1,))
    for i in range(len(stringpath) - 1):
        arclengths[i] = np.linalg.norm(stringpath[i + 1] - stringpath[i])
    return arclengths


def get_straight_path(start, end, number_points=20, height_func=None):
    start, end = np.squeeze(start), np.squeeze(end)
    dim = len(start)
    pts = np.empty((number_points, dim if height_func is None else dim + 1))
    for i in range(0, dim):
        pts[:, i] = np.linspace(start[i], end[i], num=number_points)
    if height_func is not None:
        for row in range(0, number_points):
            pts[row, dim] = height_func(pts[row, 0:dim])
    return pts
