from typing import Dict, Any


def estimate_scale_from_reference_object(
    reference_pixels: float,
    reference_length_m: float,
) -> Dict[str, Any]:
    if reference_pixels <= 0:
        raise ValueError("reference_pixels must be positive.")
    scale = reference_length_m / reference_pixels
    return {
        "m_per_pixel": scale,
        "reference_pixels": reference_pixels,
        "reference_length_m": reference_length_m,
    }


def ar_measurement_stub() -> Dict[str, Any]:
    return {
        "status": "stub",
        "message": "AR measurement integration is not yet implemented.",
    }