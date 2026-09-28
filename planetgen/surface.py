"""Surface and cloud color generation."""

import math
from dataclasses import dataclass

import numpy as np

from .noise import _build_perm_table, fbm_noise_3d, ridged_noise_3d
from .types import COLOR_RAMPS, GAS_GIANT_PALETTES, PLANET_TYPES
from .util import color_ramp_lookup, smoothstep


@dataclass
class Surface:
    """Material of every visible planet pixel (1D arrays over the mask)."""
    color: np.ndarray     # (N, 3) albedo, 0..255
    height: np.ndarray    # (N,) terrain height, liquids flattened to sea level
    specular: np.ndarray  # (N,) glossiness, 0..1
    liquid: np.ndarray    # (N,) bool, True for seas (water, lava, acid)


def generate_surface(geo, planet_type, seed):
    """Generate the surface material for all masked pixels."""
    px, py, pz = geo["px"], geo["py"], geo["pz"]
    perm = _build_perm_table(seed)
    traits = PLANET_TYPES[planet_type]
    land_specular = traits.get("land_specular", 0.04)

    if planet_type == "gas_giant":
        color = np.stack(_generate_gas_giant_surface(geo, seed, perm), axis=-1)
        n = len(color)
        return Surface(color, np.zeros(n), np.full(n, land_specular), np.zeros(n, dtype=bool))

    rng = np.random.RandomState((seed + 7777) & 0x7FFFFFFF)
    offset = rng.uniform(-1000, 1000, 3)
    height = terrain_height(px, py, pz, seed, offset, traits.get("terrain", "rolling"))

    # ── Color ramp lookup ────────────────────────────────────────────────
    ramp = COLOR_RAMPS.get(planet_type)
    if ramp is None:
        ramp = COLOR_RAMPS["barren"]

    r, g, b = color_ramp_lookup(height, ramp)

    # Add subtle noise variation to break contour uniformity
    offx, offy, offz = offset
    var_perm = _build_perm_table(seed + 300)
    variation = fbm_noise_3d(px * 15 + offx, py * 15 + offy, pz * 15 + offz,
                              var_perm, octaves=3) * 12.0
    r = np.clip(r + variation, 0, 255)
    g = np.clip(g + variation * 0.8, 0, 255)
    b = np.clip(b + variation * 0.6, 0, 255)
    color = np.stack([r, g, b], axis=-1)

    sea_level = traits.get("sea_level")
    if sea_level is None:
        liquid = np.zeros(len(height), dtype=bool)
    else:
        liquid = height < sea_level
        height = np.maximum(height, sea_level)
    specular = np.where(liquid, 0.8, land_specular)

    return Surface(color, height, specular, liquid)


def _noise(kind, px, py, pz, scale, offset, seed, **kwargs):
    """Sample fbm or ridged noise on the unit sphere at a given scale."""
    fn = ridged_noise_3d if kind == "ridged" else fbm_noise_3d
    ox, oy, oz = offset
    return fn(px * scale + ox, py * scale + oy, pz * scale + oz, _build_perm_table(seed), **kwargs)


def terrain_height(px, py, pz, seed, offset, style):
    """Terrain height, roughly -1..1, with 0 near sea level for the ramps.

    Styles:
      continents  big land masses with mountain chains inland
      rolling     hills and basins everywhere, no clear continents
      cracked     crust broken by deep channels (lava or acid fills them)
    """
    # A gentle warp keeps coastlines and ridges from looking grid-aligned.
    warp = 0.18
    wx = _noise("fbm", px, py, pz, 1.7, offset, seed + 1000, octaves=3) * warp
    wy = _noise("fbm", px, py, pz, 1.7, offset + 50, seed + 1000, octaves=3) * warp
    wz = _noise("fbm", px, py, pz, 1.7, offset + 100, seed + 1000, octaves=3) * warp
    qx, qy, qz = px + wx, py + wy, pz + wz

    detail = _noise("fbm", qx, qy, qz, 7.0, offset, seed + 200, octaves=6, persistence=0.5)

    if style == "continents":
        land = _noise("fbm", qx, qy, qz, 1.4, offset, seed, octaves=5, persistence=0.55) * 1.6
        ridges = _noise("ridged", qx, qy, qz, 3.2, offset * 0.5, seed + 100, octaves=6)
        inland = smoothstep(0.02, 0.35, land)
        return land + detail * 0.22 + ridges * inland * 0.4

    if style == "cracked":
        crust = _noise("fbm", qx, qy, qz, 2.2, offset, seed, octaves=5) * 0.7
        cracks = _noise("ridged", qx, qy, qz, 3.0, offset * 0.5, seed + 100, octaves=5)
        # Push the crust up and cut channels where the ridged noise peaks.
        return 0.4 + crust + detail * 0.2 - np.power(cracks, 3.0) * 1.3

    hills = _noise("fbm", qx, qy, qz, 2.2, offset, seed, octaves=6, persistence=0.52)
    ridges = _noise("ridged", qx, qy, qz, 2.8, offset * 0.5, seed + 100, octaves=5)
    return hills * 1.1 + (ridges - 0.6) * 0.4 + detail * 0.2


def _generate_gas_giant_surface(geo, seed, perm):
    """Generate gas giant surface with latitude-based banding."""
    px, py, pz = geo["px"], geo["py"], geo["pz"]

    rng = np.random.RandomState((seed + 5555) & 0x7FFFFFFF)
    palette_idx = rng.randint(0, len(GAS_GIANT_PALETTES))
    palette = GAS_GIANT_PALETTES[palette_idx]
    num_bands = rng.randint(8, 16)
    offx, offy, offz = rng.uniform(-1000, 1000, 3)

    # Perturb latitude with 3D noise for wavy bands
    warp_perm = _build_perm_table(seed + 2000)
    lat_warp = fbm_noise_3d(px * 3.0 + offx, py * 1.5 + offy, pz * 3.0 + offz,
                             warp_perm, octaves=4, persistence=0.5) * 0.12

    lat = py + lat_warp  # latitude from -1 to +1

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
    turbulence = fbm_noise_3d(px * 8.0 + offx, py * 4.0 + offy, pz * 8.0 + offz,
                               turb_perm, octaves=5, persistence=0.55) * 25.0
    r = np.clip(r + turbulence, 0, 255)
    g = np.clip(g + turbulence * 0.8, 0, 255)
    b = np.clip(b + turbulence * 0.5, 0, 255)

    return r, g, b


# ── Cloud layer ──────────────────────────────────────────────────────────────

def generate_clouds(geo, seed, diffuse):
    """Generate cloud layer. Returns cloud_alpha as a 1D array in [0, 1]."""
    px, py, pz = geo["px"], geo["py"], geo["pz"]

    rng = np.random.RandomState((seed + 8888) & 0x7FFFFFFF)
    offx, offy, offz = rng.uniform(-500, 500, 3)

    cloud_perm = _build_perm_table(seed + 500)

    # Domain warp for clouds
    warp_perm = _build_perm_table(seed + 2500)
    cw = fbm_noise_3d(px * 3.0 + offx, py * 3.0 + offy, pz * 3.0 + offz,
                       warp_perm, octaves=2) * 0.3

    cloud_noise = fbm_noise_3d((px + cw) * 5.0 + offx, (py + cw) * 5.0 + offy, (pz + cw) * 5.0 + offz,
                                cloud_perm, octaves=5, persistence=0.55, lacunarity=2.2)

    cloud_alpha = smoothstep(0.1, 0.5, cloud_noise)

    # Clouds are lit by the same light
    cloud_alpha *= np.clip(diffuse * 1.5, 0.2, 1.0)

    return cloud_alpha
