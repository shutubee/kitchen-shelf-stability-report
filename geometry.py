import math

def pixel_length(x1, y1, x2, y2):
    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

def m_per_pixel_from_reference(ref_pixels: float, ref_length_m: float):
    if ref_pixels <= 0:
        raise ValueError("Reference pixel length must be positive.")
    return ref_length_m / ref_pixels

def member_length_m(member: dict, m_per_pixel: float):
    return pixel_length(
        member["x1"], member["y1"], member["x2"], member["y2"]
    ) * m_per_pixel
