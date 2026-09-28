"""Planetary ring system."""

import numpy as np

from .noise import _build_perm_table, fbm_noise_3d
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

# Samples across the ring band for the precomputed profiles. Fine enough
# that ringlets stay crisp on a 4K render.
PROFILE_SAMPLES = 4096

# Subpixel grid used to anti-alias the rings (n x n samples per pixel).
SUPERSAMPLE = 3


class RingSystem:
    """A ring system's radial structure, fixed by a seed.

    Opacity and color only depend on the distance from the planet center,
    so both are precomputed as 1D profiles across the band.
    """

    def __init__(self, seed, inner, outer):
        self.inner = inner
        self.outer = outer
        rng = np.random.RandomState((seed + 4444) & 0x7FFFFFFF)

        t = np.linspace(0.0, 1.0, PROFILE_SAMPLES)
        self._t = t
        zeros = np.zeros_like(t)

        # Broad density zones plus fine ringlets, both from 1D noise.
        zone_perm = _build_perm_table(seed + 6000)
        zones = fbm_noise_3d(t * 6.0, zeros + rng.uniform(0, 100), zeros, zone_perm, octaves=3)
        ringlet_perm = _build_perm_table(seed + 6100)
        ringlets = fbm_noise_3d(t * 90.0, zeros + rng.uniform(0, 100), zeros, ringlet_perm,
                                octaves=4, persistence=0.6)
        density = 0.55 + 0.9 * zones + 0.45 * ringlets
        density = np.clip(density, 0.05, 1.0)

        # A few clean gaps, the widest one playing the Cassini division.
        for _ in range(rng.randint(1, 4)):
            center = rng.uniform(0.15, 0.85)
            width = rng.uniform(0.006, 0.035)
            density *= 1.0 - 0.95 * np.exp(-0.5 * ((t - center) / width) ** 2)

        edges = smoothstep(0.0, 0.04, t) * smoothstep(1.0, 0.97, t)
        # Rings are usually thinner toward the inside.
        taper = 0.45 + 0.55 * smoothstep(0.0, 0.35, t)
        self._opacity = np.clip(density * edges * taper * 0.92, 0.0, 1.0)

        base = np.array(RING_STYLES[rng.randint(0, len(RING_STYLES))], dtype=np.float64)
        base = np.clip(base + rng.randint(-20, 21, base.shape), 0, 255)
        color = np.stack([np.interp(t, np.linspace(0, 1, len(base)), base[:, ch])
                          for ch in range(3)], axis=-1)
        # Denser ringlets look slightly brighter and warmer.
        color *= (0.85 + 0.25 * ringlets)[:, None]
        self._color = np.clip(color, 0, 255)

    def _band_position(self, dist):
        return (dist - self.inner) / (self.outer - self.inner)

    def opacity_at(self, dist):
        t = self._band_position(dist)
        return np.interp(t, self._t, self._opacity, left=0.0, right=0.0)

    def color_at(self, dist):
        t = np.clip(self._band_position(dist), 0.0, 1.0)
        return np.stack([np.interp(t, self._t, self._color[:, ch]) for ch in range(3)], axis=-1)

    def render(self, size, planet_radius, pole, light):
        """Render the rings as (back_rgba, front_rgba) float arrays in 0..1.

        The back layer goes under the planet, the front layer over it.
        Returns (None, None) if no ring pixel lands in the image.
        """
        pole = np.asarray(pole, dtype=np.float64)
        light = np.asarray(light, dtype=np.float64)
        n = SUPERSAMPLE
        offsets = (np.arange(n) + 0.5) / n

        cx = cy = size / 2.0
        yy, xx = np.mgrid[0:size, 0:size]
        back = np.zeros((size, size, 4))
        front = np.zeros((size, size, 4))

        # Rings are lit from the side the sun is on. Seen from the other
        # side, only light scattering through thin parts gets to the viewer.
        sun_side = float(np.dot(pole, light))
        view_side = pole[2]
        lit_face = 0.25 + 0.85 * abs(sun_side)
        same_side = np.sign(sun_side) == np.sign(view_side)

        for oy in offsets:
            for ox in offsets:
                u = (xx + ox - cx) / planet_radius
                v = (yy + oy - cy) / planet_radius
                depth = _ring_plane_depth(u, v, pole)
                dist = np.sqrt(u * u + v * v + depth * depth)
                hit = (dist >= self.inner) & (dist <= self.outer)
                if not np.any(hit):
                    continue

                d = dist[hit]
                opacity = self.opacity_at(d)
                if same_side:
                    brightness = np.full_like(d, lit_face)
                else:
                    brightness = 0.15 + 1.1 * abs(sun_side) * (1.0 - 0.7 * opacity)

                # Planet shadow: the ring point is shadowed when the line
                # toward the sun passes through the planet.
                q = np.stack([u[hit], v[hit], depth[hit]], axis=-1)
                toward_sun = q @ light
                off_axis = np.sqrt(np.maximum((q * q).sum(-1) - toward_sun ** 2, 0.0))
                shadow = np.where(toward_sun < 0, smoothstep(0.97, 1.03, off_axis), 1.0)
                brightness = brightness * (0.06 + 0.94 * shadow)

                rgb = self.color_at(d) / 255.0 * brightness[:, None]
                # Only rings over the planet disc need splitting into behind
                # and in front. Keeping everything else in one layer avoids a
                # seam where the two halves meet.
                over_disc = (u[hit] ** 2 + v[hit] ** 2) < 1.0
                in_front = (depth[hit] > 0) | ~over_disc
                layer = in_front[:, None].astype(np.float64)
                sample = np.concatenate([rgb * opacity[:, None], opacity[:, None]], axis=-1)
                # Accumulate premultiplied color so the average blends right.
                front[hit] += sample * layer
                back[hit] += sample * (1 - layer)

        samples = n * n
        back /= samples
        front /= samples
        if not (back[..., 3].any() or front[..., 3].any()):
            return None, None
        return _unpremultiply(back), _unpremultiply(front)

    def shadow_on_planet(self, geo, pole, light):
        """How much sunlight reaches each planet pixel past the rings (0..1)."""
        pole = np.asarray(pole, dtype=np.float64)
        light = np.asarray(light, dtype=np.float64)
        s = np.stack([geo["nx"], geo["ny"], geo["nz"]], axis=-1)
        pole_dot_light = float(np.dot(pole, light))
        if abs(pole_dot_light) < 1e-4:
            return np.ones(len(s))
        # March from the surface toward the sun until the ring plane.
        travel = -(s @ pole) / pole_dot_light
        hit_point = s + travel[:, None] * light
        dist = np.sqrt((hit_point * hit_point).sum(-1))
        opacity = np.where(travel > 0, self.opacity_at(dist), 0.0)
        return 1.0 - 0.9 * opacity


def _ring_plane_depth(u, v, pole):
    """z of the ring plane under each pixel. The plane passes through the
    planet center with the pole as its normal."""
    ax, ay, az = pole
    # Exactly edge-on rings would divide by zero; nudge them to a sliver.
    if abs(az) < 0.02:
        az = 0.02 if az >= 0 else -0.02
    return -(ax * u + ay * v) / az


def _unpremultiply(rgba):
    alpha = rgba[..., 3:4]
    rgb = np.divide(rgba[..., :3], alpha, out=np.zeros_like(rgba[..., :3]), where=alpha > 1e-6)
    return np.concatenate([rgb, alpha], axis=-1)
