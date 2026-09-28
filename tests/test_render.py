import json

import numpy as np
import pytest

from planetgen import PLANET_TYPES, render_planet_image
from planetgen import PlanetSpec
from planetgen.cli import main
from planetgen.render import render_spin


def pixels(image):
    return np.asarray(image)


def test_same_seed_gives_same_planet():
    a, meta_a = render_planet_image(size=96, seed=1234)
    b, meta_b = render_planet_image(size=96, seed=1234)
    assert meta_a == meta_b
    assert np.array_equal(pixels(a), pixels(b))


def test_image_size_does_not_change_the_planet():
    _, small = render_planet_image(size=64, seed=55)
    _, large = render_planet_image(size=256, seed=55)
    assert small == large


def test_unknown_option_is_rejected():
    with pytest.raises(TypeError):
        render_planet_image(size=64, seed=1, colour="red")


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


def test_moons_can_be_hidden():
    shown, _ = render_planet_image(size=128, seed=3, moons=4, rings=False)
    hidden, _ = render_planet_image(size=128, seed=3, moons=4, rings=False, show_moons=False)
    assert not np.array_equal(pixels(shown), pixels(hidden))


def test_cli_writes_image_and_metadata(tmp_path):
    assert main(["--seed", "9", "--size", "64", "--out", str(tmp_path), "-q"]) == 0
    pngs = list(tmp_path.glob("*.png"))
    jsons = list(tmp_path.glob("*.json"))
    assert len(pngs) == 1 and len(jsons) == 1
    assert json.loads(jsons[0].read_text())["seed"] == 9


def test_spin_turns_the_planet():
    spec = PlanetSpec.random(5, type="ocean", rings=False, moons=0)
    frames = render_spin(spec, size=64, frames=4)
    assert len(frames) == 4
    assert not np.array_equal(pixels(frames[0]), pixels(frames[1]))


def test_cli_spin_writes_animation(tmp_path):
    assert main(["--seed", "4", "--size", "48", "--spin", "3", "--out", str(tmp_path), "-q"]) == 0
    assert len(list(tmp_path.glob("*-spin.gif"))) == 1


def test_saved_metadata_rebuilds_the_same_planet():
    spec = PlanetSpec.random(77, tilt=12.5, hue=40)
    again = PlanetSpec.from_dict(spec.to_dict())
    assert again == spec


def test_cli_from_file_with_override(tmp_path):
    assert main(["--seed", "8", "--size", "48", "--out", str(tmp_path), "-q"]) == 0
    saved = next(tmp_path.glob("*.json"))
    out = tmp_path / "again"
    assert main(["--from", str(saved), "--size", "48", "--tilt", "33", "-q",
                 "--out", str(out)]) == 0
    data = json.loads(next(out.glob("*.json")).read_text())
    assert data["tilt"] == 33
    assert data["seed"] == 8
