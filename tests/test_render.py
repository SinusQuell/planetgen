import json

import numpy as np
import pytest

from planetgen import PLANET_TYPES, render_planet_image
from planetgen.cli import main


def pixels(image):
    return np.asarray(image)


def test_same_seed_gives_same_planet():
    a, meta_a = render_planet_image(size=96, seed=1234)
    b, meta_b = render_planet_image(size=96, seed=1234)
    assert meta_a == meta_b
    assert np.array_equal(pixels(a), pixels(b))


def test_different_seeds_differ():
    a, _ = render_planet_image(size=96, seed=1, planet_type="ocean")
    b, _ = render_planet_image(size=96, seed=2, planet_type="ocean")
    assert not np.array_equal(pixels(a), pixels(b))


@pytest.mark.parametrize("planet_type", sorted(PLANET_TYPES))
def test_every_type_renders(planet_type):
    image, meta = render_planet_image(size=96, seed=7, planet_type=planet_type)
    assert image.size == (96, 96)
    assert image.mode == "RGBA"
    assert meta["type"] == planet_type
    alpha = pixels(image)[..., 3]
    assert alpha[48, 48] == 255  # planet covers the center
    assert alpha[0, 0] == 0      # corners stay transparent


@pytest.mark.parametrize("rings", [True, False])
def test_ring_override(rings):
    _, meta = render_planet_image(size=64, seed=3, rings=rings)
    assert meta["rings"] is rings


def test_cli_writes_image_and_metadata(tmp_path):
    assert main(["--seed", "9", "--size", "64", "--out", str(tmp_path), "-q"]) == 0
    pngs = list(tmp_path.glob("*.png"))
    jsons = list(tmp_path.glob("*.json"))
    assert len(pngs) == 1 and len(jsons) == 1
    assert json.loads(jsons[0].read_text())["seed"] == 9
