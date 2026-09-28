"""Random planet names."""

import random


def generate_name(rng=random):
    """Generate a random planet name"""
    prefixes = [
        "Xen", "Astra", "Nova", "Cryo", "Vul", "Zar", "Terra", "Oph", "Ere", "Quar",
        "Kel", "Dra", "Nyx", "Sol", "Lun", "Stel", "Gal", "Neb", "Cos", "Ori",
        "Pyr", "Aqua", "Aero", "Geo", "Chron", "Helio", "Thanat", "Hyper", "Proto", "Neo",
    ]
    suffixes = [
        "ion", "is", "ar", "os", "ea", "or", "a", "um", "ax", "ex",
        "ius", "eon", "yx", "ia", "us", "on", "an", "el", "al", "en",
        "ith", "eth", "oth", "ir", "ur", "ys", "ix", "ox", "yn", "ria",
    ]

    base_name = rng.choice(prefixes) + rng.choice(suffixes)

    if rng.random() < 0.3:
        secondary = rng.choice([
            " Prime", " Alpha", " Beta", " Gamma", " Delta", " Epsilon",
            " I", " II", " III", " IV", " V", " VI", " VII", " VIII", " IX", " X",
            " Major", " Minor", " Omega", " Sigma", " Tau",
        ])
        base_name += secondary

    return base_name + "-" + str(rng.randint(1, 999))
