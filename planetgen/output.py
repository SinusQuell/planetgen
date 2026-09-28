"""Saving planets to disk."""

import json
import os
import platform
import subprocess


def save_planet(planet_img, metadata, output_dir="export"):
    """Save planet image and metadata to files."""
    os.makedirs(output_dir, exist_ok=True)

    name = metadata["name"]
    image_path = os.path.join(output_dir, f"{name}.png")
    json_path = os.path.join(output_dir, f"{name}.json")

    planet_img.save(image_path)

    with open(json_path, "w") as f:
        json.dump(metadata, f, indent=4)

    print(f"Saved planet to {image_path}")
    print(f"Saved metadata to {json_path}")

    try:
        system = platform.system()
        if system == "Darwin":
            subprocess.run(["open", image_path], check=False)
        elif system == "Windows":
            os.startfile(image_path)
        elif system == "Linux":
            subprocess.run(["xdg-open", image_path], check=False)
        print(f"Opening {image_path}...")
    except Exception as e:
        print(f"Could not auto-open image: {e}")
