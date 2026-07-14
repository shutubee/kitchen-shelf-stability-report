from typing import Dict, Any, List


def live_scan_summary(
    detected_member_count: int,
    avg_tilt_deg: float | None,
    max_risk_score: float,
) -> Dict[str, Any]:
    if max_risk_score >= 0.65:
        status = "high_risk"
    elif max_risk_score >= 0.35:
        status = "moderate_risk"
    else:
        status = "low_risk"

    return {
        "status": status,
        "detected_member_count": detected_member_count,
        "avg_tilt_deg": avg_tilt_deg,
        "max_risk_score": max_risk_score,
        "message": f"Live scan status: {status}",
    }