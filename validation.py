from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
import math


@dataclass
class ValidationMessage:
    code: str
    severity: str
    message: str
    suggestion: str = ""

    def to_dict(self):
        return asdict(self)


# ---------------------------------------------------------
# Generic helpers
# ---------------------------------------------------------

def safe_positive(value: float) -> bool:
    return value is not None and value > 0


def bounded(value: float, low: float, high: float) -> bool:
    return low <= value <= high


# ---------------------------------------------------------
# Geometry validation
# ---------------------------------------------------------

def validate_geometry(
    member: Dict[str, Any],
    section: Dict[str, Any],
) -> List[ValidationMessage]:

    msgs = []

    L = member.get("length_m", 0.0)

    if not safe_positive(L):
        msgs.append(
            ValidationMessage(
                code="G001",
                severity="error",
                message="Member length must be positive.",
                suggestion="Check image calibration or line extraction."
            )
        )

    A = section.get("A", 0.0)
    I = section.get("I", 0.0)
    r = section.get("r", 0.0)

    if not safe_positive(A):
        msgs.append(
            ValidationMessage(
                code="G002",
                severity="error",
                message="Section area is invalid.",
                suggestion="Verify section dimensions."
            )
        )

    if not safe_positive(I):
        msgs.append(
            ValidationMessage(
                code="G003",
                severity="error",
                message="Second moment of area is invalid.",
                suggestion="Check section shape and dimensions."
            )
        )

    if not safe_positive(r):
        msgs.append(
            ValidationMessage(
                code="G004",
                severity="error",
                message="Radius of gyration is invalid.",
                suggestion="Verify section geometry."
            )
        )

    shape = section.get("shape")

    if shape == "hollow_circular":
        od = section.get("outer_d_m", 0)
        id_ = section.get("inner_d_m", 0)

        if id_ >= od:
            msgs.append(
                ValidationMessage(
                    code="G005",
                    severity="error",
                    message="Inner diameter must be smaller than outer diameter.",
                    suggestion="Reduce inner diameter."
                )
            )

    return msgs


# ---------------------------------------------------------
# Material validation
# ---------------------------------------------------------

def validate_material(
    E_Pa: float,
    sigma_y_Pa: float,
    density: float,
) -> List[ValidationMessage]:

    msgs = []

    if not safe_positive(E_Pa):
        msgs.append(
            ValidationMessage(
                code="M001",
                severity="error",
                message="Young's modulus must be positive.",
                suggestion="Check material preset."
            )
        )

    if not safe_positive(sigma_y_Pa):
        msgs.append(
            ValidationMessage(
                code="M002",
                severity="error",
                message="Yield stress must be positive.",
                suggestion="Verify material strength."
            )
        )

    if density <= 0:
        msgs.append(
            ValidationMessage(
                code="M003",
                severity="warning",
                message="Material density is non-positive.",
                suggestion="Self-weight calculations may be incorrect."
            )
        )

    if E_Pa < 1e8:
        msgs.append(
            ValidationMessage(
                code="M004",
                severity="warning",
                message="Very low stiffness detected.",
                suggestion="Check unit consistency."
            )
        )

    return msgs


# ---------------------------------------------------------
# Slenderness and stability checks
# ---------------------------------------------------------

def validate_slenderness(
    slenderness: float,
) -> List[ValidationMessage]:

    msgs = []

    if slenderness > 250:
        msgs.append(
            ValidationMessage(
                code="S001",
                severity="warning",
                message="Extremely slender member detected.",
                suggestion="Buckling sensitivity is very high."
            )
        )

    elif slenderness > 180:
        msgs.append(
            ValidationMessage(
                code="S002",
                severity="warning",
                message="Highly slender member.",
                suggestion="Consider imperfection-sensitive analysis."
            )
        )

    elif slenderness < 20:
        msgs.append(
            ValidationMessage(
                code="S003",
                severity="info",
                message="Low-slenderness member.",
                suggestion="Yield/crushing may govern rather than buckling."
            )
        )

    return msgs


# ---------------------------------------------------------
# Utilization and safety
# ---------------------------------------------------------

def validate_utilization(
    utilization: float,
) -> List[ValidationMessage]:

    msgs = []

    if utilization >= 1.0:
        msgs.append(
            ValidationMessage(
                code="U001",
                severity="error",
                message="Member exceeds critical utilization.",
                suggestion="Reduce load or increase stiffness."
            )
        )

    elif utilization >= 0.9:
        msgs.append(
            ValidationMessage(
                code="U002",
                severity="warning",
                message="Near-critical utilization.",
                suggestion="Increase safety margin."
            )
        )

    elif utilization >= 0.75:
        msgs.append(
            ValidationMessage(
                code="U003",
                severity="warning",
                message="High utilization.",
                suggestion="Monitor deformation and load placement."
            )
        )

    return msgs


# ---------------------------------------------------------
# Imperfection checks
# ---------------------------------------------------------

def validate_imperfection(
    imperf_mm: float,
    slenderness: float,
) -> List[ValidationMessage]:

    msgs = []

    if imperf_mm > 0 and slenderness > 120:
        msgs.append(
            ValidationMessage(
                code="I001",
                severity="warning",
                message="Imperfection-sensitive instability likely.",
                suggestion="Use Perry–Robertson or nonlinear analysis."
            )
        )

    if imperf_mm > 10:
        msgs.append(
            ValidationMessage(
                code="I002",
                severity="warning",
                message="Large initial imperfection detected.",
                suggestion="Inspect assembly alignment."
            )
        )

    return msgs


# ---------------------------------------------------------
# Tilt validation
# ---------------------------------------------------------

def validate_tilt(
    avg_tilt_deg: Optional[float],
) -> List[ValidationMessage]:

    msgs = []

    if avg_tilt_deg is None:
        return msgs

    if avg_tilt_deg > 8:
        msgs.append(
            ValidationMessage(
                code="T001",
                severity="warning",
                message="Large vertical tilt detected.",
                suggestion="Check floor level and member alignment."
            )
        )

    elif avg_tilt_deg > 3:
        msgs.append(
            ValidationMessage(
                code="T002",
                severity="info",
                message="Moderate shelf tilt observed.",
                suggestion="Imperfection effects may increase."
            )
        )

    return msgs


# ---------------------------------------------------------
# Load checks
# ---------------------------------------------------------

def validate_loads(
    axial_load_N: float,
    eccentricity_mm: float,
) -> List[ValidationMessage]:

    msgs = []

    if axial_load_N <= 0:
        msgs.append(
            ValidationMessage(
                code="L001",
                severity="warning",
                message="No axial load specified.",
                suggestion="Check load assignment."
            )
        )

    if eccentricity_mm > 100:
        msgs.append(
            ValidationMessage(
                code="L002",
                severity="warning",
                message="Very large eccentricity.",
                suggestion="Moment amplification may dominate response."
            )
        )

    return msgs


# ---------------------------------------------------------
# Confidence scoring
# ---------------------------------------------------------

def confidence_score(
    geometry_conf: float = 1.0,
    material_conf: float = 1.0,
    load_conf: float = 1.0,
    boundary_conf: float = 1.0,
) -> Dict[str, Any]:

    vals = [
        geometry_conf,
        material_conf,
        load_conf,
        boundary_conf,
    ]

    vals = [max(0.0, min(1.0, v)) for v in vals]

    score = sum(vals) / len(vals)

    if score >= 0.85:
        label = "high"
    elif score >= 0.6:
        label = "medium"
    else:
        label = "low"

    return {
        "score": score,
        "label": label,
    }


# ---------------------------------------------------------
# Main validation aggregator
# ---------------------------------------------------------

def validate_system(
    member: Dict[str, Any],
    section: Dict[str, Any],
    E_Pa: float,
    sigma_y_Pa: float,
    density: float,
    slenderness_value: float,
    utilization: float,
    imperf_mm: float,
    axial_load_N: float,
    eccentricity_mm: float,
    avg_tilt_deg: Optional[float] = None,
) -> List[Dict[str, Any]]:

    msgs = []

    msgs.extend(validate_geometry(member, section))
    msgs.extend(validate_material(E_Pa, sigma_y_Pa, density))
    msgs.extend(validate_slenderness(slenderness_value))
    msgs.extend(validate_utilization(utilization))
    msgs.extend(validate_imperfection(imperf_mm, slenderness_value))
    msgs.extend(validate_tilt(avg_tilt_deg))
    msgs.extend(validate_loads(axial_load_N, eccentricity_mm))

    return [m.to_dict() for m in msgs]
