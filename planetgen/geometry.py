"""Sphere geometry shared by the render passes."""

import numpy as np


def build_sphere_geometry(size, radius):
    """Precompute sphere geometry for vectorized operations.

    Returns dict with:
      mask    - (size, size) bool array, True inside sphere
      nx, ny, nz - 1D arrays of surface normals for masked pixels
      dx, dy     - 2D arrays of displacement from center (in pixels)
      dist_sq    - 2D array of squared distance from center (normalized by radius)
    """
    cx = cy = size / 2.0
    yy, xx = np.mgrid[0:size, 0:size]
    dx = (xx - cx).astype(np.float64)
    dy = (yy - cy).astype(np.float64)

    # Normalized by radius
    ndx = dx / radius
    ndy = dy / radius
    dist_sq = ndx * ndx + ndy * ndy

    mask = dist_sq <= 1.0

    nx = ndx[mask]
    ny = ndy[mask]
    nz = np.sqrt(np.clip(1.0 - (nx * nx + ny * ny), 0.0, 1.0))

    return {
        "mask": mask,
        "nx": nx,
        "ny": ny,
        "nz": nz,
        "dx": dx,
        "dy": dy,
        "ndx": ndx,
        "ndy": ndy,
        "dist_sq": dist_sq,
    }
