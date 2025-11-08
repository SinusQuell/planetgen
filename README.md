# 🪐 Random Planet Generator (Python)

This project generates a **512×512 pixel image of a random planet** using procedural noise and random parameters. It produces both an image (`.png`) and metadata (`.json`) describing the planet.

---

## ⚙️ Features

- Procedural **Perlin noise-based texture**
- **10 planet types**: lava, barren, ice, ocean, forest, desert, gas giant, toxic, crystal, volcanic
- Stats like **temperature, radius, moons, rings, atmosphere, size etc.**
- Automatic **planet name generation**
- Exports both `.png` and `.json` files with stats into `/export`

---

## 🧰 Requirements

Install dependencies:

```bash
pip install pillow numpy noise
```

Optional:
- `matplotlib` (for previewing)
- `json` (built-in)

---

## 🚀 Usage

Run the planet generator:

```bash
python planet_generator.py
```

This will:
1. Generate a random planet with unique characteristics
2. Create an `export/` directory (if it doesn't exist)
3. Save a PNG image of the planet
4. Save a JSON file with planet metadata
5. Print the planet details to the console

---

## 🧩 Project Structure

```
.
├── planet_generator.py   # Main generator script
├── README.md            # This file
└── export/              # Generated planets (created automatically)
    ├── PlanetName-123.png
    └── PlanetName-123.json
```

---

## 🧠 How It Works

### 1. Define Planet Types

Each planet type has a base color, temperature range, and atmospheric type:

```python
PLANET_TYPES = {
    "lava": {"base_color": (255, 80, 0), "temperature": (1000, 2000), "atmosphere": "thin"},
    "barren": {"base_color": (180, 140, 100), "temperature": (100, 400), "atmosphere": "none"},
    "ice": {"base_color": (200, 240, 255), "temperature": (-200, 0), "atmosphere": "thin"},
    "ocean": {"base_color": (0, 80, 200), "temperature": (0, 100), "atmosphere": "thick"},
    "forest": {"base_color": (50, 150, 60), "temperature": (0, 30), "atmosphere": "oxygen-rich"},
    "desert": {"base_color": (230, 200, 100), "temperature": (40, 60), "atmosphere": "thin"},
    "gas_giant": {"base_color": (255, 180, 100), "temperature": (-100, 400), "atmosphere": "dense"},
    "toxic": {"base_color": (100, 255, 100), "temperature": (100, 600), "atmosphere": "poisonous"},
    "crystal": {"base_color": (180, 255, 255), "temperature": (-50, 100), "atmosphere": "thin"},
    "volcanic": {"base_color": (255, 50, 50), "temperature": (800, 1500), "atmosphere": "sulfurous"}
}
```

### 2. Generate Random Planet Names

Creates unique names using prefixes and suffixes:

```python
def generate_name():
    prefixes = ["Xen", "Astra", "Nova", "Cryo", "Vul", "Zar", "Terra", "Oph", "Ere", "Quar"]
    suffixes = ["ion", "is", "ar", "os", "ea", "or", "a", "um", "ax", "ex"]
    return random.choice(prefixes) + random.choice(suffixes) + "-" + str(random.randint(1, 999))
```

### 3. Create Procedural Texture

Uses Perlin noise to generate natural-looking planetary surfaces:

- **Scale**: Controls the zoom level of noise patterns
- **Octaves**: Number of noise layers for detail
- **Persistence**: How much each octave contributes
- **Lacunarity**: Frequency multiplier between octaves

### 4. Render the Planet

The rendering process:
1. Select a random planet type
2. Generate procedural texture
3. Apply circular masking
4. Add lighting effects
5. Optionally add rings (20% chance)
6. Generate metadata

### 5. Save Output

Saves both image and metadata to the `export/` directory:
- `{PlanetName}.png` - Planet image
- `{PlanetName}.json` - Planet metadata

---

## 🧮 Example Output

### Metadata (JSON)

```json
{
    "name": "Astraea-742",
    "type": "lava",
    "temperature": 1573,
    "radius": 205,
    "rings": true,
    "moons": 2,
    "atmosphere": "thin",
    "seed": 2375
}
```

### Planet Types

Each planet type has unique characteristics:

- **Lava**: Red-orange, extremely hot (1000-2000°C)
- **Barren**: Brown-tan, moderate temperature (100-400°C)
- **Ice**: Light blue, freezing cold (-200-0°C)
- **Ocean**: Deep blue, temperate (0-100°C)
- **Forest**: Green, habitable range (0-30°C)
- **Desert**: Sandy yellow, warm (40-60°C)
- **Gas Giant**: Orange-yellow, variable (-100-400°C)
- **Toxic**: Bright green, hot (100-600°C)
- **Crystal**: Cyan, cool (-50-100°C)
- **Volcanic**: Bright red, very hot (800-1500°C)

---

## 🎨 Customization

You can modify the planet generator by:

1. **Adding new planet types**: Add entries to the `PLANET_TYPES` dictionary
2. **Adjusting texture parameters**: Modify `scale`, `octaves`, `persistence` in `generate_texture()`
3. **Changing image size**: Pass a different `size` parameter to `render_planet_image()`
4. **Customizing names**: Add more prefixes/suffixes to `generate_name()`

---

## 📝 License

This project is open source and available for educational purposes.

---

## 🤝 Contributing

Feel free to fork, modify, and submit pull requests to improve the planet generator!
