"""Planet type definitions, color ramps and palettes."""

# Optional material keys per type:
#   sea_level      height below which the surface is liquid (flat and glossy)
#   land_specular  how glossy the solid surface is, 0..1 (default 0.04)
#   glow           color the liquid gives off, visible on the night side
#   ice_caps       polar ice that grows as the planet gets colder
#   craters        how many impact craters to scatter over the surface
#   terrain        height field style, see surface.terrain_height (default rolling)
PLANET_TYPES = {
    "lava": {
        "base_color": (255, 80, 0),
        "temperature": (1000, 2000),
        "atmosphere": "thin",
        "atmo_color": (255, 100, 20),
        "atmo_strength": 0.3,
        "sea_level": -0.05,
        "land_specular": 0.03,
        "terrain": "cracked",
        "glow": (255, 120, 30),
    },
    "barren": {
        "base_color": (180, 140, 100),
        "temperature": (100, 400),
        "atmosphere": "none",
        "atmo_color": (0, 0, 0),
        "atmo_strength": 0.0,
        "craters": 140,
    },
    "ice": {
        "base_color": (200, 240, 255),
        "temperature": (-200, 0),
        "atmosphere": "thin",
        "atmo_color": (180, 210, 255),
        "atmo_strength": 0.3,
        "land_specular": 0.25,
        "craters": 45,
    },
    "ocean": {
        "base_color": (0, 80, 200),
        "temperature": (0, 100),
        "atmosphere": "thick",
        "atmo_color": (100, 150, 255),
        "atmo_strength": 0.5,
        "sea_level": -0.01,
        "terrain": "continents",
        "ice_caps": True,
    },
    "forest": {
        "base_color": (50, 150, 60),
        "temperature": (0, 30),
        "atmosphere": "oxygen-rich",
        "atmo_color": (100, 160, 255),
        "atmo_strength": 0.45,
        "sea_level": -0.05,
        "terrain": "continents",
        "ice_caps": True,
    },
    "desert": {
        "base_color": (230, 200, 100),
        "temperature": (40, 60),
        "atmosphere": "thin",
        "atmo_color": (220, 180, 120),
        "atmo_strength": 0.25,
        "ice_caps": True,
        "craters": 12,
    },
    "gas_giant": {
        "base_color": (255, 180, 100),
        "temperature": (-100, 400),
        "atmosphere": "dense",
        "atmo_color": (200, 160, 100),
        "atmo_strength": 0.5,
        "land_specular": 0.06,
    },
    "toxic": {
        "base_color": (100, 255, 100),
        "temperature": (100, 600),
        "atmosphere": "poisonous",
        "atmo_color": (120, 220, 80),
        "atmo_strength": 0.4,
        "sea_level": -0.05,
        "terrain": "cracked",
        "glow": (60, 190, 45),
    },
    "crystal": {
        "base_color": (180, 255, 255),
        "temperature": (-50, 100),
        "atmosphere": "thin",
        "atmo_color": (160, 230, 255),
        "atmo_strength": 0.3,
        "land_specular": 0.45,
        "craters": 20,
    },
    "volcanic": {
        "base_color": (255, 50, 50),
        "temperature": (800, 1500),
        "atmosphere": "sulfurous",
        "atmo_color": (200, 80, 20),
        "atmo_strength": 0.35,
        "sea_level": -0.05,
        "land_specular": 0.03,
        "terrain": "cracked",
        "glow": (255, 90, 20),
    },
}

# Color ramps: list of (height_threshold, (r, g, b)) for smooth interpolation
COLOR_RAMPS = {
    "ocean": [
        (-1.0, (0, 25, 80)),
        (-0.25, (0, 40, 120)),
        (-0.08, (0, 80, 180)),
        (-0.02, (30, 120, 200)),
        (0.0, (210, 195, 140)),
        (0.05, (80, 150, 60)),
        (0.25, (60, 130, 50)),
        (0.45, (150, 145, 135)),
        (0.7, (200, 200, 200)),
        (1.0, (250, 250, 255)),
    ],
    "forest": [
        (-1.0, (20, 50, 120)),
        (-0.15, (30, 80, 150)),
        (-0.05, (35, 90, 60)),
        (0.0, (40, 100, 50)),
        (0.15, (50, 140, 55)),
        (0.30, (70, 160, 60)),
        (0.45, (90, 130, 70)),
        (0.6, (130, 120, 100)),
        (1.0, (180, 175, 170)),
    ],
    "lava": [
        (-1.0, (255, 120, 0)),
        (-0.15, (255, 90, 0)),
        (-0.05, (220, 50, 0)),
        (0.05, (180, 40, 0)),
        (0.2, (100, 25, 0)),
        (0.5, (40, 15, 5)),
        (1.0, (20, 8, 2)),
    ],
    "volcanic": [
        (-1.0, (255, 100, 20)),
        (-0.25, (255, 70, 15)),
        (-0.05, (180, 35, 10)),
        (0.05, (140, 30, 10)),
        (0.3, (60, 20, 10)),
        (0.6, (40, 18, 8)),
        (1.0, (25, 12, 5)),
    ],
    "ice": [
        (-1.0, (160, 185, 240)),
        (-0.15, (180, 200, 250)),
        (0.0, (210, 225, 255)),
        (0.2, (230, 240, 255)),
        (0.5, (245, 248, 255)),
        (1.0, (255, 255, 255)),
    ],
    "desert": [
        (-1.0, (140, 110, 60)),
        (-0.2, (160, 130, 75)),
        (0.0, (200, 175, 95)),
        (0.2, (225, 200, 110)),
        (0.4, (240, 215, 130)),
        (0.7, (180, 145, 90)),
        (1.0, (150, 120, 80)),
    ],
    "barren": [
        (-1.0, (100, 80, 60)),
        (-0.2, (130, 105, 80)),
        (0.0, (165, 135, 100)),
        (0.2, (185, 150, 110)),
        (0.5, (200, 165, 120)),
        (1.0, (140, 110, 80)),
    ],
    "toxic": [
        (-1.0, (60, 220, 80)),
        (-0.1, (80, 255, 100)),
        (0.0, (70, 200, 90)),
        (0.2, (60, 180, 80)),
        (0.5, (90, 160, 70)),
        (1.0, (50, 130, 50)),
    ],
    "crystal": [
        (-1.0, (140, 220, 240)),
        (-0.1, (160, 240, 255)),
        (0.1, (180, 255, 255)),
        (0.3, (200, 255, 250)),
        (0.6, (170, 235, 245)),
        (1.0, (150, 220, 240)),
    ],
}

# Gas giant band color palettes (warm and cool variants)
# Gas giant palettes: light "zones" and darker "belts" alternate in bands,
# storms take the storm color.
GAS_GIANT_PALETTES = [
    {   # Jupiter-like warm
        "zones": [(236, 222, 196), (245, 232, 205), (228, 208, 172)],
        "belts": [(176, 118, 72), (196, 142, 94), (150, 100, 66), (210, 170, 120)],
        "storm": (196, 92, 56),
    },
    {   # Saturn-like pale gold
        "zones": [(240, 222, 170), (248, 234, 190), (232, 212, 158)],
        "belts": [(206, 176, 118), (218, 190, 134), (190, 160, 108)],
        "storm": (250, 240, 214),
    },
    {   # Neptune-like deep blue
        "zones": [(96, 140, 222), (110, 156, 232), (84, 124, 206)],
        "belts": [(52, 84, 170), (64, 100, 188), (44, 70, 150)],
        "storm": (28, 44, 110),
    },
    {   # Hot, dark violet
        "zones": [(170, 128, 170), (186, 146, 180), (156, 116, 160)],
        "belts": [(100, 62, 110), (122, 78, 124), (86, 52, 96)],
        "storm": (230, 190, 214),
    },
    {   # Teal and cream
        "zones": [(214, 228, 212), (226, 236, 220), (200, 218, 204)],
        "belts": [(96, 150, 150), (116, 166, 160), (80, 130, 136)],
        "storm": (240, 246, 236),
    },
    {   # Rusty orange
        "zones": [(238, 196, 150), (246, 210, 168), (230, 184, 136)],
        "belts": [(190, 100, 58), (170, 84, 48), (206, 122, 72)],
        "storm": (250, 232, 200),
    },
]
