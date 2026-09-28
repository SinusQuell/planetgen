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
    emission: np.ndarray = None  # (N, 3) light given off, 0..255, or None


def generate_surface(geo, planet_type, seed, temperature=None):
    """Generate the surface material for all masked pixels.

    temperature (°C) sizes the polar ice caps on types that have them.
    """
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
    crater_floor = np.zeros_like(height)
    if traits.get("craters"):
        dent, crater_floor = crater_field(px, py, pz, seed, traits["craters"])
        height = height + dent

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
    color *= (1.0 - 0.18 * crater_floor)[:, None]

    sea_level = traits.get("sea_level")
    if sea_level is None:
        liquid = np.zeros(len(height), dtype=bool)
    else:
        liquid = height < sea_level
        raw_height = height
        height = np.maximum(height, sea_level)
    specular = np.where(liquid, 0.8, land_specular)

    if traits.get("ice_caps") and temperature is not None:
        ice = polar_ice(px, py, pz, seed, offset, temperature, height)
        color = color * (1.0 - ice[:, None]) + np.array([236.0, 242.0, 250.0]) * ice[:, None]
        frozen = ice > 0.5
        liquid = liquid & ~frozen
        specular = np.where(frozen, 0.3, specular)

    emission = None
    glow = traits.get("glow")
    if glow is not None and sea_level is not None:
        # Deeper channels glow hotter; the shores cool off into the crust.
        depth = sea_level - raw_height
        heat = smoothstep(-0.03, 0.25, depth)
        emission = np.array(glow, dtype=np.float64) * heat[:, None]

    return Surface(color, height, specular, liquid, emission)


def crater_field(px, py, pz, seed, count):
    """Scatter impact craters over the sphere.

    Returns (height_change, floor): the dent each pixel gets and how deep
    inside a crater bowl it sits (0..1), used to darken crater floors.
    Sizes follow a power law, so there are many small craters and few big
    ones.
    """
    rng = np.random.RandomState((seed + 9191) & 0x7FFFFFFF)
    centers = rng.normal(size=(count, 3))
    centers /= np.linalg.norm(centers, axis=1, keepdims=True)
    # Angular radius in radians, between about 1 and 17 degrees
    radii = np.clip(0.02 * (1.0 - rng.uniform(0, 0.97, count)) ** (-1.0 / 1.3), 0.02, 0.3)
    # Older craters are shallower and softer.
    freshness = rng.uniform(0.35, 1.0, count)

    change = np.zeros_like(px)
    floor = np.zeros_like(px)
    # Biggest first, so small craters punch into big ones rather than the
    # other way around.
    for i in np.argsort(-radii):
        cx, cy, cz = centers[i]
        radius = radii[i]
        cos_angle = px * cx + py * cy + pz * cz
        near = np.nonzero(cos_angle > np.cos(radius * 1.8))[0]
        if near.size == 0:
            continue
        d = np.arccos(np.clip(cos_angle[near], -1.0, 1.0)) / radius

        depth = 5.0 * radius * freshness[i]
        bowl = np.clip(1.0 - d * d, 0.0, 1.0)
        rim = np.exp(-((d - 1.0) / 0.22) ** 2)
        dent = depth * (0.35 * rim - bowl)
        # Flatten what was there before inside the bowl
        change[near] = change[near] * (1.0 - bowl) + dent
        floor[near] = np.maximum(floor[near], bowl * freshness[i])
    return change, floor


def polar_ice(px, py, pz, seed, offset, temperature, height):
    """Ice cover 0..1 around the poles. At 0 °C the caps reach down to about
    45° latitude, by 50 °C they are gone. High ground freezes a little
    further from the pole."""
    edge = np.clip(0.72 + temperature * 0.006, 0.55, 1.1)
    ragged = _noise("fbm", px, py, pz, 4.0, offset + 300, seed + 400, octaves=5) * 0.12
    latitude = np.abs(py) + ragged + np.maximum(height, 0.0) * 0.15
    return smoothstep(edge - 0.015, edge + 0.015, latitude)


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


def _gas_giant_band_table(rng, palette, samples=2048):
    """Color for every latitude, as a table from -1 (south) to 1 (north).

    Bands have uneven widths, alternate between light zones and dark belts
    and blend into each other over a short distance."""
    count = rng.randint(14, 26)
    # Evenly spaced edges, each nudged by up to 40% of a band width
    spacing = 2.0 / count
    edges = np.linspace(-1.0, 1.0, count + 1)
    edges[1:-1] += rng.uniform(-0.4, 0.4, count - 1) * spacing
    start_light = rng.rand() < 0.5

    lat = np.linspace(-1.0, 1.0, samples)
    table = np.zeros((samples, 3))
    for i in range(count):
        light = (i % 2 == 0) == start_light
        choices = palette["zones"] if light else palette["belts"]
        color = np.array(choices[rng.randint(len(choices))], dtype=np.float64)
        color = color * rng.uniform(0.92, 1.06)
        table[(lat >= edges[i]) & (lat <= edges[i + 1])] = color

    # Faint sub-bands inside each band
    fine = np.zeros(samples)
    for freq in (37, 71, 131):
        fine += np.sin(lat * freq + rng.uniform(0, 2 * math.pi)) * rng.uniform(0.01, 0.035)
    table *= (1.0 + fine)[:, None]

    # High latitudes fade into an even polar haze instead of rings of bands.
    haze = table[np.abs(lat) < 0.2].mean(axis=0) * 0.85
    polar = smoothstep(0.62, 0.9, np.abs(lat))[:, None]
    table = table * (1.0 - polar) + haze * polar

    # Soften the band edges with a box blur.
    width = samples // 70
    kernel = np.ones(width) / width
    padded = np.pad(table, ((width, width), (0, 0)), mode="edge")
    for ch in range(3):
        table[:, ch] = np.convolve(padded[:, ch], kernel, mode="same")[width:-width]
    # Where the color changes fast, bands meet and shear against each other.
    shear = np.abs(np.gradient(table.sum(axis=1)))
    shear = np.clip(shear / (shear.max() + 1e-9) * 3.0, 0.0, 1.0)
    return lat, table, shear


def _generate_gas_giant_surface(geo, seed, perm):
    """Gas giant: latitude bands sheared by turbulence, with oval storms."""
    px, py, pz = geo["px"], geo["py"], geo["pz"]

    rng = np.random.RandomState((seed + 5555) & 0x7FFFFFFF)
    palette = GAS_GIANT_PALETTES[rng.randint(0, len(GAS_GIANT_PALETTES))]
    offset = rng.uniform(-1000, 1000, 3)
    table_lat, table, shear_table = _gas_giant_band_table(rng, palette)

    # Latitude as an angle, so bands near the poles are not squeezed.
    lat = np.arcsin(np.clip(py, -1, 1)) / (math.pi / 2)
    lon = np.arctan2(pz, px)

    # Stretched noise: slow waves along the bands and fine streaks.
    ox, oy, oz = offset
    waves = fbm_noise_3d(px * 2.5 + ox, py * 9.0 + oy, pz * 2.5 + oz,
                         _build_perm_table(seed + 2000), octaves=4)
    eddies = fbm_noise_3d(px * 7.0 + ox, py * 22.0 + oy, pz * 7.0 + oz,
                          _build_perm_table(seed + 2100), octaves=5, persistence=0.6)
    streaks = fbm_noise_3d(px * 5.0 + ox, py * 70.0 + oy, pz * 5.0 + oz,
                           _build_perm_table(seed + 3000), octaves=4, persistence=0.55)
    # Turbulence is strongest where bands meet and toward the chaotic poles.
    shear = np.interp(lat + waves * 0.04, table_lat, shear_table)
    polar = smoothstep(0.6, 0.95, np.abs(lat))
    swirl = fbm_noise_3d(px * 12.0 + ox, py * 18.0 + oy, pz * 12.0 + oz,
                         _build_perm_table(seed + 2200), octaves=4, persistence=0.55)
    band_lat = (lat + waves * 0.04 + eddies * 0.012
                + swirl * (0.006 + 0.03 * shear + 0.08 * polar))

    # Storms: oval vortices that twist the bands around them.
    storm_mix = np.zeros_like(lat)
    for _ in range(rng.randint(1, 4)):
        c_lat = rng.uniform(-0.6, 0.6)
        c_lon = rng.uniform(-math.pi, math.pi)
        size = rng.uniform(0.05, 0.14)
        d_lon = (lon - c_lon + math.pi) % (2 * math.pi) - math.pi
        local_x = d_lon * np.cos(lat * math.pi / 2) / (math.pi / 2)
        local_y = lat - c_lat
        # Storms are wider than they are tall.
        dist = np.sqrt((local_x / 2.2) ** 2 + local_y ** 2) / size
        twist = 2.4 * np.exp(-dist * dist) * rng.choice([-1, 1])
        rotated_y = local_x * np.sin(twist) / 2.2 + local_y * np.cos(twist)
        band_lat = band_lat + (rotated_y - local_y) * (dist < 2.5)
        storm_mix = np.maximum(storm_mix, smoothstep(1.0, 0.55, dist) * rng.uniform(0.6, 0.95))

    color = np.stack([np.interp(band_lat, table_lat, table[:, ch]) for ch in range(3)], axis=-1)
    color *= (1.0 + streaks * 0.07 + eddies * 0.08)[:, None]

    storm_color = np.array(palette["storm"], dtype=np.float64)
    color = color * (1.0 - storm_mix[:, None]) + storm_color * storm_mix[:, None]

    # Hazier, slightly darker poles
    color *= (1.0 - 0.2 * polar)[:, None]

    color = np.clip(color, 0, 255)
    return color[:, 0], color[:, 1], color[:, 2]


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
