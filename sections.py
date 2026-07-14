import math


def rectangular_section(width_m: float, depth_m: float):
    area = width_m * depth_m
    I = width_m * depth_m**3 / 12.0
    c = depth_m / 2.0
    r = math.sqrt(I / area) if area > 0 else 0.0
    return {
        "shape": "rectangular",
        "A": area,
        "I": I,
        "c": c,
        "r": r,
        "width_m": width_m,
        "depth_m": depth_m,
    }


def circular_section(diameter_m: float):
    area = math.pi * diameter_m**2 / 4.0
    I = math.pi * diameter_m**4 / 64.0
    c = diameter_m / 2.0
    r = math.sqrt(I / area) if area > 0 else 0.0
    return {
        "shape": "circular",
        "A": area,
        "I": I,
        "c": c,
        "r": r,
        "diameter_m": diameter_m,
    }


def hollow_circular_section(outer_d_m: float, inner_d_m: float):
    area = math.pi * (outer_d_m**2 - inner_d_m**2) / 4.0
    I = math.pi * (outer_d_m**4 - inner_d_m**4) / 64.0
    c = outer_d_m / 2.0
    r = math.sqrt(I / area) if area > 0 else 0.0
    return {
        "shape": "hollow_circular",
        "A": area,
        "I": I,
        "c": c,
        "r": r,
        "outer_d_m": outer_d_m,
        "inner_d_m": inner_d_m,
    }


def build_section(shape: str, **kwargs):
    if shape == "rectangular":
        return rectangular_section(kwargs["width_m"], kwargs["depth_m"])
    if shape == "circular":
        return circular_section(kwargs["diameter_m"])
    if shape == "hollow_circular":
        return hollow_circular_section(kwargs["outer_d_m"], kwargs["inner_d_m"])
    raise ValueError(f"Unsupported shape: {shape}")