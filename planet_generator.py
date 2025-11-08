#!/usr/bin/env python3
"""
Random Planet Generator
Generates procedural planet images with metadata
"""

import random
import math
import json
import os
from PIL import Image, ImageDraw
import numpy as np
from noise import pnoise2


# Define planet types with characteristics
PLANET_TYPES = {
    "lava": {
        "base_color": (255, 80, 0),
        "temperature": (1000, 2000),
        "atmosphere": "thin"
    },
    "barren": {
        "base_color": (180, 140, 100),
        "temperature": (100, 400),
        "atmosphere": "none"
    },
    "ice": {
        "base_color": (200, 240, 255),
        "temperature": (-200, 0),
        "atmosphere": "thin"
    },
    "ocean": {
        "base_color": (0, 80, 200),
        "temperature": (0, 100),
        "atmosphere": "thick"
    },
    "forest": {
        "base_color": (50, 150, 60),
        "temperature": (0, 30),
        "atmosphere": "oxygen-rich"
    },
    "desert": {
        "base_color": (230, 200, 100),
        "temperature": (40, 60),
        "atmosphere": "thin"
    },
    "gas_giant": {
        "base_color": (255, 180, 100),
        "temperature": (-100, 400),
        "atmosphere": "dense"
    },
    "toxic": {
        "base_color": (100, 255, 100),
        "temperature": (100, 600),
        "atmosphere": "poisonous"
    },
    "crystal": {
        "base_color": (180, 255, 255),
        "temperature": (-50, 100),
        "atmosphere": "thin"
    },
    "volcanic": {
        "base_color": (255, 50, 50),
        "temperature": (800, 1500),
        "atmosphere": "sulfurous"
    }
}


def generate_name():
    """Generate a random planet name"""
    prefixes = ["Xen", "Astra", "Nova", "Cryo", "Vul", "Zar", "Terra", "Oph", "Ere", "Quar"]
    suffixes = ["ion", "is", "ar", "os", "ea", "or", "a", "um", "ax", "ex"]
    return random.choice(prefixes) + random.choice(suffixes) + "-" + str(random.randint(1, 999))


def generate_texture(size, base_color, seed):
    """Generate procedural texture using Perlin noise"""
    np.random.seed(seed)
    scale = 50.0
    octaves = 6
    persistence = 0.5
    lacunarity = 2.0
    
    texture = np.zeros((size, size, 3), dtype=np.uint8)
    for y in range(size):
        for x in range(size):
            noise_value = pnoise2(
                x / scale,
                y / scale,
                octaves=octaves,
                persistence=persistence,
                lacunarity=lacunarity,
                repeatx=1024,
                repeaty=1024,
                base=seed
            )
            variation = int(noise_value * 80)
            r = min(255, max(0, base_color[0] + variation))
            g = min(255, max(0, base_color[1] + variation))
            b = min(255, max(0, base_color[2] + variation))
            texture[y, x] = (r, g, b)
    
    return texture


def render_planet_image(size=512):
    """Render a complete planet image with metadata"""
    # Select random planet type
    planet_type = random.choice(list(PLANET_TYPES.keys()))
    traits = PLANET_TYPES[planet_type]
    
    # Generate planet characteristics
    name = generate_name()
    temp_range = traits["temperature"]
    temperature = random.randint(temp_range[0], temp_range[1])
    has_rings = random.random() < 0.2
    has_moons = random.randint(0, 5)
    radius = random.randint(int(size * 0.3), int(size * 0.45))
    
    # Generate texture
    seed = random.randint(0, 10000)
    texture = generate_texture(size, traits["base_color"], seed)
    img = Image.fromarray(texture, "RGB")
    
    # Create circular planet mask
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse(
        (size/2 - radius, size/2 - radius, size/2 + radius, size/2 + radius),
        fill=255
    )
    
    # Apply mask to create planet
    planet = Image.new("RGBA", (size, size))
    planet.paste(img, (0, 0), mask=mask)
    
    # Add lighting effect
    light = Image.new("L", (size, size), 0)
    light_draw = ImageDraw.Draw(light)
    for y in range(size):
        for x in range(size):
            dx = x - size / 3
            dy = y - size / 3
            dist = math.sqrt(dx * dx + dy * dy)
            light_value = max(0, 255 - int(dist * 0.6))
            light_draw.point((x, y), fill=light_value)
    planet.putalpha(light)
    
    # Add rings if applicable
    if has_rings:
        ring_draw = ImageDraw.Draw(planet)
        ring_draw.ellipse(
            (size/2 - radius * 1.2, size/2 - radius * 0.4,
             size/2 + radius * 1.2, size/2 + radius * 0.4),
            outline=(180, 180, 180, 80),
            width=3
        )
    
    # Create metadata
    metadata = {
        "name": name,
        "type": planet_type,
        "temperature": temperature,
        "radius": radius,
        "rings": has_rings,
        "moons": has_moons,
        "atmosphere": traits["atmosphere"],
        "seed": seed
    }
    
    return planet, metadata


def save_planet(planet_img, metadata, output_dir="export"):
    """Save planet image and metadata to files"""
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    name = metadata["name"]
    image_path = os.path.join(output_dir, f"{name}.png")
    json_path = os.path.join(output_dir, f"{name}.json")
    
    # Save image
    planet_img.save(image_path)
    
    # Save metadata
    with open(json_path, "w") as f:
        json.dump(metadata, f, indent=4)
    
    print(f"Saved planet to {image_path}")
    print(f"Saved metadata to {json_path}")


if __name__ == "__main__":
    print("Generating random planet...")
    planet, data = render_planet_image()
    save_planet(planet, data)
    print(f"\nGenerated planet: {data['name']}")
    print(json.dumps(data, indent=4))
