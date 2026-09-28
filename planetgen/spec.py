"""Everything that describes one planet, drawn from a single seed."""

import math
import random
from dataclasses import asdict, dataclass, fields

from .names import generate_name
from .types import PLANET_TYPES


# Fields whose rolled values depend on the planet type
TYPE_DEPENDENT_FIELDS = ("temperature", "clouds", "cities", "radius_km", "density",
                         "day_length_hours")


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
    # Degrees to rotate the ground colors by. Small by default; large values
    # give alien color schemes.
    hue: float
    # Inhabited: city lights on the night side.
    cities: bool
    # Physical stats for the metadata; they do not change the picture.
    radius_km: int
    density: float          # g/cm³
    day_length_hours: float
    # How strongly terrain height shades the surface; 0 renders it flat.
    relief: float = 1.0
    # Draw the moons into the picture (they are always counted).
    show_moons: bool = True
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
        values["hue"] = round(rng.uniform(-12, 12), 1)
        values["cities"] = rng.random() < traits.get("cities", 0.0)
        giant = traits.get("banded")
        if giant == "gas":
            radius, density, day = (40_000, 90_000), (0.6, 1.6), (9, 18)
        elif giant == "ice":
            radius, density, day = (18_000, 30_000), (1.1, 1.8), (13, 20)
        else:
            radius, density, day = (1_500, 9_000), (2.8, 6.0), (8, 60)
        values["radius_km"] = int(round(rng.uniform(*radius), -1))
        values["density"] = round(rng.uniform(*density), 2)
        values["day_length_hours"] = round(rng.uniform(*day), 1)

        unknown = set(overrides) - {f.name for f in fields(cls)}
        if unknown:
            raise TypeError(f"unknown planet option(s): {', '.join(sorted(unknown))}")
        values.update({k: v for k, v in overrides.items() if v is not None})
        if values["rings"] and overrides.get("scale") is None:
            # Keep the whole ring system inside the image.
            values["scale"] = min(values["scale"], 0.47 / values["ring_outer"])
        values["scale"] = round(values["scale"], 3)
        return cls(**values)

    @property
    def mass_earths(self):
        earth_mass_kg = 5.972e24
        volume_m3 = 4.0 / 3.0 * math.pi * (self.radius_km * 1000.0) ** 3
        return volume_m3 * self.density * 1000.0 / earth_mass_kg

    @property
    def gravity_g(self):
        """Surface gravity in multiples of Earth's."""
        big_g = 6.674e-11
        mass_kg = self.mass_earths * 5.972e24
        return big_g * mass_kg / (self.radius_km * 1000.0) ** 2 / 9.81

    @property
    def description(self):
        """One sentence summing the planet up."""
        kind = self.type.replace("_", " ")
        article = "An" if kind[0] in "aeiou" else "A"
        air = self.atmosphere
        features = ["no atmosphere" if air == "none" else f"a {air} atmosphere"]
        if self.moons:
            features.append(f"{self.moons} moon{'s' if self.moons != 1 else ''}")
        if self.rings:
            features.append("a ring system")
        if self.cities:
            features.append("lit cities on its night side")
        listed = features[0] if len(features) == 1 else (
            ", ".join(features[:-1]) + " and " + features[-1])
        sentence = f"{article} {kind} world {self.radius_km * 2:,} km across with {listed}"
        return sentence + "."

    @classmethod
    def from_dict(cls, data, **overrides):
        """Rebuild a spec from saved metadata. Keys that are not spec fields
        (derived stats, the description) are ignored; fields missing from
        older files are rolled from the seed as usual."""
        known = {f.name for f in fields(cls)}
        saved = {k: v for k, v in data.items() if k in known}
        new_type = overrides.get("type")
        if new_type and new_type != saved.get("type"):
            # These were rolled for the old type; roll them again.
            for key in TYPE_DEPENDENT_FIELDS:
                saved.pop(key, None)
        saved.update({k: v for k, v in overrides.items() if v is not None})
        seed = saved.pop("seed")
        # Roll the full spec first so anything the file lacks gets a value.
        return cls.random(seed, **saved)

    def to_dict(self):
        data = asdict(self)
        data["atmosphere"] = self.atmosphere
        data["mass_earths"] = round(self.mass_earths, 3)
        data["gravity_g"] = round(self.gravity_g, 2)
        data["description"] = self.description
        return data
