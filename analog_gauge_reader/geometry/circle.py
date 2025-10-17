import numpy as np

# -------------Fit Circle to Points ---------------


def fit_circle(center, start, end):
    """
    Estimate circle params using center point and 2 points on circle

    """
    x0 = center[0]
    y0 = center[1]
    c = np.array(center)
    p1 = np.array(start)
    p2 = np.array(end)
    r1 = np.linalg.norm(start - center)
    r2 = np.linalg.norm(end - center)
    r = r1 + r2 / 2
    return x0, y0, r


def get_circle_pts(params, npts=100, tmin=0, tmax=2 * np.pi):
    """
    Return npts points on the circle described by the params = x0, y0, r
    for values of the parametric variable t between tmin and tmax.

    """

    x0, y0, r = params
    # A grid of the parametric variable, t.
    t = np.linspace(tmin, tmax, npts)
    # x, y are numpy arrays
    x = x0 + r * np.cos(t)
    y = y0 + r * np.sin(t)
    return x, y


# ------------------Project Point To Circle-----------------------------


def get_polar_angle(point, circle_params):
    """Returns angles in range [0, 2*pi)"""
    theta = _get_polar_angle(point, circle_params)
    if theta < 0:
        theta = 2 * np.pi + theta
    return theta


def _get_polar_angle(point, circle_params):
    x0, y0, r = circle_params
    x, y = point

    # find angle
    theta = np.arctan2(y - y0, x - x0)
    return theta


def get_point_from_angle(theta, circle_params):
    x0, y0, r = circle_params
    x = x0 + np.cos(theta) * r
    y = y0 + np.sin(theta) * r

    return x, y


def project_point(point, circle_params):
    theta = _get_polar_angle(point, circle_params)
    return get_point_from_angle(theta, circle_params)


# --------------------Get Circle Error------------------------------


def get_circle_error(points, circle_params):
    mean_dist = 0
    n_points = len(points)
    for point in points:
        proj_point = project_point(point, circle_params)
        distance = np.linalg.norm(proj_point - point)
        mean_dist += distance / n_points
    return mean_dist


# --------------------Intersect Line and Circle------------------------------


def get_line_circle_point(line_coeffs, x, circle_params):
    """
    Most times you have two intersection points.
    Take the intersection point that has the smallest distance to either start
    or end point of the needle
    :param line_coeffs:
    :param x: x coordinates of end and start point of line
    :param circle_params:
    :return: numpy array with x and y coordinate
    """
    intersection_points = find_line_circle_intersection(line_coeffs, x, circle_params)

    n_points = intersection_points.shape[0]
    if n_points == 0:
        return None
    elif n_points == 1:
        return intersection_points[0]
    else:
        # Two points: pick the one closest to the midpoint of the segment
        midpt_x = (x[0] + x[1]) / 2
        midpt_y = (line_coeffs[0] * midpt_x + line_coeffs[1])
        midpoint = np.array([midpt_x, midpt_y])

        # Compute distances to midpoint
        distances = np.linalg.norm(intersection_points - midpoint, axis=1)
        min_idx = np.argmin(distances)

        return intersection_points[min_idx]


def find_line_circle_intersection(line_coeffs, x, circle_params):
    """
    If no point exists return empty array with shape (2,0)
    :param line_coeffs:
    :param x: two points on the line
    :param circle_params:
    :return: np array with x and y vertically stacked
    """

    # (1 + m^2) * x^2 + 2 * (m(c − y0​) − x0​) * x + (x0^2 ​+ (c − y0​)^2 − r^2) = 0
    m, n = line_coeffs
    x0, y0, r = circle_params

    # Quadratic coefficients for x
    a = 1 + m**2
    b = 2 * (m*(n - y0) - x0)
    c = x0**2 + (n - y0)**2 - r**2

    # Solve quadratic
    x_intersect = np.roots([a, b, c])
    y_intersect = m * x_intersect + n

    # Only keep real or almost real solutions (mask == True)
    mask = abs(x_intersect.imag) < 1e-5
    x_intersect = x_intersect[mask].real
    y_intersect = y_intersect[mask].real

    if len(x_intersect) == 0:
        return np.empty((0,2))

    return np.vstack((x_intersect, y_intersect)).T


def find_intersection_points_centered(line_coeffs, circle_params):
    """
    Solve quadratic function
    """
    line = np.poly1d(line_coeffs)

    ap, bp = circle_params[2:4]

    m = line_coeffs[0]
    c = line_coeffs[1]

    a = np.square(ap) * np.square(m) + np.square(bp)
    b = 2 * np.square(ap) * m * c
    c = np.square(ap) * (np.square(c) - np.square(bp))

    x_intersected = np.roots([a, b, c])
    y_intersected = line(x_intersected)

    return np.vstack((x_intersected, y_intersected))


# --------------------Get middle point of two angles------------------------------


def get_theta_middle(theta_1, theta_2):
    """
    Return the point on an circle that is between two other points on an circle.
    """
    candidate_1 = (theta_2 + theta_1) / 2
    if theta_2 + theta_1 > 2 * np.pi:
        candidate_2 = (theta_2 + theta_1 - 2 * np.pi) / 2
    else:
        candidate_2 = (theta_2 + theta_1 + 2 * np.pi) / 2

    distance_1 = min(abs(candidate_1 - theta_1), abs(candidate_1 - theta_2))
    distance_2 = min(abs(candidate_2 - theta_1), abs(candidate_2 - theta_2))

    if distance_1 < distance_2:
        return candidate_1

    return candidate_2
