"""Planet type definitions, color ramps and palettes."""

# Optional material keys per type:
#   sea_level      height below which the surface is liquid (flat and glossy)
#   land_specular  how glossy the solid surface is, 0..1 (default 0.04)
#   glow           color the liquid gives off, visible on the night side
#   ice_caps       polar ice that grows as the planet gets colder; the value
#                  is the temperature (°C) at which it reaches about 45°
#   craters        how many impact craters to scatter over the surface
#   banded         a giant planet: bands and storms instead of terrain, using
#                  the named set in BAND_PALETTES
#   clouds         range the cloud coverage (0..1) is rolled from
#   cloud_color    color of the cloud tops
#   cities         chance that the planet is inhabited and shows city lights
#   terrain        height field style, see surface.terrain_height (default rolling)
PLANET_TYPES = {
    "lava": {
        "temperature": (1000, 2000),
        "atmosphere": "thin",
        "atmo_color": (255, 100, 20),
        "atmo_strength": 0.3,
        "sea_level": -0.05,
        "land_specular": 0.03,
        "terrain": "cracked",
        "glow": (255, 120, 30),
        "clouds": (0.0, 0.15), "cloud_color": (84, 74, 68),
    },
    "barren": {
        "temperature": (100, 400),
        "atmosphere": "none",
        "atmo_color": (0, 0, 0),
        "atmo_strength": 0.0,
        "craters": 140,
    },
    "ice": {
        "temperature": (-200, 0),
        "atmosphere": "thin",
        "atmo_color": (180, 210, 255),
        "atmo_strength": 0.3,
        "land_specular": 0.25,
        "craters": 45,
        "clouds": (0.1, 0.35), "cloud_color": (235, 242, 255),
    },
    "ocean": {
        "temperature": (0, 100),
        "atmosphere": "thick",
        "atmo_color": (100, 150, 255),
        "atmo_strength": 0.5,
        "sea_level": -0.01,
        "terrain": "continents",
        "ice_caps": 0,
        "clouds": (0.35, 0.65), "cloud_color": (250, 250, 252),
        "cities": 0.3,
    },
    "forest": {
        "temperature": (0, 30),
        "atmosphere": "oxygen-rich",
        "atmo_color": (100, 160, 255),
        "atmo_strength": 0.45,
        "sea_level": -0.05,
        "terrain": "continents",
        "ice_caps": 0,
        "clouds": (0.3, 0.6), "cloud_color": (250, 250, 250),
        "cities": 0.3,
    },
    "desert": {
        "temperature": (40, 60),
        "atmosphere": "thin",
        "atmo_color": (220, 180, 120),
        "atmo_strength": 0.25,
        "ice_caps": 0,
        "craters": 12,
        "clouds": (0.0, 0.2), "cloud_color": (232, 214, 178),
    },
    "gas_giant": {
        "temperature": (-100, 400),
        "atmosphere": "dense",
        "atmo_color": (200, 160, 100),
        "atmo_strength": 0.5,
        "land_specular": 0.06,
        "banded": "gas",
    },
    "toxic": {
        "temperature": (100, 600),
        "atmosphere": "poisonous",
        "atmo_color": (120, 220, 80),
        "atmo_strength": 0.4,
        "sea_level": -0.05,
        "terrain": "cracked",
        "glow": (60, 190, 45),
        "clouds": (0.2, 0.5), "cloud_color": (196, 214, 120),
    },
    "crystal": {
        "temperature": (-50, 100),
        "atmosphere": "thin",
        "atmo_color": (160, 230, 255),
        "atmo_strength": 0.3,
        "land_specular": 0.45,
        "craters": 20,
    },
    "volcanic": {
        "temperature": (800, 1500),
        "atmosphere": "sulfurous",
        "atmo_color": (200, 80, 20),
        "atmo_strength": 0.35,
        "sea_level": -0.05,
        "land_specular": 0.03,
        "terrain": "cracked",
        "glow": (255, 90, 20),
        "clouds": (0.15, 0.4), "cloud_color": (96, 86, 80),
    },
    "ice_giant": {
        "temperature": (-220, -150),
        "atmosphere": "hydrogen-methane",
        "atmo_color": (150, 210, 240),
        "atmo_strength": 0.55,
        "land_specular": 0.05,
        "banded": "ice",
    },
    "tundra": {
        "temperature": (-60, -5),
        "atmosphere": "thin",
        "atmo_color": (170, 200, 240),
        "atmo_strength": 0.3,
        "sea_level": -0.12,
        "ice_caps": -45,
        "craters": 8,
        "clouds": (0.1, 0.35),
        "cloud_color": (238, 242, 248),
    },
}

# Color ramps: list of (height_threshold, (r, g, b)) for smooth interpolation
COLOR_RAMPS = {
    "tundra": [
        (-1.0, (18, 38, 70)),
        (-0.14, (40, 72, 104)),
        (-0.12, (160, 176, 186)),
        (-0.05, (112, 116, 96)),
        (0.08, (128, 124, 98)),
        (0.2, (104, 100, 86)),
        (0.35, (150, 146, 138)),
        (0.5, (226, 230, 236)),
        (1.0, (248, 250, 255)),
    ],
    "ocean": [
        (-1.0, (6, 22, 64)),
        (-0.3, (12, 46, 112)),
        (-0.1, (22, 80, 158)),
        (-0.03, (40, 118, 184)),
        (-0.01, (78, 158, 196)),
        (0.0, (196, 184, 140)),
        (0.03, (92, 138, 62)),
        (0.18, (58, 106, 44)),
        (0.32, (120, 118, 72)),
        (0.48, (116, 96, 72)),
        (0.66, (140, 128, 118)),
        (0.82, (236, 238, 244)),
        (1.0, (250, 250, 255)),
    ],
    "forest": [
        (-1.0, (10, 40, 70)),
        (-0.2, (18, 70, 98)),
        (-0.07, (30, 104, 110)),
        (-0.05, (58, 120, 96)),
        (-0.03, (48, 98, 44)),
        (0.1, (40, 112, 42)),
        (0.25, (62, 138, 50)),
        (0.4, (88, 120, 58)),
        (0.55, (110, 100, 76)),
        (0.8, (150, 142, 130)),
        (1.0, (230, 232, 236)),
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

ICE_GIANT_PALETTES = [
    {   # Uranus-like pale cyan, bands barely there
        "zones": [(176, 226, 232), (186, 234, 238), (168, 218, 228)],
        "belts": [(150, 206, 220), (158, 212, 224), (142, 198, 214)],
        "storm": (224, 246, 250),
    },
    {   # Deep blue with dark spots
        "zones": [(80, 128, 214), (92, 142, 224), (72, 118, 204)],
        "belts": [(58, 100, 190), (66, 110, 198), (50, 90, 176)],
        "storm": (26, 44, 120),
    },
    {   # Teal
        "zones": [(110, 196, 196), (124, 206, 204), (100, 186, 188)],
        "belts": [(80, 164, 176), (88, 172, 182), (72, 152, 166)],
        "storm": (210, 240, 238),
    },
]

BAND_PALETTES = {"gas": GAS_GIANT_PALETTES, "ice": ICE_GIANT_PALETTES}
