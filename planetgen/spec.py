"""Everything that describes one planet, drawn from a single seed."""

import random
from dataclasses import asdict, dataclass, fields

from .names import generate_name
from .types import PLANET_TYPES


@dataclass
class PlanetSpec:
    seed: int
    name: str
    type: str
    temperature: int
    rings: bool
    moons: int
    # Planet radius as a fraction of the image width, so the same seed looks
    # the same at every image size.
    scale: float
    # Direction of the sun, see lighting.light_direction.
    light_azimuth: float
    light_elevation: float
    # Orientation in degrees: tilt turns the axis in the image, inclination
    # tips the north pole toward the viewer, rotation spins the planet.
    tilt: float
    inclination: float
    rotation: float
    # Ring edges in planet radii.
    ring_inner: float
    ring_outer: float
    # Fraction of the sky covered by clouds, 0..1.
    clouds: float
    # How strongly terrain height shades the surface; 0 renders it flat.
    relief: float = 1.0
    # Multiplies how thick the planet type's atmosphere looks; 0 removes it.
    atmosphere_density: float = 1.0

    @property
    def atmosphere(self):
        return PLANET_TYPES[self.type]["atmosphere"]

    @classmethod
    def random(cls, seed=None, **overrides):
        """Roll a planet from a seed. Any field passed in overrides (and not
        None) replaces the rolled value; the other fields stay the same as
        they would be without the override."""
        if seed is None:
            seed = random.randint(0, 999_999)
        rng = random.Random(seed)

        planet_type = rng.choice(list(PLANET_TYPES.keys()))
        traits = PLANET_TYPES[overrides.get("type") or planet_type]
        values = {
            "seed": seed,
            "type": planet_type,
            "name": generate_name(rng),
            "temperature": rng.randint(*traits["temperature"]),
            "rings": rng.random() < 0.2,
            "moons": rng.randint(0, 5),
        }
        ringed = overrides.get("rings")
        if ringed is None:
            ringed = values["rings"]
        values["scale"] = rng.uniform(0.22, 0.30) if ringed else rng.uniform(0.30, 0.45)
        # New rolls go at the end so older seeds keep their earlier values.
        values["light_azimuth"] = round(rng.uniform(15, 165), 1)
        values["light_elevation"] = round(rng.uniform(15, 60), 1)
        values["tilt"] = round(rng.uniform(-25, 25), 1)
        # Positive, so with the sun above the planet we see the lit face of
        # the rings.
        values["inclination"] = round(rng.uniform(8, 30), 1)
        values["rotation"] = round(rng.uniform(0, 360), 1)
        values["ring_inner"] = round(rng.uniform(1.3, 1.5), 2)
        values["ring_outer"] = round(rng.uniform(1.9, 2.4), 2)
        values["clouds"] = round(rng.uniform(*traits.get("clouds", (0.0, 0.0))), 2)

        unknown = set(overrides) - {f.name for f in fields(cls)}
        if unknown:
            raise TypeError(f"unknown planet option(s): {', '.join(sorted(unknown))}")
        values.update({k: v for k, v in overrides.items() if v is not None})
        if values["rings"] and overrides.get("scale") is None:
            # Keep the whole ring system inside the image.
            values["scale"] = min(values["scale"], 0.47 / values["ring_outer"])
        values["scale"] = round(values["scale"], 3)
        return cls(**values)

    def to_dict(self):
        data = asdict(self)
        data["atmosphere"] = self.atmosphere
        return data
