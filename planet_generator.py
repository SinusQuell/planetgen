#!/usr/bin/env python3
"""
Random Planet Generator
Generates procedural planet images with metadata
"""

import random
import math
import json
import os
import platform
import subprocess
import numpy as np
from PIL import Image


# ── Planet type definitions ──────────────────────────────────────────────────

PLANET_TYPES = {
    "lava": {
        "base_color": (255, 80, 0),
        "temperature": (1000, 2000),
        "atmosphere": "thin",
        "atmo_color": (255, 100, 20),
        "atmo_strength": 0.3,
    },
    "barren": {
        "base_color": (180, 140, 100),
        "temperature": (100, 400),
        "atmosphere": "none",
        "atmo_color": (0, 0, 0),
        "atmo_strength": 0.0,
    },
    "ice": {
        "base_color": (200, 240, 255),
        "temperature": (-200, 0),
        "atmosphere": "thin",
        "atmo_color": (180, 210, 255),
        "atmo_strength": 0.3,
    },
    "ocean": {
        "base_color": (0, 80, 200),
        "temperature": (0, 100),
        "atmosphere": "thick",
        "atmo_color": (100, 150, 255),
        "atmo_strength": 0.5,
    },
    "forest": {
        "base_color": (50, 150, 60),
        "temperature": (0, 30),
        "atmosphere": "oxygen-rich",
        "atmo_color": (100, 160, 255),
        "atmo_strength": 0.45,
    },
    "desert": {
        "base_color": (230, 200, 100),
        "temperature": (40, 60),
        "atmosphere": "thin",
        "atmo_color": (220, 180, 120),
        "atmo_strength": 0.25,
    },
    "gas_giant": {
        "base_color": (255, 180, 100),
        "temperature": (-100, 400),
        "atmosphere": "dense",
        "atmo_color": (200, 160, 100),
        "atmo_strength": 0.5,
    },
    "toxic": {
        "base_color": (100, 255, 100),
        "temperature": (100, 600),
        "atmosphere": "poisonous",
        "atmo_color": (120, 220, 80),
        "atmo_strength": 0.4,
    },
    "crystal": {
        "base_color": (180, 255, 255),
        "temperature": (-50, 100),
        "atmosphere": "thin",
        "atmo_color": (160, 230, 255),
        "atmo_strength": 0.3,
    },
    "volcanic": {
        "base_color": (255, 50, 50),
        "temperature": (800, 1500),
        "atmosphere": "sulfurous",
        "atmo_color": (200, 80, 20),
        "atmo_strength": 0.35,
    },
}

# Color ramps: list of (height_threshold, (r, g, b)) for smooth interpolation
COLOR_RAMPS = {
    "ocean": [
        (-1.0, (0, 25, 80)),
        (-0.25, (0, 40, 120)),
        (-0.08, (0, 80, 180)),
        (-0.02, (30, 120, 200)),
        (0.0, (210, 195, 140)),
        (0.05, (80, 150, 60)),
        (0.25, (60, 130, 50)),
        (0.45, (150, 145, 135)),
        (0.7, (200, 200, 200)),
        (1.0, (250, 250, 255)),
    ],
    "forest": [
        (-1.0, (20, 50, 120)),
        (-0.15, (30, 80, 150)),
        (-0.05, (35, 90, 60)),
        (0.0, (40, 100, 50)),
        (0.15, (50, 140, 55)),
        (0.30, (70, 160, 60)),
        (0.45, (90, 130, 70)),
        (0.6, (130, 120, 100)),
        (1.0, (180, 175, 170)),
    ],
    "lava": [
        (-1.0, (255, 120, 0)),
        (-0.15, (255, 90, 0)),
        (-0.05, (220, 50, 0)),
        (0.05, (180, 40, 0)),
        (0.2, (100, 25, 0)),
        (0.5, (40, 15, 5)),
        (1.0, (20, 8, 2)),
    ],
    "volcanic": [
        (-1.0, (255, 100, 20)),
        (-0.25, (255, 70, 15)),
        (-0.05, (180, 35, 10)),
        (0.05, (140, 30, 10)),
        (0.3, (60, 20, 10)),
        (0.6, (40, 18, 8)),
        (1.0, (25, 12, 5)),
    ],
    "ice": [
        (-1.0, (160, 185, 240)),
        (-0.15, (180, 200, 250)),
        (0.0, (210, 225, 255)),
        (0.2, (230, 240, 255)),
        (0.5, (245, 248, 255)),
        (1.0, (255, 255, 255)),
    ],
    "desert": [
        (-1.0, (140, 110, 60)),
        (-0.2, (160, 130, 75)),
        (0.0, (200, 175, 95)),
        (0.2, (225, 200, 110)),
        (0.4, (240, 215, 130)),
        (0.7, (180, 145, 90)),
        (1.0, (150, 120, 80)),
    ],
    "barren": [
        (-1.0, (100, 80, 60)),
        (-0.2, (130, 105, 80)),
        (0.0, (165, 135, 100)),
        (0.2, (185, 150, 110)),
        (0.5, (200, 165, 120)),
        (1.0, (140, 110, 80)),
    ],
    "toxic": [
        (-1.0, (60, 220, 80)),
        (-0.1, (80, 255, 100)),
        (0.0, (70, 200, 90)),
        (0.2, (60, 180, 80)),
        (0.5, (90, 160, 70)),
        (1.0, (50, 130, 50)),
    ],
    "crystal": [
        (-1.0, (140, 220, 240)),
        (-0.1, (160, 240, 255)),
        (0.1, (180, 255, 255)),
        (0.3, (200, 255, 250)),
        (0.6, (170, 235, 245)),
        (1.0, (150, 220, 240)),
    ],
}

# Gas giant band color palettes (warm and cool variants)
GAS_GIANT_PALETTES = [
    # Jupiter-like warm
    [(200, 140, 80), (240, 190, 120), (220, 160, 90), (180, 120, 60), (255, 210, 150)],
    # Saturn-like pale
    [(220, 200, 150), (240, 220, 170), (200, 180, 130), (230, 210, 160), (250, 235, 190)],
    # Blue-gray gas giant
    [(120, 140, 180), (150, 170, 210), (100, 120, 160), (170, 190, 220), (130, 150, 190)],
]


# ── Name generator ───────────────────────────────────────────────────────────

def generate_name():
    """Generate a random planet name"""
    prefixes = [
        "Xen", "Astra", "Nova", "Cryo", "Vul", "Zar", "Terra", "Oph", "Ere", "Quar",
        "Kel", "Dra", "Nyx", "Sol", "Lun", "Stel", "Gal", "Neb", "Cos", "Ori",
        "Pyr", "Aqua", "Aero", "Geo", "Chron", "Helio", "Thanat", "Hyper", "Proto", "Neo",
    ]
    suffixes = [
        "ion", "is", "ar", "os", "ea", "or", "a", "um", "ax", "ex",
        "ius", "eon", "yx", "ia", "us", "on", "an", "el", "al", "en",
        "ith", "eth", "oth", "ir", "ur", "ys", "ix", "ox", "yn", "ria",
    ]

    base_name = random.choice(prefixes) + random.choice(suffixes)

    if random.random() < 0.3:
        secondary = random.choice([
            " Prime", " Alpha", " Beta", " Gamma", " Delta", " Epsilon",
            " I", " II", " III", " IV", " V", " VI", " VII", " VIII", " IX", " X",
            " Major", " Minor", " Omega", " Sigma", " Tau",
        ])
        base_name += secondary

    return base_name + "-" + str(random.randint(1, 999))


# ── Pure NumPy Perlin noise ──────────────────────────────────────────────────

# 12 standard Perlin gradient vectors
_GRAD3 = np.array([
    [1, 1, 0], [-1, 1, 0], [1, -1, 0], [-1, -1, 0],
    [1, 0, 1], [-1, 0, 1], [1, 0, -1], [-1, 0, -1],
    [0, 1, 1], [0, -1, 1], [0, 1, -1], [0, -1, -1],
], dtype=np.float64)


def _build_perm_table(seed):
    """Build a 512-entry permutation table from seed."""
    rng = np.random.RandomState(seed & 0x7FFFFFFF)
    p = rng.permutation(256).astype(np.int32)
    return np.concatenate([p, p])


def _fade(t):
    """Improved Perlin fade: 6t^5 - 15t^4 + 10t^3"""
    return t * t * t * (t * (t * 6.0 - 15.0) + 10.0)


def perlin_noise_3d(x, y, z, perm):
    """Vectorized 3D Perlin noise. x, y, z are arrays of same shape. Returns array of noise values in ~[-1, 1]."""
    # Integer grid coordinates
    xi = np.floor(x).astype(np.int32)
    yi = np.floor(y).astype(np.int32)
    zi = np.floor(z).astype(np.int32)

    # Fractional part
    xf = x - xi
    yf = y - yi
    zf = z - zi

    # Wrap to 0-255
    xi = xi & 255
    yi = yi & 255
    zi = zi & 255

    # Fade curves
    u = _fade(xf)
    v = _fade(yf)
    w = _fade(zf)

    # Hash coordinates of the 8 cube corners
    a  = perm[xi] + yi
    aa = perm[a] + zi
    ab = perm[a + 1] + zi
    b  = perm[xi + 1] + yi
    ba = perm[b] + zi
    bb = perm[b + 1] + zi

    # Gradient indices (mod 12) for each corner
    g000 = perm[aa] % 12
    g001 = perm[aa + 1] % 12
    g010 = perm[ab] % 12
    g011 = perm[ab + 1] % 12
    g100 = perm[ba] % 12
    g101 = perm[ba + 1] % 12
    g110 = perm[bb] % 12
    g111 = perm[bb + 1] % 12

    # Dot products of gradient vectors with distance vectors
    def dot_grad(g_idx, dx, dy, dz):
        g = _GRAD3[g_idx]
        return g[..., 0] * dx + g[..., 1] * dy + g[..., 2] * dz

    n000 = dot_grad(g000, xf,       yf,       zf)
    n100 = dot_grad(g100, xf - 1.0, yf,       zf)
    n010 = dot_grad(g010, xf,       yf - 1.0, zf)
    n110 = dot_grad(g110, xf - 1.0, yf - 1.0, zf)
    n001 = dot_grad(g001, xf,       yf,       zf - 1.0)
    n101 = dot_grad(g101, xf - 1.0, yf,       zf - 1.0)
    n011 = dot_grad(g011, xf,       yf - 1.0, zf - 1.0)
    n111 = dot_grad(g111, xf - 1.0, yf - 1.0, zf - 1.0)

    # Trilinear interpolation
    nx00 = n000 + u * (n100 - n000)
    nx01 = n001 + u * (n101 - n001)
    nx10 = n010 + u * (n110 - n010)
    nx11 = n011 + u * (n111 - n011)

    nxy0 = nx00 + v * (nx10 - nx00)
    nxy1 = nx01 + v * (nx11 - nx01)

    return nxy0 + w * (nxy1 - nxy0)


def fbm_noise_3d(x, y, z, perm, octaves=6, persistence=0.5, lacunarity=2.0):
    """Fractal Brownian Motion: stacked octaves of Perlin noise."""
    total = np.zeros_like(x, dtype=np.float64)
    amplitude = 1.0
    frequency = 1.0
    max_amp = 0.0

    for _ in range(octaves):
        total += amplitude * perlin_noise_3d(x * frequency, y * frequency, z * frequency, perm)
        max_amp += amplitude
        amplitude *= persistence
        frequency *= lacunarity

    return total / max_amp


# ── Sphere geometry ──────────────────────────────────────────────────────────

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


# ── Surface color generation ────────────────────────────────────────────────

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


# ── Lighting ─────────────────────────────────────────────────────────────────

def apply_lighting(r, g, b, geo, planet_type):
    """Apply Lambertian diffuse + Blinn-Phong specular + limb darkening.

    Returns (r, g, b, diffuse) where diffuse is the raw diffuse factor for cloud lighting.
    """
    nx, ny, nz = geo["nx"], geo["ny"], geo["nz"]

    # Light from upper-right, toward camera
    lx, ly, lz = 0.6, -0.4, 0.8
    l_len = math.sqrt(lx * lx + ly * ly + lz * lz)
    lx /= l_len
    ly /= l_len
    lz /= l_len

    # Diffuse (Lambertian)
    diffuse = np.clip(nx * lx + ny * ly + nz * lz, 0.0, 1.0)

    # Limb darkening
    limb = np.sqrt(nz)

    # Ambient
    ambient = 0.1

    # Specular (Blinn-Phong)
    vx, vy, vz = 0.0, 0.0, 1.0
    hx, hy, hz = lx + vx, ly + vy, lz + vz
    h_len = math.sqrt(hx * hx + hy * hy + hz * hz)
    hx /= h_len
    hy /= h_len
    hz /= h_len

    n_dot_h = np.clip(nx * hx + ny * hy + nz * hz, 0.0, 1.0)
    shininess = 10.0 if planet_type == "gas_giant" else 30.0
    specular = np.power(n_dot_h, shininess) * 0.25

    # Combine
    light_factor = ambient + diffuse * limb
    r_out = r * light_factor + specular * 255.0
    g_out = g * light_factor + specular * 255.0
    b_out = b * light_factor + specular * 255.0

    return np.clip(r_out, 0, 255), np.clip(g_out, 0, 255), np.clip(b_out, 0, 255), diffuse


# ── Atmosphere ───────────────────────────────────────────────────────────────

def apply_atmosphere(r, g, b, geo, traits):
    """Apply Fresnel-based atmospheric rim glow."""
    strength = traits["atmo_strength"]
    if strength <= 0:
        return r, g, b

    nz = geo["nz"]
    atmo_color = traits["atmo_color"]

    # Fresnel: bright at the limb, transparent at center
    fresnel = np.power(np.clip(1.0 - nz, 0, 1), 3.0) * strength

    ar, ag, ab = float(atmo_color[0]), float(atmo_color[1]), float(atmo_color[2])

    r_out = r * (1.0 - fresnel) + ar * fresnel
    g_out = g * (1.0 - fresnel) + ag * fresnel
    b_out = b * (1.0 - fresnel) + ab * fresnel

    return np.clip(r_out, 0, 255), np.clip(g_out, 0, 255), np.clip(b_out, 0, 255)


def render_outer_glow(size, radius, traits):
    """Render atmospheric glow outside the planet sphere. Returns RGBA array."""
    strength = traits["atmo_strength"]
    if strength <= 0:
        return None

    cx = cy = size / 2.0
    yy, xx = np.mgrid[0:size, 0:size]
    dx = xx - cx
    dy = yy - cy
    dist = np.sqrt(dx * dx + dy * dy)

    glow_width = radius * 0.12
    glow_mask = (dist > radius) & (dist < radius + glow_width * 3)

    glow = np.zeros((size, size, 4), dtype=np.uint8)
    if not np.any(glow_mask):
        return glow

    falloff = np.exp(-((dist[glow_mask] - radius) / glow_width) ** 2)
    alpha = (falloff * strength * 180).astype(np.uint8)

    ac = traits["atmo_color"]
    glow[glow_mask, 0] = ac[0]
    glow[glow_mask, 1] = ac[1]
    glow[glow_mask, 2] = ac[2]
    glow[glow_mask, 3] = alpha

    return glow


# ── Ring system ──────────────────────────────────────────────────────────────

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


# ── Main rendering pipeline ──────────────────────────────────────────────────

def render_planet_image(size=512):
    """Render a complete planet image with metadata."""
    planet_type = random.choice(list(PLANET_TYPES.keys()))
    traits = PLANET_TYPES[planet_type]

    name = generate_name()
    temp_range = traits["temperature"]
    temperature = random.randint(temp_range[0], temp_range[1])
    has_rings = random.random() < 0.2
    has_moons = random.randint(0, 5)
    seed = random.randint(0, 10000)

    if has_rings:
        radius = random.randint(int(size * 0.22), int(size * 0.30))
    else:
        radius = random.randint(int(size * 0.30), int(size * 0.45))

    # 1. Build sphere geometry
    geo = build_sphere_geometry(size, radius)

    # 2. Generate surface colors
    r, g, b = generate_surface(geo, planet_type, seed)

    # 3. Apply lighting
    r, g, b, diffuse = apply_lighting(r, g, b, geo, planet_type)

    # 4. Add clouds (before atmosphere, after lighting)
    if planet_type in ("ocean", "forest", "ice", "desert"):
        cloud_alpha = generate_clouds(geo, seed, diffuse)
        # Blend white clouds over surface
        r = r * (1.0 - cloud_alpha) + 255.0 * cloud_alpha
        g = g * (1.0 - cloud_alpha) + 255.0 * cloud_alpha
        b = b * (1.0 - cloud_alpha) + 255.0 * cloud_alpha

    # 5. Apply atmosphere
    r, g, b = apply_atmosphere(r, g, b, geo, traits)

    # 6. Assemble planet RGBA
    planet_rgba = np.zeros((size, size, 4), dtype=np.uint8)
    mask = geo["mask"]
    planet_rgba[mask, 0] = np.clip(r, 0, 255).astype(np.uint8)
    planet_rgba[mask, 1] = np.clip(g, 0, 255).astype(np.uint8)
    planet_rgba[mask, 2] = np.clip(b, 0, 255).astype(np.uint8)
    planet_rgba[mask, 3] = 255

    # 7. Rings
    if has_rings:
        back_rings, front_rings = render_rings(size, radius, seed)
        final = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        if back_rings is not None:
            final = Image.alpha_composite(final, Image.fromarray(back_rings, "RGBA"))
        final = Image.alpha_composite(final, Image.fromarray(planet_rgba, "RGBA"))
        if front_rings is not None:
            final = Image.alpha_composite(final, Image.fromarray(front_rings, "RGBA"))
    else:
        final = Image.fromarray(planet_rgba, "RGBA")

    # 8. Outer atmospheric glow
    glow = render_outer_glow(size, radius, traits)
    if glow is not None:
        glow_img = Image.fromarray(glow, "RGBA")
        canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        canvas = Image.alpha_composite(canvas, glow_img)
        canvas = Image.alpha_composite(canvas, final)
        final = canvas

    metadata = {
        "name": name,
        "type": planet_type,
        "temperature": temperature,
        "radius": radius,
        "rings": has_rings,
        "moons": has_moons,
        "atmosphere": traits["atmosphere"],
        "seed": seed,
    }

    return final, metadata


# ── Save and open ────────────────────────────────────────────────────────────

def save_planet(planet_img, metadata, output_dir="export"):
    """Save planet image and metadata to files."""
    os.makedirs(output_dir, exist_ok=True)

    name = metadata["name"]
    image_path = os.path.join(output_dir, f"{name}.png")
    json_path = os.path.join(output_dir, f"{name}.json")

    planet_img.save(image_path)

    with open(json_path, "w") as f:
        json.dump(metadata, f, indent=4)

    print(f"Saved planet to {image_path}")
    print(f"Saved metadata to {json_path}")

    try:
        system = platform.system()
        if system == "Darwin":
            subprocess.run(["open", image_path], check=False)
        elif system == "Windows":
            os.startfile(image_path)
        elif system == "Linux":
            subprocess.run(["xdg-open", image_path], check=False)
        print(f"Opening {image_path}...")
    except Exception as e:
        print(f"Could not auto-open image: {e}")


if __name__ == "__main__":
    print("Generating random planet...")
    planet, data = render_planet_image()
    save_planet(planet, data)
    print(f"\nGenerated planet: {data['name']}")
    print(json.dumps(data, indent=4))
