"""Planetary ring system."""

import numpy as np

from .noise import _build_perm_table, perlin_noise_3d
from .util import smoothstep


RING_STYLES = [
    # Saturn-like warm tans/browns
    [(210, 190, 160), (190, 165, 130), (230, 210, 175), (170, 145, 110), (220, 200, 170)],
    # Icy blue-white
    [(200, 210, 230), (220, 225, 240), (180, 195, 220), (230, 235, 245), (195, 205, 225)],
    # Rocky gray/brown
    [(180, 170, 160), (160, 150, 140), (200, 190, 175), (145, 135, 125), (190, 180, 170)],
    # Reddish-brown
    [(200, 160, 130), (180, 140, 110), (220, 180, 150), (165, 130, 100), (210, 170, 140)],
]


def ring_plane_hits(size, planet_radius, pole):
    """Intersect every pixel's view ray with the ring plane.

    pole is the planet's rotation axis in image space (x right, y down,
    z toward the viewer). Returns (dist, depth): the distance of the hit
    from the planet center and its z coordinate, both in planet radii.
    """
    cx = cy = size / 2.0
    yy, xx = np.mgrid[0:size, 0:size]
    u = (xx + 0.5 - cx) / planet_radius
    v = (yy + 0.5 - cy) / planet_radius

    ax, ay, az = pole
    # Exactly edge-on rings would divide by zero; nudge them to a sliver.
    if abs(az) < 0.02:
        az = 0.02 if az >= 0 else -0.02
    # The ring plane passes through the planet center with the pole as its
    # normal: ax*u + ay*v + az*z = 0.
    depth = -(ax * u + ay * v) / az
    dist = np.sqrt(u * u + v * v + depth * depth)
    return dist, depth


def render_rings(size, planet_radius, seed, pole, inner, outer):
    """Render the ring system as two RGBA layers: (back_rings, front_rings).

    inner and outer are the ring edges in planet radii. The back layer goes
    under the planet, the front layer over it.
    Returns (None, None) if no ring pixel lands in the image.
    """
    rng = np.random.RandomState((seed + 4444) & 0x7FFFFFFF)

    ring_colors = []
    for base in RING_STYLES[rng.randint(0, len(RING_STYLES))]:
        offset = rng.randint(-20, 21, 3)
        ring_colors.append(np.clip(np.array(base) + offset, 0, 255))
    ring_colors = np.array(ring_colors, dtype=np.float64)

    num_gaps = rng.randint(1, 3)
    gap_centers = rng.uniform(0.2, 0.8, num_gaps)
    gap_widths = rng.uniform(0.02, 0.06, num_gaps)

    ring_perm = _build_perm_table(seed + 6000)

    dist, depth = ring_plane_hits(size, planet_radius, pole)
    ring_mask = (dist >= inner) & (dist <= outer)
    if not np.any(ring_mask):
        return None, None

    # Position across the ring band, 0 at the inner edge and 1 at the outer
    t = (dist[ring_mask] - inner) / (outer - inner)

    edge_fade = smoothstep(0.0, 0.08, t) * smoothstep(1.0, 0.92, t)

    gap_factor = np.ones_like(t)
    for gc, gw in zip(gap_centers, gap_widths):
        gap_factor *= 1.0 - np.exp(-0.5 * ((t - gc) / gw) ** 2)

    fine = perlin_noise_3d(t * 25.0, np.zeros_like(t) + seed * 0.01, np.zeros_like(t), ring_perm)
    fine_factor = 0.7 + 0.3 * (fine * 0.5 + 0.5)

    opacity = edge_fade * gap_factor * fine_factor
    alpha = np.clip(opacity * 200, 0, 255).astype(np.uint8)

    color_pos = np.linspace(0, 1, len(ring_colors))
    ring_rgba = np.zeros((size, size, 4), dtype=np.uint8)
    for ch in range(3):
        ring_rgba[ring_mask, ch] = np.interp(t, color_pos, ring_colors[:, ch]).astype(np.uint8)
    ring_rgba[ring_mask, 3] = alpha

    # The ring never passes through the planet (inner > 1), so everything on
    # the viewer's side of the center plane is in front of the planet.
    in_front = depth > 0
    back_rgba = ring_rgba.copy()
    back_rgba[in_front, 3] = 0
    front_rgba = ring_rgba
    front_rgba[~in_front, 3] = 0

    return back_rgba, front_rgba
