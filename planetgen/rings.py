"""Planetary ring system."""

import numpy as np

from .noise import _build_perm_table, perlin_noise_3d
from .util import smoothstep


def render_rings(size, planet_radius, seed):
    """Render ring system as two RGBA layers: (back_rings, front_rings).

    Returns (back_rgba, front_rgba) as numpy arrays, or (None, None) if no rings.
    """
    rng = np.random.RandomState((seed + 4444) & 0x7FFFFFFF)

    # Tilt: how much the ring plane is inclined toward the viewer.
    # y_scale < 1 compresses the vertical axis to create the elliptical perspective.
    # Values 0.2-0.45 give a nice diagonal view (not too edge-on, not too top-down).
    y_scale = rng.uniform(0.2, 0.45)

    inner_r = planet_radius * rng.uniform(1.3, 1.5)
    outer_r = planet_radius * rng.uniform(1.9, 2.4)

    # Ring color palette - pick a base style then add variation
    style = rng.randint(0, 4)
    ring_colors = []
    if style == 0:
        # Saturn-like warm tans/browns
        bases = [(210, 190, 160), (190, 165, 130), (230, 210, 175), (170, 145, 110), (220, 200, 170)]
    elif style == 1:
        # Icy blue-white rings
        bases = [(200, 210, 230), (220, 225, 240), (180, 195, 220), (230, 235, 245), (195, 205, 225)]
    elif style == 2:
        # Rocky gray/brown
        bases = [(180, 170, 160), (160, 150, 140), (200, 190, 175), (145, 135, 125), (190, 180, 170)]
    else:
        # Reddish-brown
        bases = [(200, 160, 130), (180, 140, 110), (220, 180, 150), (165, 130, 100), (210, 170, 140)]
    for base in bases:
        r_off, g_off, b_off = rng.randint(-20, 21, 3)
        ring_colors.append((
            int(np.clip(base[0] + r_off, 0, 255)),
            int(np.clip(base[1] + g_off, 0, 255)),
            int(np.clip(base[2] + b_off, 0, 255)),
        ))

    # Gap positions (1-2 gaps)
    num_gaps = rng.randint(1, 3)
    gap_centers = rng.uniform(0.2, 0.8, num_gaps)
    gap_widths = rng.uniform(0.02, 0.06, num_gaps)

    # Build noise permutation for fine structure
    ring_perm = _build_perm_table(seed + 6000)

    cx = cy = size / 2.0
    yy, xx = np.mgrid[0:size, 0:size]
    dx = (xx - cx).astype(np.float64)
    dy = (yy - cy).astype(np.float64)

    # Ring-plane distance: scale dy to flatten the ring into an ellipse
    ring_r = np.sqrt(dx * dx + (dy / y_scale) ** 2)

    # Which pixels are in the ring annulus
    ring_mask = (ring_r >= inner_r) & (ring_r <= outer_r)

    if not np.any(ring_mask):
        return None, None

    # Normalized ring position [0, 1]
    t = (ring_r[ring_mask] - inner_r) / (outer_r - inner_r)

    # ── Opacity profile ──────────────────────────────────────────────────
    # Smooth edges
    edge_fade = smoothstep(0.0, 0.08, t) * smoothstep(1.0, 0.92, t)

    # Gaps
    gap_factor = np.ones_like(t)
    for gc, gw in zip(gap_centers, gap_widths):
        gap_factor *= 1.0 - np.exp(-0.5 * ((t - gc) / gw) ** 2)

    # Fine structure noise (1D-ish, based on t)
    fine = perlin_noise_3d(t * 25.0, np.zeros_like(t) + seed * 0.01, np.zeros_like(t), ring_perm)
    fine_factor = 0.7 + 0.3 * (fine * 0.5 + 0.5)

    opacity = edge_fade * gap_factor * fine_factor
    alpha = np.clip(opacity * 200, 0, 255).astype(np.uint8)

    # ── Ring colors ──────────────────────────────────────────────────────
    color_pos = np.linspace(0, 1, len(ring_colors))
    rc_r = np.array([c[0] for c in ring_colors], dtype=np.float64)
    rc_g = np.array([c[1] for c in ring_colors], dtype=np.float64)
    rc_b = np.array([c[2] for c in ring_colors], dtype=np.float64)

    ring_r_ch = np.interp(t, color_pos, rc_r).astype(np.uint8)
    ring_g_ch = np.interp(t, color_pos, rc_g).astype(np.uint8)
    ring_b_ch = np.interp(t, color_pos, rc_b).astype(np.uint8)

    # Build full RGBA ring image
    ring_rgba = np.zeros((size, size, 4), dtype=np.uint8)
    ring_rgba[ring_mask, 0] = ring_r_ch
    ring_rgba[ring_mask, 1] = ring_g_ch
    ring_rgba[ring_mask, 2] = ring_b_ch
    ring_rgba[ring_mask, 3] = alpha

    # Split into back (top half) and front (bottom half)
    center_row = int(cy)
    back_rgba = ring_rgba.copy()
    back_rgba[center_row:, :, 3] = 0  # Remove bottom half

    front_rgba = ring_rgba.copy()
    front_rgba[:center_row, :, 3] = 0  # Remove top half

    # Also remove ring pixels that are behind the planet disc (for back rings)
    planet_mask_sq = (dx * dx + dy * dy) <= (planet_radius * planet_radius)
    back_rgba[planet_mask_sq, 3] = 0

    return back_rgba, front_rgba
