#!/usr/bin/env python3
"""
Random Planet Generator
Generates procedural planet images with metadata
"""

import random
import math
import json
import os
import platform
import subprocess
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
    prefixes = ["Xen", "Astra", "Nova", "Cryo", "Vul", "Zar", "Terra", "Oph", "Ere", "Quar",
                "Kel", "Dra", "Nyx", "Sol", "Lun", "Stel", "Gal", "Neb", "Cos", "Ori",
                "Pyr", "Aqua", "Aero", "Geo", "Chron", "Helio", "Thanat", "Hyper", "Proto", "Neo"]
    suffixes = ["ion", "is", "ar", "os", "ea", "or", "a", "um", "ax", "ex",
                "ius", "eon", "yx", "ia", "us", "on", "an", "el", "al", "en",
                "ith", "eth", "oth", "ir", "ur", "ys", "ix", "ox", "yn", "ria"]
    
    base_name = random.choice(prefixes) + random.choice(suffixes)
    
    # 30% chance to add a secondary designation
    if random.random() < 0.3:
        secondary = random.choice([
            " Prime", " Alpha", " Beta", " Gamma", " Delta", " Epsilon",
            " I", " II", " III", " IV", " V", " VI", " VII", " VIII", " IX", " X",
            " Major", " Minor", " Omega", " Sigma", " Tau"
        ])
        base_name += secondary
    
    return base_name + "-" + str(random.randint(1, 999))


def generate_texture(size, base_color, seed, planet_type):
    """Generate procedural texture using Perlin noise with layered details"""
    np.random.seed(seed)
    scale = 40.0
    octaves = 8
    persistence = 0.55
    lacunarity = 2.2
    
    texture = np.zeros((size, size, 3), dtype=np.uint8)
    
    # Generate base elevation/terrain layer
    for y in range(size):
        for x in range(size):
            # Primary terrain noise
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
            
            # Secondary detail noise for fine features
            detail_noise = pnoise2(
                x / (scale * 0.3),
                y / (scale * 0.3),
                octaves=4,
                persistence=0.4,
                lacunarity=2.5,
                repeatx=1024,
                repeaty=1024,
                base=seed + 100
            )
            
            # Combine noises
            combined_noise = noise_value * 0.7 + detail_noise * 0.3
            
            # Apply different effects based on planet type
            if planet_type in ["ocean", "forest"]:
                # Water/land distinction
                if combined_noise < -0.1:
                    # Ocean areas - darker blue
                    variation = int(combined_noise * 60)
                    r = min(255, max(0, int(base_color[0] * 0.4) + variation))
                    g = min(255, max(0, int(base_color[1] * 0.6) + variation))
                    b = min(255, max(0, int(base_color[2] * 1.2) + variation))
                else:
                    # Land areas
                    variation = int(combined_noise * 100)
                    if planet_type == "forest":
                        r = min(255, max(0, base_color[0] + variation))
                        g = min(255, max(0, base_color[1] + variation))
                        b = min(255, max(0, int(base_color[2] * 0.7) + variation))
                    else:
                        r = min(255, max(0, int(base_color[0] * 1.5) + variation))
                        g = min(255, max(0, int(base_color[1] * 1.3) + variation))
                        b = min(255, max(0, base_color[2] + variation))
            else:
                # Other planet types - enhanced variation
                variation = int(combined_noise * 120)
                r = min(255, max(0, base_color[0] + variation))
                g = min(255, max(0, base_color[1] + variation))
                b = min(255, max(0, base_color[2] + variation))
            
            texture[y, x] = (r, g, b)
    
    # Add cloud layer for suitable planets
    if planet_type in ["ocean", "forest", "ice"]:
        cloud_scale = 80.0
        for y in range(size):
            for x in range(size):
                cloud_noise = pnoise2(
                    x / cloud_scale,
                    y / cloud_scale,
                    octaves=4,
                    persistence=0.5,
                    lacunarity=2.0,
                    repeatx=1024,
                    repeaty=1024,
                    base=seed + 500
                )
                # Add white clouds where noise is high
                if cloud_noise > 0.3:
                    cloud_intensity = int((cloud_noise - 0.3) * 400)
                    texture[y, x] = (
                        min(255, texture[y, x][0] + cloud_intensity),
                        min(255, texture[y, x][1] + cloud_intensity),
                        min(255, texture[y, x][2] + cloud_intensity)
                    )
    
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
    
    # Make planets with rings larger to accommodate the rings
    if has_rings:
        radius = random.randint(int(size * 0.25), int(size * 0.35))
    else:
        radius = random.randint(int(size * 0.3), int(size * 0.45))
    
    # Generate texture
    seed = random.randint(0, 10000)
    texture = generate_texture(size, traits["base_color"], seed, planet_type)
    img = Image.fromarray(texture, "RGB")
    
    # Create circular planet mask
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse(
        (size/2 - radius, size/2 - radius, size/2 + radius, size/2 + radius),
        fill=255
    )
    
    # Apply mask to create planet with transparent background
    planet = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    
    # Convert to numpy for faster processing
    img_array = np.array(img)
    mask_array = np.array(mask)
    planet_array = np.zeros((size, size, 4), dtype=np.uint8)
    
    center_x = size / 2
    center_y = size / 2
    
    # Apply texture and full opacity where mask is active
    for y in range(size):
        for x in range(size):
            if mask_array[y, x] > 0:
                # Set RGB from texture
                planet_array[y, x, 0:3] = img_array[y, x]
                
                # Add subtle edge darkening for 3D effect
                dx = x - center_x
                dy = y - center_y
                dist_from_center = math.sqrt(dx * dx + dy * dy)
                edge_factor = dist_from_center / radius
                
                if edge_factor > 0.75:
                    # Darken edges slightly
                    darken = int((edge_factor - 0.75) * 180)
                    planet_array[y, x, 0] = max(0, planet_array[y, x, 0] - darken)
                    planet_array[y, x, 1] = max(0, planet_array[y, x, 1] - darken)
                    planet_array[y, x, 2] = max(0, planet_array[y, x, 2] - darken)
                
                # Set full opacity for planet surface
                planet_array[y, x, 3] = 255
    
    planet = Image.fromarray(planet_array, 'RGBA')
    
    # Add rings if applicable
    if has_rings:
        # Create a separate layer for rings to avoid transparency issues
        ring_layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        ring_draw = ImageDraw.Draw(ring_layer)
        
        # Ring colors with variations
        ring_colors = [
            (220, 200, 180, 200),
            (200, 180, 160, 210),
            (240, 220, 200, 190),
            (210, 190, 170, 200),
            (190, 170, 150, 210),
            (230, 210, 190, 195)
        ]
        
        ring_inner_radius = radius * 1.4
        ring_outer_radius = radius * 2.0
        num_ring_bands = 20  # Draw multiple ring bands for thickness
        
        for i in range(num_ring_bands):
            # Calculate ring position with slight variations
            progress = i / num_ring_bands
            ring_radius = ring_inner_radius + (ring_outer_radius - ring_inner_radius) * progress
            ring_color = ring_colors[i % len(ring_colors)]
            
            # Draw thick ring band
            ring_draw.ellipse(
                (center_x - ring_radius, center_y - ring_radius * 0.25,
                 center_x + ring_radius, center_y + ring_radius * 0.25),
                outline=ring_color,
                width=10
            )
        
        # Composite rings over planet
        planet = Image.alpha_composite(planet, ring_layer)
    
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
    
    # Open the image automatically
    try:
        system = platform.system()
        if system == "Darwin":  # macOS
            subprocess.run(["open", image_path], check=False)
        elif system == "Windows":
            os.startfile(image_path)
        elif system == "Linux":
            subprocess.run(["xdg-open", image_path], check=False)
        print(f"Opening {image_path}...")
    except Exception as e:
        print(f"Could not auto-open image: {e}")


if __name__ == "__main__":
    print("Generating random planet...")
    planet, data = render_planet_image()
    save_planet(planet, data)
    print(f"\nGenerated planet: {data['name']}")
    print(json.dumps(data, indent=4))
