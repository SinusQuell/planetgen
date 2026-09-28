"""Saving planets to disk."""

import json
import os
import platform
import subprocess


def save_planet(planet_img, metadata, output_dir="export"):
    """Save the planet image and its metadata. Returns (image_path, json_path)."""
    os.makedirs(output_dir, exist_ok=True)

    name = metadata["name"]
    image_path = os.path.join(output_dir, f"{name}.png")
    json_path = os.path.join(output_dir, f"{name}.json")

    planet_img.save(image_path)

    with open(json_path, "w") as f:
        json.dump(metadata, f, indent=4)

    return image_path, json_path


def open_file(path):
    """Open a file with the system's default viewer. Returns False if that failed."""
    try:
        system = platform.system()
        if system == "Darwin":
            subprocess.run(["open", path], check=False)
        elif system == "Windows":
            os.startfile(path)
        else:
            subprocess.run(["xdg-open", path], check=False)
    except Exception:
        return False
    return True
