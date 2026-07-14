"""Validation utilities for the Kitchen Shelf Stability Report.

This module validates geometry, material properties, stability indicators,
loads, imperfections, tilt, and confidence inputs.  The public function
``validate_system`` preserves the original project interface and returns a
list of dictionaries suitable for reports or a Streamlit UI.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from numbers import Real
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class ValidationMessage:
    """A structured validation result."""

    code: str
    severity: str
    message: str
    suggestion: str = ""

    def to_dict(self) -> Dict[str, str]:
        return asdict(self)


# ---------------------------------------------------------
# Generic helpers
# ---------------------------------------------------------

def is_finite_number(value: Any) -> bool:
    """Return True when *value* is a finite real number (excluding booleans)."""
    return (
        isinstance(value, Real)
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    )


def safe_positive(value: Any) -> bool:
    """Return True when *value* is finite and strictly positive."""
    return is_finite_number(value) and float(value) > 0.0


def bounded(value: Any, low: float, high: float) -> bool:
    """Return True when *value* is finite and lies within [low, high]."""
    return is_finite_number(value) and low <= float(value) <= high


def _invalid_number_message(
    code: str,
    field_name: str,
    suggestion: str,
) -> ValidationMessage:
    return ValidationMessage(
        code=code,
        severity="error",
        message=f"{field_name} must be a finite number.",
        suggestion=suggestion,
    )


# ---------------------------------------------------------
# Geometry validation
# ---------------------------------------------------------

def validate_geometry(
    member: Dict[str, Any],
    section: Dict[str, Any],
) -> List[ValidationMessage]:
    msgs: List[ValidationMessage] = []

    member = member or {}
    section = section or {}

    length_m = member.get("length_m")
    area = section.get("A")
    second_moment = section.get("I")
    radius_gyration = section.get("r")

    if not safe_positive(length_m):
        msgs.append(
            ValidationMessage(
                code="G001",
                severity="error",
                message="Member length must be a finite positive value.",
                suggestion="Check image calibration, units, or line extraction.",
            )
        )

    if not safe_positive(area):
        msgs.append(
            ValidationMessage(
                code="G002",
                severity="error",
                message="Section area must be a finite positive value.",
                suggestion="Verify the section shape, dimensions, and units.",
            )
        )

    if not safe_positive(second_moment):
        msgs.append(
            ValidationMessage(
                code="G003",
                severity="error",
                message="Second moment of area must be a finite positive value.",
                suggestion="Check section shape, dimensions, axis, and units.",
            )
        )

    if not safe_positive(radius_gyration):
        msgs.append(
            ValidationMessage(
                code="G004",
                severity="error",
                message="Radius of gyration must be a finite positive value.",
                suggestion="Verify the section geometry or calculate r = sqrt(I/A).",
            )
        )

    shape = str(section.get("shape", "")).strip().lower()
    if shape == "hollow_circular":
        outer_d = section.get("outer_d_m")
        inner_d = section.get("inner_d_m")

        if not safe_positive(outer_d):
            msgs.append(
                ValidationMessage(
                    code="G005",
                    severity="error",
                    message="Outer diameter must be a finite positive value.",
                    suggestion="Enter a valid hollow-section outer diameter in metres.",
                )
            )

        if not is_finite_number(inner_d) or float(inner_d) < 0.0:
            msgs.append(
                ValidationMessage(
                    code="G006",
                    severity="error",
                    message="Inner diameter must be a finite non-negative value.",
                    suggestion="Enter zero for a solid section or a valid inner diameter.",
                )
            )
        elif safe_positive(outer_d) and float(inner_d) >= float(outer_d):
            msgs.append(
                ValidationMessage(
                    code="G007",
                    severity="error",
                    message="Inner diameter must be smaller than outer diameter.",
                    suggestion="Reduce the inner diameter or increase the outer diameter.",
                )
            )

    # Check the identity r² = I/A when all section properties are usable.
    if safe_positive(area) and safe_positive(second_moment) and safe_positive(radius_gyration):
        calculated_r = math.sqrt(float(second_moment) / float(area))
        relative_error = abs(float(radius_gyration) - calculated_r) / calculated_r
        if relative_error > 0.10:
            msgs.append(
                ValidationMessage(
                    code="G008",
                    severity="warning",
                    message="Section properties are inconsistent: r does not match sqrt(I/A).",
                    suggestion="Recalculate A, I, and r using one consistent unit system and axis.",
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
    msgs: List[ValidationMessage] = []

    if not safe_positive(E_Pa):
        msgs.append(
            ValidationMessage(
                code="M001",
                severity="error",
                message="Young's modulus must be a finite positive value.",
                suggestion="Check the material preset and confirm that E is entered in pascals.",
            )
        )

    if not safe_positive(sigma_y_Pa):
        msgs.append(
            ValidationMessage(
                code="M002",
                severity="error",
                message="Yield stress must be a finite positive value.",
                suggestion="Verify the material strength and confirm units are pascals.",
            )
        )

    if not is_finite_number(density):
        msgs.append(
            _invalid_number_message(
                code="M003",
                field_name="Material density",
                suggestion="Enter density in kg/m³.",
            )
        )
    elif float(density) <= 0.0:
        msgs.append(
            ValidationMessage(
                code="M004",
                severity="error",
                message="Material density must be positive.",
                suggestion="Enter a valid density in kg/m³; self-weight depends on it.",
            )
        )

    if safe_positive(E_Pa) and float(E_Pa) < 1.0e8:
        msgs.append(
            ValidationMessage(
                code="M005",
                severity="warning",
                message="Very low stiffness detected.",
                suggestion="Check whether Young's modulus was entered in GPa or MPa instead of Pa.",
            )
        )

    if safe_positive(sigma_y_Pa) and float(sigma_y_Pa) < 1.0e5:
        msgs.append(
            ValidationMessage(
                code="M006",
                severity="warning",
                message="Very low yield stress detected.",
                suggestion="Check whether yield stress was entered in MPa instead of Pa.",
            )
        )

    return msgs


# ---------------------------------------------------------
# Slenderness and stability checks
# ---------------------------------------------------------

def validate_slenderness(slenderness: float) -> List[ValidationMessage]:
    msgs: List[ValidationMessage] = []

    if not is_finite_number(slenderness):
        return [
            _invalid_number_message(
                code="S000",
                field_name="Slenderness",
                suggestion="Recalculate slenderness from effective length and radius of gyration.",
            )
        ]

    value = float(slenderness)
    if value < 0.0:
        msgs.append(
            ValidationMessage(
                code="S001",
                severity="error",
                message="Slenderness cannot be negative.",
                suggestion="Check effective length, radius of gyration, and sign handling.",
            )
        )
    elif value > 250.0:
        msgs.append(
            ValidationMessage(
                code="S002",
                severity="warning",
                message="Extremely slender member detected.",
                suggestion="Buckling and imperfection sensitivity are very high.",
            )
        )
    elif value > 180.0:
        msgs.append(
            ValidationMessage(
                code="S003",
                severity="warning",
                message="Highly slender member detected.",
                suggestion="Consider imperfection-sensitive or nonlinear analysis.",
            )
        )
    elif value < 20.0:
        msgs.append(
            ValidationMessage(
                code="S004",
                severity="info",
                message="Low-slenderness member detected.",
                suggestion="Yielding, crushing, or local effects may govern rather than Euler buckling.",
            )
        )

    return msgs


# ---------------------------------------------------------
# Utilization and safety
# ---------------------------------------------------------

def validate_utilization(utilization: float) -> List[ValidationMessage]:
    msgs: List[ValidationMessage] = []

    if not is_finite_number(utilization):
        return [
            _invalid_number_message(
                code="U000",
                field_name="Utilization",
                suggestion="Recalculate demand-to-capacity utilization.",
            )
        ]

    value = float(utilization)
    if value < 0.0:
        msgs.append(
            ValidationMessage(
                code="U001",
                severity="error",
                message="Utilization cannot be negative.",
                suggestion="Check load signs and the demand-to-capacity calculation.",
            )
        )
    elif value >= 1.0:
        msgs.append(
            ValidationMessage(
                code="U002",
                severity="error",
                message="Member exceeds critical utilization.",
                suggestion="Reduce load, improve restraint, or increase section capacity.",
            )
        )
    elif value >= 0.90:
        msgs.append(
            ValidationMessage(
                code="U003",
                severity="warning",
                message="Near-critical utilization.",
                suggestion="Increase the safety margin and verify all assumptions.",
            )
        )
    elif value >= 0.75:
        msgs.append(
            ValidationMessage(
                code="U004",
                severity="warning",
                message="High utilization.",
                suggestion="Monitor deformation, connection behaviour, and load placement.",
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
    msgs: List[ValidationMessage] = []

    if not is_finite_number(imperf_mm):
        return [
            _invalid_number_message(
                code="I000",
                field_name="Initial imperfection",
                suggestion="Enter the measured or assumed imperfection in millimetres.",
            )
        ]

    imperfection = float(imperf_mm)
    if imperfection < 0.0:
        msgs.append(
            ValidationMessage(
                code="I001",
                severity="error",
                message="Initial imperfection magnitude cannot be negative.",
                suggestion="Use a non-negative magnitude; direction should be stored separately.",
            )
        )
        return msgs

    if is_finite_number(slenderness) and float(slenderness) >= 0.0:
        if imperfection > 0.0 and float(slenderness) > 120.0:
            msgs.append(
                ValidationMessage(
                    code="I002",
                    severity="warning",
                    message="Imperfection-sensitive instability is likely.",
                    suggestion="Use Perry-Robertson, second-order, or nonlinear analysis.",
                )
            )

    if imperfection > 10.0:
        msgs.append(
            ValidationMessage(
                code="I003",
                severity="warning",
                message="Large initial imperfection detected.",
                suggestion="Inspect shelf assembly, member straightness, and connection alignment.",
            )
        )

    return msgs


# ---------------------------------------------------------
# Tilt validation
# ---------------------------------------------------------

def validate_tilt(avg_tilt_deg: Optional[float]) -> List[ValidationMessage]:
    msgs: List[ValidationMessage] = []

    if avg_tilt_deg is None:
        return msgs

    if not is_finite_number(avg_tilt_deg):
        return [
            _invalid_number_message(
                code="T000",
                field_name="Average tilt",
                suggestion="Enter tilt in degrees or leave it as None when unavailable.",
            )
        ]

    tilt = abs(float(avg_tilt_deg))
    if tilt > 8.0:
        msgs.append(
            ValidationMessage(
                code="T001",
                severity="warning",
                message="Large vertical tilt detected.",
                suggestion="Check floor level, shelf plumbness, member alignment, and anchorage.",
            )
        )
    elif tilt > 3.0:
        msgs.append(
            ValidationMessage(
                code="T002",
                severity="info",
                message="Moderate shelf tilt observed.",
                suggestion="Include eccentricity and imperfection effects in the stability assessment.",
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
    msgs: List[ValidationMessage] = []

    if not is_finite_number(axial_load_N):
        msgs.append(
            _invalid_number_message(
                code="L000",
                field_name="Axial load",
                suggestion="Enter the applied axial load in newtons.",
            )
        )
    elif float(axial_load_N) < 0.0:
        msgs.append(
            ValidationMessage(
                code="L001",
                severity="error",
                message="Axial load cannot be negative in this compression-only model.",
                suggestion="Use a positive compression magnitude or revise the sign convention.",
            )
        )
    elif float(axial_load_N) == 0.0:
        msgs.append(
            ValidationMessage(
                code="L002",
                severity="warning",
                message="No axial load specified.",
                suggestion="Check load assignment before interpreting buckling utilization.",
            )
        )

    if not is_finite_number(eccentricity_mm):
        msgs.append(
            _invalid_number_message(
                code="L003",
                field_name="Load eccentricity",
                suggestion="Enter eccentricity in millimetres.",
            )
        )
    elif abs(float(eccentricity_mm)) > 100.0:
        msgs.append(
            ValidationMessage(
                code="L004",
                severity="warning",
                message="Very large load eccentricity detected.",
                suggestion="Moment amplification may dominate; consider beam-column analysis.",
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
    """Return a bounded average confidence score and qualitative label.

    Invalid or non-finite confidence inputs are treated as zero confidence.
    """

    raw_values = [
        geometry_conf,
        material_conf,
        load_conf,
        boundary_conf,
    ]
    values = [
        max(0.0, min(1.0, float(value))) if is_finite_number(value) else 0.0
        for value in raw_values
    ]

    score = sum(values) / len(values)
    if score >= 0.85:
        label = "high"
    elif score >= 0.60:
        label = "medium"
    else:
        label = "low"

    return {
        "score": score,
        "label": label,
        "components": {
            "geometry": values[0],
            "material": values[1],
            "load": values[2],
            "boundary": values[3],
        },
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
    """Run all validation groups and return serializable dictionaries."""

    msgs: List[ValidationMessage] = []

    msgs.extend(validate_geometry(member, section))
    msgs.extend(validate_material(E_Pa, sigma_y_Pa, density))
    msgs.extend(validate_slenderness(slenderness_value))
    msgs.extend(validate_utilization(utilization))
    msgs.extend(validate_imperfection(imperf_mm, slenderness_value))
    msgs.extend(validate_tilt(avg_tilt_deg))
    msgs.extend(validate_loads(axial_load_N, eccentricity_mm))

    return [message.to_dict() for message in msgs]


__all__ = [
    "ValidationMessage",
    "bounded",
    "confidence_score",
    "is_finite_number",
    "safe_positive",
    "validate_geometry",
    "validate_imperfection",
    "validate_loads",
    "validate_material",
    "validate_slenderness",
    "validate_system",
    "validate_tilt",
    "validate_utilization",
]
