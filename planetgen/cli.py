"""Command line interface."""

import argparse
import json
import sys

from .output import open_file, save_planet
from .render import render_planet_image
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
    parser.add_argument("--clouds", type=float, metavar="COVER",
                        help="cloud cover from 0 to 1 (types without weather ignore it)")
    parser.add_argument("--atmosphere", type=float, metavar="DENSITY",
                        help="atmosphere thickness multiplier (default 1, 0 = none)")
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
               "clouds": args.clouds}
    if args.light is not None:
        options["light_azimuth"], options["light_elevation"] = args.light
    return options


def main(argv=None):
    args = build_parser().parse_args(argv)

    if args.list_types:
        list_types()
        return 0
    if args.count < 1:
        print("--count must be at least 1", file=sys.stderr)
        return 2
    if not 32 <= args.size <= 8192:
        print("--size must be between 32 and 8192", file=sys.stderr)
        return 2

    for i in range(args.count):
        # With a fixed seed and a count above 1, step the seed so each planet
        # differs but the whole batch is still reproducible.
        seed = None if args.seed is None else args.seed + i
        image, metadata = render_planet_image(
            size=args.size, seed=seed, planet_type=args.type, rings=args.rings,
            **spec_options(args),
        )
        image_path, json_path = save_planet(image, metadata, args.out)

        if args.quiet:
            print(image_path)
        else:
            print(f"{metadata['name']}  ({metadata['type']}, seed {metadata['seed']})")
            print(f"  image:    {image_path}")
            print(f"  metadata: {json_path}")
            if args.count == 1:
                print(json.dumps(metadata, indent=4))

        if args.open and i == args.count - 1:
            open_file(image_path)

    return 0
