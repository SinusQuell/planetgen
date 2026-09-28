"""Vectorized 3D Perlin noise in pure NumPy."""

import numpy as np


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


def ridged_noise_3d(x, y, z, perm, octaves=5, lacunarity=2.1, gain=2.0):
    """Ridged multifractal noise in 0..1: sharp crests where Perlin noise
    crosses zero, like mountain chains or cracks. Each octave is weighted by
    the one before it, so detail gathers along the ridges."""
    total = np.zeros_like(x, dtype=np.float64)
    weight = np.ones_like(x, dtype=np.float64)
    amplitude = 1.0
    frequency = 1.0
    max_amp = 0.0

    for _ in range(octaves):
        ridge = 1.0 - np.abs(perlin_noise_3d(x * frequency, y * frequency, z * frequency, perm))
        ridge = ridge * ridge * weight
        weight = np.clip(ridge * gain, 0.0, 1.0)
        total += ridge * amplitude
        max_amp += amplitude
        amplitude *= 0.5
        frequency *= lacunarity

    return total / max_amp
