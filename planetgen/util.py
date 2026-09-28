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
