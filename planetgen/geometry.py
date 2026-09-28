"""Sphere geometry shared by the render passes."""

import math

import numpy as np


def orientation_matrix(tilt, inclination, rotation):
    """Rotation from the planet's body frame into view space, both y-up.

    In the body frame the north pole is +y. rotation spins the planet about
    its own axis, inclination tips the north pole toward the viewer and
    tilt turns the axis counterclockwise in the image. All in degrees.
    """
    t, i, r = (math.radians(a) for a in (tilt, inclination, rotation))
    spin = np.array([[math.cos(r), 0, math.sin(r)], [0, 1, 0], [-math.sin(r), 0, math.cos(r)]])
    tip = np.array([[1, 0, 0], [0, math.cos(i), -math.sin(i)], [0, math.sin(i), math.cos(i)]])
    roll = np.array([[math.cos(t), -math.sin(t), 0], [math.sin(t), math.cos(t), 0], [0, 0, 1]])
    return roll @ tip @ spin


def build_sphere_geometry(size, radius, orientation=None):
    """Precompute sphere geometry for vectorized operations.

    Returns dict with:
      mask    - (size, size) bool array, True where the planet covers any
                part of the pixel
      coverage - 1D array, how much of each masked pixel the disc covers
                 (1 inside, fading to 0 across the edge for anti-aliasing)
      nx, ny, nz - 1D arrays of surface normals for masked pixels
                   (x right, y down, z toward the viewer)
      px, py, pz - 1D arrays, the same points in the planet's own frame
                   (py is latitude, +1 at the north pole); surface
                   features are sampled here so they turn with the planet
      pole       - the north pole direction in image space
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

    if orientation is None:
        orientation = np.eye(3)
    # View space is y-down, the body frame is y-up: flip y on the way in
    # and out. Body = orientation^T @ view.
    view_up = np.stack([nx, -ny, nz])
    px, py, pz = orientation.T @ view_up
    pole = (orientation[0, 1], -orientation[1, 1], orientation[2, 1])

    return {
        "mask": mask,
        "coverage": coverage,
        "nx": nx,
        "ny": ny,
        "nz": nz,
        "px": px,
        "py": py,
        "pz": pz,
        "pole": pole,
        "dx": dx,
        "dy": dy,
        "ndx": ndx,
        "ndy": ndy,
        "dist_sq": dist_sq,
    }
