"""Planet type definitions, color ramps and palettes."""

# Optional material keys per type:
#   sea_level      height below which the surface is liquid (flat and glossy)
#   land_specular  how glossy the solid surface is, 0..1 (default 0.04)
PLANET_TYPES = {
    "lava": {
        "base_color": (255, 80, 0),
        "temperature": (1000, 2000),
        "atmosphere": "thin",
        "atmo_color": (255, 100, 20),
        "atmo_strength": 0.3,
        "sea_level": -0.05,
        "land_specular": 0.03,
    },
    "barren": {
        "base_color": (180, 140, 100),
        "temperature": (100, 400),
        "atmosphere": "none",
        "atmo_color": (0, 0, 0),
        "atmo_strength": 0.0,
    },
    "ice": {
        "base_color": (200, 240, 255),
        "temperature": (-200, 0),
        "atmosphere": "thin",
        "atmo_color": (180, 210, 255),
        "atmo_strength": 0.3,
        "land_specular": 0.25,
    },
    "ocean": {
        "base_color": (0, 80, 200),
        "temperature": (0, 100),
        "atmosphere": "thick",
        "atmo_color": (100, 150, 255),
        "atmo_strength": 0.5,
        "sea_level": -0.01,
    },
    "forest": {
        "base_color": (50, 150, 60),
        "temperature": (0, 30),
        "atmosphere": "oxygen-rich",
        "atmo_color": (100, 160, 255),
        "atmo_strength": 0.45,
        "sea_level": -0.05,
    },
    "desert": {
        "base_color": (230, 200, 100),
        "temperature": (40, 60),
        "atmosphere": "thin",
        "atmo_color": (220, 180, 120),
        "atmo_strength": 0.25,
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
    },
    "crystal": {
        "base_color": (180, 255, 255),
        "temperature": (-50, 100),
        "atmosphere": "thin",
        "atmo_color": (160, 230, 255),
        "atmo_strength": 0.3,
        "land_specular": 0.45,
    },
    "volcanic": {
        "base_color": (255, 50, 50),
        "temperature": (800, 1500),
        "atmosphere": "sulfurous",
        "atmo_color": (200, 80, 20),
        "atmo_strength": 0.35,
        "sea_level": -0.05,
        "land_specular": 0.03,
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
GAS_GIANT_PALETTES = [
    # Jupiter-like warm
    [(200, 140, 80), (240, 190, 120), (220, 160, 90), (180, 120, 60), (255, 210, 150)],
    # Saturn-like pale
    [(220, 200, 150), (240, 220, 170), (200, 180, 130), (230, 210, 160), (250, 235, 190)],
    # Blue-gray gas giant
    [(120, 140, 180), (150, 170, 210), (100, 120, 160), (170, 190, 220), (130, 150, 190)],
]
