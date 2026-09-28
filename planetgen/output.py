"""Saving planets to disk."""

import json
import math
import os
import platform
import subprocess

from PIL import Image, ImageDraw, ImageFont


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


def save_animation(frames, path, fps=20):
    """Save frames as an animated GIF or WebP, picked by the file extension.
    GIF has no soft transparency, so give it frames with a background."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    duration = int(round(1000 / fps))
    first, rest = frames[0], frames[1:]
    if path.lower().endswith(".gif"):
        first = first.convert("RGB")
        rest = [f.convert("RGB") for f in rest]
        first.save(path, save_all=True, append_images=rest, duration=duration, loop=0,
                   optimize=False)
    else:
        first.save(path, save_all=True, append_images=rest, duration=duration, loop=0,
                   quality=90)
    return path


def contact_sheet(images, labels, cell=256, columns=None):
    """Lay planets out in a labelled grid on a dark background."""
    count = len(images)
    columns = columns or min(count, max(1, math.ceil(math.sqrt(count))))
    rows = math.ceil(count / columns)
    label_height = max(18, cell // 10)
    sheet = Image.new("RGBA", (columns * cell, rows * (cell + label_height)), (10, 11, 18, 255))
    draw = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.load_default(size=max(10, label_height * 2 // 3))
    except TypeError:  # Pillow before 10.1 has only the fixed bitmap font
        font = ImageFont.load_default()

    for i, (image, label) in enumerate(zip(images, labels)):
        x = (i % columns) * cell
        y = (i // columns) * (cell + label_height)
        sheet.alpha_composite(image.resize((cell, cell), Image.LANCZOS), (x, y))
        width = draw.textlength(label, font=font)
        draw.text((x + (cell - width) / 2, y + cell), label, fill=(200, 205, 220), font=font)
    return sheet


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
