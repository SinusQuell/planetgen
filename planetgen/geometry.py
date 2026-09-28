"""Sphere geometry shared by the render passes."""

import numpy as np


def build_sphere_geometry(size, radius):
    """Precompute sphere geometry for vectorized operations.

    Returns dict with:
      mask    - (size, size) bool array, True where the planet covers any
                part of the pixel
      coverage - 1D array, how much of each masked pixel the disc covers
                 (1 inside, fading to 0 across the edge for anti-aliasing)
      nx, ny, nz - 1D arrays of surface normals for masked pixels
                   (x right, y down, z toward the viewer)
      dx, dy     - 2D arrays of displacement from center (in pixels)
      dist_sq    - 2D array of squared distance from center (normalized by radius)
    """
    cx = cy = size / 2.0
    yy, xx = np.mgrid[0:size, 0:size]
    # Sample at pixel centers so the disc is symmetric around the image center.
    dx = (xx + 0.5 - cx).astype(np.float64)
    dy = (yy + 0.5 - cy).astype(np.float64)

    # Normalized by radius
    ndx = dx / radius
    ndy = dy / radius
    dist_sq = ndx * ndx + ndy * ndy

    dist_px = np.sqrt(dist_sq) * radius
    mask = dist_px < radius + 0.5
    coverage = np.clip(radius + 0.5 - dist_px[mask], 0.0, 1.0)

    # Edge pixels sit slightly outside the unit disc; pull them back onto the
    # rim so their normals stay valid.
    rim = np.maximum(np.sqrt(dist_sq[mask]), 1.0)
    nx = ndx[mask] / rim
    ny = ndy[mask] / rim
    nz = np.sqrt(np.clip(1.0 - (nx * nx + ny * ny), 0.0, 1.0))

    return {
        "mask": mask,
        "coverage": coverage,
        "nx": nx,
        "ny": ny,
        "nz": nz,
        "dx": dx,
        "dy": dy,
        "ndx": ndx,
        "ndy": ndy,
        "dist_sq": dist_sq,
    }
