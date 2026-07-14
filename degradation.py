from typing import Dict, Any


def corrosion_loss_factor(corrosion_level: float) -> float:
    corrosion_level = max(0.0, min(1.0, corrosion_level))
    return max(0.5, 1.0 - 0.4 * corrosion_level)


def moisture_loss_factor(moisture_level: float, material_category: str) -> float:
    moisture_level = max(0.0, min(1.0, moisture_level))
    if material_category == "wood":
        return max(0.4, 1.0 - 0.5 * moisture_level)
    return max(0.7, 1.0 - 0.15 * moisture_level)


def looseness_loss_factor(looseness_level: float) -> float:
    looseness_level = max(0.0, min(1.0, looseness_level))
    return max(0.5, 1.0 - 0.35 * looseness_level)


def combined_degradation_factor(
    corrosion_level: float = 0.0,
    moisture_level: float = 0.0,
    looseness_level: float = 0.0,
    material_category: str = "metal",
) -> Dict[str, Any]:
    c = corrosion_loss_factor(corrosion_level)
    m = moisture_loss_factor(moisture_level, material_category)
    l = looseness_loss_factor(looseness_level)
    total = max(0.3, c * m * l)
    return {
        "corrosion_factor": c,
        "moisture_factor": m,
        "looseness_factor": l,
        "combined_factor": total,
    }