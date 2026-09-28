"""Command line interface."""

import argparse
import json
import os
import sys

from .background import BACKGROUNDS
from .output import open_file, save_animation, save_planet
from .render import render_planet, render_spin
from .spec import PlanetSpec
from .types import PLANET_TYPES


def build_parser():
    parser = argparse.ArgumentParser(
        prog="planetgen",
        description="Generate procedural planet images with matching metadata.",
    )
    parser.add_argument("-t", "--type", choices=sorted(PLANET_TYPES), metavar="TYPE",
                        help="planet type (default: random). See --list-types.")
    parser.add_argument("-s", "--seed", type=int,
                        help="seed for a reproducible planet (default: random)")
    parser.add_argument("-f", "--from", dest="from_file", metavar="JSON",
                        help="re-render a planet from its saved metadata file; other "
                             "options change it from there")
    parser.add_argument("-n", "--count", type=int, default=1,
                        help="number of planets to generate (default: 1)")
    parser.add_argument("--size", type=int, default=512,
                        help="image width and height in pixels (default: 512)")
    rings = parser.add_mutually_exclusive_group()
    rings.add_argument("--rings", dest="rings", action="store_true", default=None,
                       help="always give the planet rings")
    rings.add_argument("--no-rings", dest="rings", action="store_false",
                       help="never give the planet rings")
    parser.add_argument("--light", nargs=2, type=float, metavar=("AZIMUTH", "ELEVATION"),
                        help="sun direction in degrees: azimuth counterclockwise from the "
                             "right edge, elevation toward the viewer (90 = fully lit, "
                             "0 = half lit, negative = crescent)")
    parser.add_argument("--tilt", type=float,
                        help="axial tilt in degrees, counterclockwise in the image")
    parser.add_argument("--inclination", type=float,
                        help="degrees the north pole leans toward you (0 = rings edge-on)")
    parser.add_argument("--rotation", type=float,
                        help="spin around the axis in degrees, shows a different side")
    parser.add_argument("--relief", type=float,
                        help="terrain shading strength (default 1, 0 = flat)")
    parser.add_argument("--hue", type=float, metavar="DEGREES",
                        help="rotate the surface colors, e.g. 180 for an alien palette")
    parser.add_argument("--clouds", type=float, metavar="COVER",
                        help="cloud cover from 0 to 1 (types without weather ignore it)")
    parser.add_argument("--atmosphere", type=float, metavar="DENSITY",
                        help="atmosphere thickness multiplier (default 1, 0 = none)")
    cities = parser.add_mutually_exclusive_group()
    cities.add_argument("--cities", dest="cities", action="store_true", default=None,
                        help="show city lights on the night side")
    cities.add_argument("--no-cities", dest="cities", action="store_false",
                        help="an uninhabited planet")
    parser.add_argument("--moons", type=int, metavar="COUNT",
                        help="number of moons (default: random, 0 to 5)")
    parser.add_argument("--hide-moons", action="store_true",
                        help="leave the moons out of the picture")
    parser.add_argument("-b", "--background", choices=BACKGROUNDS, default="transparent",
                        help="what goes behind the planet (default: transparent)")
    parser.add_argument("--spin", type=int, nargs="?", const=36, metavar="FRAMES",
                        help="also save an animation of one full turn "
                             "(default 36 frames when given without a number)")
    parser.add_argument("--spin-format", choices=["gif", "webp"], default="gif",
                        help="animation format; webp keeps transparency (default: gif)")
    parser.add_argument("--fps", type=int, default=20,
                        help="animation frames per second (default: 20)")
    parser.add_argument("-o", "--out", default="export",
                        help="output folder (default: export)")
    parser.add_argument("--open", action="store_true",
                        help="open the image in your default viewer when done")
    parser.add_argument("-q", "--quiet", action="store_true",
                        help="only print the saved file paths")
    parser.add_argument("--list-types", action="store_true",
                        help="list the available planet types and exit")
    return parser


def list_types():
    for name, traits in sorted(PLANET_TYPES.items()):
        low, high = traits["temperature"]
        print(f"  {name:<10} {low:>5} to {high:>5} C, atmosphere: {traits['atmosphere']}")


def spec_options(args):
    """PlanetSpec overrides from the command line."""
    options = {"tilt": args.tilt, "inclination": args.inclination, "rotation": args.rotation,
               "relief": args.relief, "atmosphere_density": args.atmosphere,
               "clouds": args.clouds, "hue": args.hue,
               "cities": args.cities, "moons": args.moons,
               "show_moons": False if args.hide_moons else None}
    if args.light is not None:
        options["light_azimuth"], options["light_elevation"] = args.light
    return options


def save_spin(spec, args):
    background = args.background
    if args.spin_format == "gif" and background == "transparent":
        background = "black"

    def progress(done, total):
        if not args.quiet:
            print(f"\r  rendering spin: {done}/{total} frames", end="", flush=True)

    frames = render_spin(spec, args.size, args.spin, background, progress)
    if not args.quiet:
        print()
    path = os.path.join(args.out, f"{spec.name}-spin.{args.spin_format}")
    return save_animation(frames, path, args.fps)


def main(argv=None):
    args = build_parser().parse_args(argv)

    if args.list_types:
        list_types()
        return 0
    if args.count < 1:
        print("--count must be at least 1", file=sys.stderr)
        return 2
    if args.spin is not None and args.spin < 2:
        print("--spin needs at least 2 frames", file=sys.stderr)
        return 2
    if not 32 <= args.size <= 8192:
        print("--size must be between 32 and 8192", file=sys.stderr)
        return 2

    saved = None
    if args.from_file:
        try:
            with open(args.from_file) as f:
                saved = json.load(f)
        except (OSError, ValueError) as error:
            print(f"Could not read {args.from_file}: {error}", file=sys.stderr)
            return 2
        if args.count != 1 or args.seed is not None:
            print("--from renders one saved planet; drop --count and --seed", file=sys.stderr)
            return 2

    for i in range(args.count):
        # With a fixed seed and a count above 1, step the seed so each planet
        # differs but the whole batch is still reproducible.
        seed = None if args.seed is None else args.seed + i
        overrides = dict(type=args.type, rings=args.rings, **spec_options(args))
        if saved is not None:
            spec = PlanetSpec.from_dict(saved, **overrides)
        else:
            spec = PlanetSpec.random(seed, **overrides)
        image = render_planet(spec, args.size, args.background)
        metadata = spec.to_dict()
        image_path, json_path = save_planet(image, metadata, args.out)
        spin_path = save_spin(spec, args) if args.spin else None

        if args.quiet:
            print(image_path)
        else:
            print(f"{metadata['name']}  ({metadata['type']}, seed {metadata['seed']})")
            print(f"  {metadata['description']}")
            print(f"  image:    {image_path}")
            print(f"  metadata: {json_path}")
            if spin_path:
                print(f"  spin:     {spin_path}")
            if args.count == 1:
                print(json.dumps(metadata, indent=4))

        if args.open and i == args.count - 1:
            open_file(image_path)

    return 0
