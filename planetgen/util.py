"""Small numeric helpers."""

import numpy as np


def smoothstep(edge0, edge1, x):
    """Hermite interpolation between edge0 and edge1."""
    t = np.clip((x - edge0) / (edge1 - edge0 + 1e-10), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def color_ramp_lookup(height, ramp):
    """Interpolate through a color ramp. height is a 1D array, ramp is a list of (threshold, (r,g,b))."""
    thresholds = np.array([s[0] for s in ramp])
    r_vals = np.array([s[1][0] for s in ramp], dtype=np.float64)
    g_vals = np.array([s[1][1] for s in ramp], dtype=np.float64)
    b_vals = np.array([s[1][2] for s in ramp], dtype=np.float64)

    r = np.interp(height, thresholds, r_vals)
    g = np.interp(height, thresholds, g_vals)
    b = np.interp(height, thresholds, b_vals)

    return r, g, b


def shift_hue(rgb, degrees, saturation=1.0):
    """Rotate the hue of (N, 3) colors and scale their saturation, keeping
    brightness. Works in YIQ space, where hue is an angle in the IQ plane."""
    if degrees == 0 and saturation == 1.0:
        return rgb
    to_yiq = np.array([[0.299, 0.587, 0.114],
                       [0.596, -0.274, -0.322],
                       [0.211, -0.523, 0.312]])
    angle = np.radians(degrees)
    c, s = np.cos(angle) * saturation, np.sin(angle) * saturation
    rotate = np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
    matrix = np.linalg.inv(to_yiq) @ rotate @ to_yiq
    return np.clip(rgb @ matrix.T, 0, 255)
