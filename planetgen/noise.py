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

    # Gradient components per hash value, looked up once per call instead
    # of indexing a (N, 3) array for every corner.
    grad = _GRAD3[perm % 12]
    gx, gy, gz = grad[:, 0], grad[:, 1], grad[:, 2]

    def dot_grad(h, dx, dy, dz):
        return gx[h] * dx + gy[h] * dy + gz[h] * dz

    xf1 = xf - 1.0
    yf1 = yf - 1.0
    zf1 = zf - 1.0
    n000 = dot_grad(aa,     xf,  yf,  zf)
    n100 = dot_grad(ba,     xf1, yf,  zf)
    n010 = dot_grad(ab,     xf,  yf1, zf)
    n110 = dot_grad(bb,     xf1, yf1, zf)
    n001 = dot_grad(aa + 1, xf,  yf,  zf1)
    n101 = dot_grad(ba + 1, xf1, yf,  zf1)
    n011 = dot_grad(ab + 1, xf,  yf1, zf1)
    n111 = dot_grad(bb + 1, xf1, yf1, zf1)

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
