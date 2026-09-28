"""Surface and cloud color generation."""

import math

import numpy as np

from .noise import _build_perm_table, fbm_noise_3d
from .types import COLOR_RAMPS, GAS_GIANT_PALETTES
from .util import color_ramp_lookup, smoothstep


def generate_surface(geo, planet_type, seed):
    """Generate the surface color array for all masked pixels.

    Returns (r, g, b) as 1D float64 arrays in [0, 255].
    """
    nx, ny, nz = geo["nx"], geo["ny"], geo["nz"]
    perm = _build_perm_table(seed)

    if planet_type == "gas_giant":
        return _generate_gas_giant_surface(geo, seed, perm)

    # ── Domain warping ───────────────────────────────────────────────────
    rng = np.random.RandomState((seed + 7777) & 0x7FFFFFFF)
    offx, offy, offz = rng.uniform(-1000, 1000, 3)

    warp_perm = _build_perm_table(seed + 1000)
    warp_scale = 2.5
    warp_mag = 0.4

    wx = fbm_noise_3d(nx * warp_scale + offx, ny * warp_scale + offy, nz * warp_scale + offz,
                       warp_perm, octaves=3) * warp_mag
    wy = fbm_noise_3d(nx * warp_scale + offx + 50, ny * warp_scale + offy + 50, nz * warp_scale + offz + 50,
                       warp_perm, octaves=3) * warp_mag
    wz = fbm_noise_3d(nx * warp_scale + offx + 100, ny * warp_scale + offy + 100, nz * warp_scale + offz + 100,
                       warp_perm, octaves=3) * warp_mag

    wnx = nx + wx
    wny = ny + wy
    wnz = nz + wz

    # ── Multi-scale terrain noise ────────────────────────────────────────
    scale1 = 4.0
    height = fbm_noise_3d(wnx * scale1 + offx, wny * scale1 + offy, wnz * scale1 + offz,
                           perm, octaves=7, persistence=0.5, lacunarity=2.0)

    mid_perm = _build_perm_table(seed + 100)
    scale2 = 10.0
    mid = fbm_noise_3d(wnx * scale2 + offx * 0.5, wny * scale2 + offy * 0.5, wnz * scale2 + offz * 0.5,
                        mid_perm, octaves=5, persistence=0.55, lacunarity=2.2) * 0.35

    fine_perm = _build_perm_table(seed + 200)
    scale3 = 18.0
    fine = fbm_noise_3d(wnx * scale3 + offx * 0.25, wny * scale3 + offy * 0.25, wnz * scale3 + offz * 0.25,
                         fine_perm, octaves=4, persistence=0.6, lacunarity=2.4) * 0.15

    height = height + mid + fine

    # ── Color ramp lookup ────────────────────────────────────────────────
    ramp = COLOR_RAMPS.get(planet_type)
    if ramp is None:
        ramp = COLOR_RAMPS["barren"]

    r, g, b = color_ramp_lookup(height, ramp)

    # Add subtle noise variation to break contour uniformity
    var_perm = _build_perm_table(seed + 300)
    variation = fbm_noise_3d(nx * 15 + offx, ny * 15 + offy, nz * 15 + offz,
                              var_perm, octaves=3) * 12.0
    r = np.clip(r + variation, 0, 255)
    g = np.clip(g + variation * 0.8, 0, 255)
    b = np.clip(b + variation * 0.6, 0, 255)

    return r, g, b


def _generate_gas_giant_surface(geo, seed, perm):
    """Generate gas giant surface with latitude-based banding."""
    nx, ny, nz = geo["nx"], geo["ny"], geo["nz"]

    rng = np.random.RandomState((seed + 5555) & 0x7FFFFFFF)
    palette_idx = rng.randint(0, len(GAS_GIANT_PALETTES))
    palette = GAS_GIANT_PALETTES[palette_idx]
    num_bands = rng.randint(8, 16)
    offx, offy, offz = rng.uniform(-1000, 1000, 3)

    # Perturb latitude with 3D noise for wavy bands
    warp_perm = _build_perm_table(seed + 2000)
    lat_warp = fbm_noise_3d(nx * 3.0 + offx, ny * 1.5 + offy, nz * 3.0 + offz,
                             warp_perm, octaves=4, persistence=0.5) * 0.12

    lat = ny + lat_warp  # latitude from -1 to +1

    # Band profile: sinusoidal banding
    band_val = np.sin(lat * num_bands * math.pi)
    # Normalize to 0-1
    band_t = band_val * 0.5 + 0.5

    # Map band_t to palette colors via interpolation
    n_colors = len(palette)
    color_positions = np.linspace(0, 1, n_colors)
    r_vals = np.array([c[0] for c in palette], dtype=np.float64)
    g_vals = np.array([c[1] for c in palette], dtype=np.float64)
    b_vals = np.array([c[2] for c in palette], dtype=np.float64)

    r = np.interp(band_t, color_positions, r_vals)
    g = np.interp(band_t, color_positions, g_vals)
    b = np.interp(band_t, color_positions, b_vals)

    # Add turbulence/storm detail
    turb_perm = _build_perm_table(seed + 3000)
    turbulence = fbm_noise_3d(nx * 8.0 + offx, ny * 4.0 + offy, nz * 8.0 + offz,
                               turb_perm, octaves=5, persistence=0.55) * 25.0
    r = np.clip(r + turbulence, 0, 255)
    g = np.clip(g + turbulence * 0.8, 0, 255)
    b = np.clip(b + turbulence * 0.5, 0, 255)

    return r, g, b


# ── Cloud layer ──────────────────────────────────────────────────────────────

def generate_clouds(geo, seed, diffuse):
    """Generate cloud layer. Returns cloud_alpha as a 1D array in [0, 1]."""
    nx, ny, nz = geo["nx"], geo["ny"], geo["nz"]

    rng = np.random.RandomState((seed + 8888) & 0x7FFFFFFF)
    offx, offy, offz = rng.uniform(-500, 500, 3)

    cloud_perm = _build_perm_table(seed + 500)

    # Domain warp for clouds
    warp_perm = _build_perm_table(seed + 2500)
    cw = fbm_noise_3d(nx * 3.0 + offx, ny * 3.0 + offy, nz * 3.0 + offz,
                       warp_perm, octaves=2) * 0.3

    cloud_noise = fbm_noise_3d((nx + cw) * 5.0 + offx, (ny + cw) * 5.0 + offy, (nz + cw) * 5.0 + offz,
                                cloud_perm, octaves=5, persistence=0.55, lacunarity=2.2)

    cloud_alpha = smoothstep(0.1, 0.5, cloud_noise)

    # Clouds are lit by the same light
    cloud_alpha *= np.clip(diffuse * 1.5, 0.2, 1.0)

    return cloud_alpha
