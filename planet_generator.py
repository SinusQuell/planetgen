#!/usr/bin/env python3
"""
Random Planet Generator
Generates procedural planet images with metadata
"""

import json

from planetgen import render_planet_image, save_planet


if __name__ == "__main__":
    print("Generating random planet...")
    planet, data = render_planet_image()
    save_planet(planet, data)
    print(f"\nGenerated planet: {data['name']}")
    print(json.dumps(data, indent=4))
