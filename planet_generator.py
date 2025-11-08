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
from noise import pnoise2, pnoise3


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
    """Generate procedural texture using equirectangular UV mapping on sphere"""
    np.random.seed(seed)
    
    texture = np.zeros((size, size, 3), dtype=np.uint8)
    center = size / 2
    radius = center
    
    # Generate elevation map using proper UV texture mapping
    for y in range(size):
        for x in range(size):
            # Calculate position relative to center
            dx = x - center
            dy = y - center
            dist = math.sqrt(dx * dx + dy * dy)
            
            # Skip if outside circle
            if dist > radius:
                continue
            
            # Normalize coordinates to [-1, 1]
            nx = dx / radius
            ny = dy / radius
            
            # Calculate depth (z) on the sphere surface
            # For a sphere: x^2 + y^2 + z^2 = 1
            z_squared = 1.0 - (nx * nx + ny * ny)
            if z_squared < 0:
                continue
            nz = math.sqrt(z_squared)
            
            # Use 3D noise sampling on the sphere surface
            # This eliminates seams and vertical line artifacts
            # by sampling a continuous 3D noise field
            scale = 3.0
            
            # Base elevation noise - large scale terrain
            # Sample directly at the 3D point on sphere surface
            elevation = pnoise3(
                nx * scale,
                ny * scale,
                nz * scale,
                octaves=6,
                persistence=0.5,
                lacunarity=2.0,
                base=seed
            )
            
            # Detail noise - small scale features
            detail_scale = 8.0
            detail = pnoise3(
                nx * detail_scale,
                ny * detail_scale,
                nz * detail_scale,
                octaves=4,
                persistence=0.6,
                lacunarity=2.5,
                base=seed + 50
            ) * 0.3
            
            # Combine elevation and detail
            height = elevation + detail
            
            # For rendering, we still need UV coordinates for certain effects
            u = 0.5 + math.atan2(nx, nz) / (2 * math.pi)
            v = 0.5 - math.asin(ny) / math.pi
            
            # Apply planet-type-specific rendering
            r, g, b = render_planet_surface(height, planet_type, base_color, u, v, seed)
            texture[y, x] = (r, g, b)
    
    # Add cloud layer for suitable planets
    if planet_type in ["ocean", "forest", "ice", "desert"]:
        add_cloud_layer(texture, size, seed)
    
    return texture


def render_planet_surface(height, planet_type, base_color, u, v, seed):
    """Render surface color based on height and planet type"""
    
    if planet_type == "ocean":
        # Ocean world with water, beaches, and land
        if height < -0.2:
            # Deep ocean - dark blue
            return (0, 40, 120)
        elif height < -0.05:
            # Shallow ocean - lighter blue
            return (0, 80, 180)
        elif height < 0.0:
            # Beach - sandy
            return (220, 200, 140)
        elif height < 0.3:
            # Lowland - green
            variation = int(height * 80)
            return (60 + variation, 140 + variation, 70)
        else:
            # Mountains - gray/white
            rock_color = int(150 + height * 100)
            return (rock_color, rock_color, rock_color)
    
    elif planet_type == "forest":
        # Forest world with varied green terrain
        if height < -0.1:
            # Water bodies - blue
            return (30, 80, 150)
        elif height < 0.0:
            # Wetlands - dark green
            return (40, 100, 50)
        elif height < 0.4:
            # Forest - multiple shades of green
            green_var = int(height * 150)
            return (30 + green_var, 120 + green_var, 40 + green_var)
        else:
            # Mountain peaks - gray/brown
            return (120, 110, 100)
    
    elif planet_type == "lava":
        # Lava world with molten rock and dark crust
        if height < -0.1:
            # Lava pools - bright orange/red
            return (255, 100, 0)
        elif height < 0.1:
            # Hot crust - dark red
            return (180, 40, 0)
        else:
            # Cooled rock - very dark brown/black
            dark = int(20 + height * 40)
            return (dark, dark // 2, 0)
    
    elif planet_type == "volcanic":
        # Volcanic world - similar to lava but more rock
        if height < -0.2:
            # Lava - bright
            return (255, 80, 20)
        elif height < 0.0:
            # Recent lava - dark red
            return (140, 30, 10)
        else:
            # Volcanic rock - black/dark gray
            rock = int(40 + height * 60)
            return (rock, rock // 2, rock // 4)
    
    elif planet_type == "ice":
        # Ice world with varied ice and snow
        if height < -0.1:
            # Deep ice - blue tint
            return (180, 200, 255)
        elif height < 0.2:
            # Ice plains - white with blue
            ice_var = int(height * 40)
            return (220 + ice_var, 230 + ice_var, 255)
        else:
            # Ice mountains - pure white
            return (250, 250, 255)
    
    elif planet_type == "desert":
        # Desert world with sand and rock
        if height < -0.15:
            # Oasis/dry lake - darker
            return (160, 130, 80)
        elif height < 0.3:
            # Sand dunes - yellow/tan
            sand_var = int(height * 60)
            return (210 + sand_var, 180 + sand_var, 100 + sand_var)
        else:
            # Rocky outcrops - brown
            return (150, 120, 80)
    
    elif planet_type == "barren":
        # Barren rocky world
        variation = int(height * 100)
        return (
            min(255, max(0, base_color[0] + variation)),
            min(255, max(0, base_color[1] + variation)),
            min(255, max(0, base_color[2] + variation))
        )
    
    elif planet_type == "gas_giant":
        # Gas giant with bands (horizontal bands using v coordinate)
        band_noise = pnoise2(u * 4, v * 0.5, octaves=3, base=seed + 200)
        variation = int(band_noise * 100)
        return (
            min(255, max(0, base_color[0] + variation)),
            min(255, max(0, base_color[1] + variation)),
            min(255, max(0, base_color[2] + variation))
        )
    
    elif planet_type == "toxic":
        # Toxic world with varied green
        if height < 0.0:
            # Toxic pools
            return (80, 255, 100)
        else:
            # Toxic land
            variation = int(height * 80)
            return (
                min(255, max(0, 60 + variation)),
                min(255, max(0, 200 + variation)),
                min(255, max(0, 80 + variation))
            )
    
    elif planet_type == "crystal":
        # Crystal world with shimmering colors
        variation = int(height * 100)
        return (
            min(255, max(0, 160 + variation)),
            min(255, max(0, 230 + variation)),
            min(255, max(0, 250 + variation))
        )
    
    else:
        # Default rendering
        variation = int(height * 100)
        return (
            min(255, max(0, base_color[0] + variation)),
            min(255, max(0, base_color[1] + variation)),
            min(255, max(0, base_color[2] + variation))
        )


def add_cloud_layer(texture, size, seed):
    """Add clouds to the texture using side-view projection"""
    center = size / 2
    radius = center
    
    for y in range(size):
        for x in range(size):
            dx = x - center
            dy = y - center
            dist = math.sqrt(dx * dx + dy * dy)
            
            if dist > radius:
                continue
            
            # Use same UV mapping as terrain
            nx = dx / radius
            ny = dy / radius
            
            z_squared = 1.0 - (nx * nx + ny * ny)
            if z_squared < 0:
                continue
            nz = math.sqrt(z_squared)
            
            # Use 3D noise for clouds to avoid seams
            cloud_scale = 4.0
            cloud_noise = pnoise3(
                nx * cloud_scale,
                ny * cloud_scale,
                nz * cloud_scale,
                octaves=4,
                persistence=0.5,
                lacunarity=2.0,
                base=seed + 500
            )
            
            # Add white clouds where noise is high
            if cloud_noise > 0.2:
                cloud_intensity = int((cloud_noise - 0.2) * 300)
                texture[y, x] = (
                    min(255, int(texture[y, x][0]) + cloud_intensity),
                    min(255, int(texture[y, x][1]) + cloud_intensity),
                    min(255, int(texture[y, x][2]) + cloud_intensity)
                )


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
    
    # Apply texture and full opacity where mask is active
    # Keep it clean - no shadows, no glows, just the planet texture
    for y in range(size):
        for x in range(size):
            if mask_array[y, x] > 0:
                # Set RGB from texture
                planet_array[y, x, 0:3] = img_array[y, x]
                # Set full opacity for planet surface
                planet_array[y, x, 3] = 255
    
    # Add rings if applicable - must do BEFORE converting to RGBA to layer properly
    if has_rings:
        center_x = size / 2
        center_y = size / 2
        
        # Create back ring layer (behind planet)
        back_ring_layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        back_ring_draw = ImageDraw.Draw(back_ring_layer)
        
        # Create front ring layer (in front of planet)
        front_ring_layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        front_ring_draw = ImageDraw.Draw(front_ring_layer)
        
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
        num_ring_bands = 20
        
        # Draw rings
        for i in range(num_ring_bands):
            progress = i / num_ring_bands
            ring_radius = ring_inner_radius + (ring_outer_radius - ring_inner_radius) * progress
            ring_color = ring_colors[i % len(ring_colors)]
            
            # For back rings: draw bottom half only (behind planet)
            # Create a mask for bottom half
            for draw_layer, y_range in [(back_ring_draw, (center_y, size)), (front_ring_draw, (0, center_y))]:
                # Draw full ring
                draw_layer.ellipse(
                    (center_x - ring_radius, center_y - ring_radius * 0.25,
                     center_x + ring_radius, center_y + ring_radius * 0.25),
                    outline=ring_color,
                    width=10
                )
        
        # Mask the back rings to only show TOP half (behind planet - upper/far side)
        back_ring_array = np.array(back_ring_layer)
        for y in range(int(center_y), size):
            back_ring_array[y, :, 3] = 0  # Make bottom half transparent
        back_ring_layer = Image.fromarray(back_ring_array, 'RGBA')
        
        # Mask the front rings to only show BOTTOM half (in front of planet - lower/near side)
        front_ring_array = np.array(front_ring_layer)
        for y in range(int(center_y)):
            front_ring_array[y, :, 3] = 0  # Make top half transparent
        front_ring_layer = Image.fromarray(front_ring_array, 'RGBA')
        
        # Composite: back rings, then planet, then front rings
        final_image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        final_image = Image.alpha_composite(final_image, back_ring_layer)
        
        planet = Image.fromarray(planet_array, 'RGBA')
        final_image = Image.alpha_composite(final_image, planet)
        final_image = Image.alpha_composite(final_image, front_ring_layer)
        
        planet = final_image
    else:
        planet = Image.fromarray(planet_array, 'RGBA')
    
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
