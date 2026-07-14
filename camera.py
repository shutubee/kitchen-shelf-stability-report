from typing import Dict, Any


def camera_frame_stub() -> Dict[str, Any]:
    return {
        "status": "stub",
        "message": "Live camera processing is not implemented in this MVP.",
    }


def estimate_live_quality(brightness: float, blur_level: float) -> Dict[str, Any]:
    good_brightness = 0.3 <= brightness <= 0.85
    good_blur = blur_level <= 0.3
    usable = good_brightness and good_blur
    return {
        "usable": usable,
        "brightness_ok": good_brightness,
        "blur_ok": good_blur,
    }