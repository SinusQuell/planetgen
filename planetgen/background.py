"""Backgrounds behind the planet."""

import numpy as np
from PIL import Image, ImageFilter

from .noise import _build_perm_table, fbm_noise_3d

BACKGROUNDS = ["transparent", "black", "stars", "nebula"]

# Star tints from cool red through white to hot blue
STAR_COLORS = np.array([
    (255, 190, 150), (255, 220, 190), (255, 244, 232),
    (255, 255, 255), (220, 232, 255), (180, 204, 255),
])

NEBULA_PALETTES = [
    [(60, 20, 90), (20, 60, 120)],
    [(110, 30, 60), (40, 20, 90)],
    [(20, 80, 90), (30, 40, 110)],
    [(120, 60, 20), (70, 20, 60)],
]


def render_background(size, seed, style):
    """Background as an RGBA image, or None for a transparent one."""
    if style == "transparent":
        return None
    if style not in BACKGROUNDS:
        raise ValueError(f"unknown background {style!r}, pick one of {', '.join(BACKGROUNDS)}")

    canvas = np.zeros((size, size, 3))
    canvas[:] = (4, 5, 10)
    if style == "black":
        return _to_image(canvas)

    rng = np.random.RandomState((seed + 2024) & 0x7FFFFFFF)
    if style == "nebula":
        canvas += _nebula(size, seed, rng)
    canvas = _add_stars(canvas, size, rng)
    return _to_image(canvas)


def _nebula(size, seed, rng):
    """Faint colored gas clouds."""
    yy, xx = np.mgrid[0:size, 0:size] / size
    ox, oy = rng.uniform(-500, 500, 2)
    zeros = np.zeros_like(xx)
    perm = _build_perm_table(seed + 4040)
    warp = fbm_noise_3d(xx * 2.0 + ox, yy * 2.0 + oy, zeros + 3.0, perm, octaves=3)
    gas = fbm_noise_3d(xx * 3.0 + warp + ox, yy * 3.0 + warp + oy, zeros, perm, octaves=6)
    mix = fbm_noise_3d(xx * 1.5 + oy, yy * 1.5 + ox, zeros + 7.0, perm, octaves=2) * 0.5 + 0.5
    density = np.clip(gas * 1.6 + 0.15, 0.0, 1.0) ** 1.5

    first, second = (np.array(c, dtype=np.float64) for c in
                     NEBULA_PALETTES[rng.randint(len(NEBULA_PALETTES))])
    color = first * mix[..., None] + second * (1.0 - mix[..., None])
    return color * density[..., None] * 0.8


def _add_stars(canvas, size, rng):
    count = int(size * size / 350)
    xs = rng.uniform(0, size, count)
    ys = rng.uniform(0, size, count)
    # Many faint stars, few bright ones
    brightness = np.clip(rng.pareto(2.2, count) * 0.25 + 0.1, 0.0, 1.5)
    colors = STAR_COLORS[rng.randint(len(STAR_COLORS), size=count)]

    stars = np.zeros_like(canvas)
    ix = xs.astype(int)
    iy = ys.astype(int)
    np.add.at(stars, (iy, ix), colors * np.minimum(brightness, 1.0)[:, None])

    # The brightest stars get a soft halo.
    bright = brightness > 0.8
    halo = np.zeros_like(canvas)
    np.add.at(halo, (iy[bright], ix[bright]), colors[bright] * brightness[bright, None] * 4)
    halo_img = Image.fromarray(np.clip(halo, 0, 255).astype(np.uint8))
    halo = np.asarray(halo_img.filter(ImageFilter.GaussianBlur(max(1.0, size / 500))),
                      dtype=np.float64)

    return canvas + stars + halo


def _to_image(rgb):
    rgba = np.empty(rgb.shape[:2] + (4,), dtype=np.uint8)
    rgba[..., :3] = np.clip(rgb, 0, 255).astype(np.uint8)
    rgba[..., 3] = 255
    return Image.fromarray(rgba, "RGBA")
