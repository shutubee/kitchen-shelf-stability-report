from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional


@dataclass
class RiskBreakdown:
    stress_score: float
    buckling_score: float
    slenderness_score: float
    imperfection_score: float
    tilt_score: float
    degradation_score: float
    confidence_penalty: float
    total_score: float
    risk_band: str
    note: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------
# Basic normalization helpers
# ---------------------------------------------------------

def clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


def normalize_ratio(value: float, warning_level: float = 0.6, critical_level: float = 1.0) -> float:
    """
    Maps a ratio-like quantity to [0,1].
    Below warning -> low score
    Near critical -> high score
    """
    if critical_level <= warning_level:
        return clamp01(value)

    if value <= warning_level:
        return 0.5 * (value / max(warning_level, 1e-9))
    if value >= critical_level:
        return 1.0

    return 0.5 + 0.5 * ((value - warning_level) / (critical_level - warning_level))


# ---------------------------------------------------------
# Component scores
# ---------------------------------------------------------

def stress_risk_score(normalized_stress: float) -> float:
    """
    normalized_stress = sigma / sigma_ref
    """
    return normalize_ratio(normalized_stress, warning_level=0.5, critical_level=1.0)


def buckling_risk_score(buckling_utilization: float) -> float:
    """
    buckling_utilization = P / Pcr_adj  or equivalent
    """
    return normalize_ratio(buckling_utilization, warning_level=0.5, critical_level=1.0)


def slenderness_risk_score(slenderness: float, lambda_safe: float = 60.0, lambda_high: float = 180.0) -> float:
    if slenderness <= lambda_safe:
        return clamp01(0.3 * slenderness / max(lambda_safe, 1e-9))
    if slenderness >= lambda_high:
        return 1.0
    return 0.3 + 0.7 * ((slenderness - lambda_safe) / (lambda_high - lambda_safe))


def imperfection_risk_score(imperf_mm: float, slenderness: float) -> float:
    """
    Penalize imperfections more when the member is slender.
    """
    amp_score = clamp01(imperf_mm / 10.0)
    slender_factor = clamp01(slenderness / 180.0)
    return clamp01(0.25 * amp_score + 0.75 * amp_score * slender_factor)


def tilt_risk_score(avg_tilt_deg: Optional[float]) -> float:
    if avg_tilt_deg is None:
        return 0.0
    return clamp01(avg_tilt_deg / 10.0)


def degradation_risk_score(
    corrosion_level: float = 0.0,
    moisture_level: float = 0.0,
    looseness_level: float = 0.0,
) -> float:
    """
    Inputs expected in [0,1].
    """
    corrosion_level = clamp01(corrosion_level)
    moisture_level = clamp01(moisture_level)
    looseness_level = clamp01(looseness_level)

    return clamp01(
        0.4 * corrosion_level +
        0.25 * moisture_level +
        0.35 * looseness_level
    )


def confidence_penalty_score(confidence_score: float) -> float:
    """
    Lower confidence increases penalty.
    confidence_score in [0,1]
    """
    confidence_score = clamp01(confidence_score)
    return 1.0 - confidence_score


# ---------------------------------------------------------
# Risk aggregation
# ---------------------------------------------------------

DEFAULT_WEIGHTS = {
    "stress": 0.22,
    "buckling": 0.22,
    "slenderness": 0.16,
    "imperfection": 0.12,
    "tilt": 0.08,
    "degradation": 0.10,
    "confidence_penalty": 0.10,
}


def weighted_total(scores: Dict[str, float], weights: Dict[str, float]) -> float:
    total_w = sum(weights.values())
    if total_w <= 0:
        return 0.0

    total = 0.0
    for key, weight in weights.items():
        total += weight * clamp01(scores.get(key, 0.0))
    return clamp01(total / total_w)


def classify_risk_band(total_score: float) -> str:
    if total_score < 0.35:
        return "green"
    if total_score < 0.65:
        return "amber"
    return "red"


def risk_note(total_score: float, dominant_component: str) -> str:
    if total_score < 0.35:
        return f"Low overall structural risk. Main watch item: {dominant_component}."
    if total_score < 0.65:
        return f"Moderate structural risk. Governing contributor: {dominant_component}."
    return f"High structural risk. Immediate attention recommended; dominant contributor: {dominant_component}."


# ---------------------------------------------------------
# Main composite risk engine
# ---------------------------------------------------------

def compute_risk_breakdown(
    normalized_stress: float,
    buckling_utilization: float,
    slenderness: float,
    imperf_mm: float,
    avg_tilt_deg: Optional[float] = None,
    corrosion_level: float = 0.0,
    moisture_level: float = 0.0,
    looseness_level: float = 0.0,
    confidence_score: float = 1.0,
    weights: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:

    weights = weights or DEFAULT_WEIGHTS

    scores = {
        "stress": stress_risk_score(normalized_stress),
        "buckling": buckling_risk_score(buckling_utilization),
        "slenderness": slenderness_risk_score(slenderness),
        "imperfection": imperfection_risk_score(imperf_mm, slenderness),
        "tilt": tilt_risk_score(avg_tilt_deg),
        "degradation": degradation_risk_score(
            corrosion_level=corrosion_level,
            moisture_level=moisture_level,
            looseness_level=looseness_level,
        ),
        "confidence_penalty": confidence_penalty_score(confidence_score),
    }

    total = weighted_total(scores, weights)
    band = classify_risk_band(total)

    dominant_component = max(scores.items(), key=lambda kv: kv[1])[0]
    note = risk_note(total, dominant_component)

    result = RiskBreakdown(
        stress_score=scores["stress"],
        buckling_score=scores["buckling"],
        slenderness_score=scores["slenderness"],
        imperfection_score=scores["imperfection"],
        tilt_score=scores["tilt"],
        degradation_score=scores["degradation"],
        confidence_penalty=scores["confidence_penalty"],
        total_score=total,
        risk_band=band,
        note=note,
    )
    return result.to_dict()


# ---------------------------------------------------------
# Shelf-level aggregation
# ---------------------------------------------------------

def aggregate_member_risks(member_risks: list[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Aggregate multiple member risk records into a shelf-level summary.
    """
    if not member_risks:
        return {
            "member_count": 0,
            "max_total_score": 0.0,
            "mean_total_score": 0.0,
            "governing_member": None,
            "risk_band": "green",
            "note": "No member risks available."
        }

    max_item = max(member_risks, key=lambda x: x.get("total_score", 0.0))
    mean_score = sum(x.get("total_score", 0.0) for x in member_risks) / len(member_risks)

    max_score = max_item.get("total_score", 0.0)
    band = classify_risk_band(max_score)

    if band == "green":
        note = "Shelf-level risk is low under current assumptions."
    elif band == "amber":
        note = "Shelf-level risk is moderate; inspect the governing member."
    else:
        note = "Shelf-level risk is high; reinforcement or load reduction is recommended."

    return {
        "member_count": len(member_risks),
        "max_total_score": max_score,
        "mean_total_score": mean_score,
        "governing_member": max_item.get("id"),
        "risk_band": band,
        "note": note,
    }
