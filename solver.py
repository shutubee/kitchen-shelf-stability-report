"""
solver.py

Core engineering calculations for the Kitchen Shelf Stability Report app.

Units
-----
E               : Pa
yield_stress     : Pa
length           : m
area             : m²
second moment I  : m⁴
radius gyration  : m
load             : N
moment           : N·m
stress           : Pa
imperfection     : mm

This module provides preliminary screening calculations only.
It is not a replacement for a structural design check or site inspection.
"""

from __future__ import annotations

import math
from typing import Tuple


_EPS = 1.0e-12


def _positive(value: float, name: str) -> float:
    """Return value as float and ensure that it is strictly positive."""
    value = float(value)

    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite.")

    if value <= 0.0:
        raise ValueError(f"{name} must be greater than zero.")

    return value


def _non_negative(value: float, name: str) -> float:
    """Return value as float and ensure that it is non-negative."""
    value = float(value)

    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite.")

    if value < 0.0:
        raise ValueError(f"{name} cannot be negative.")

    return value


def slenderness(
    effective_length_factor: float,
    length_m: float,
    radius_of_gyration_m: float,
) -> float:
    """
    Calculate member slenderness ratio.

    λ = K L / r

    Parameters
    ----------
    effective_length_factor:
        Effective-length factor K.
    length_m:
        Actual member length in metres.
    radius_of_gyration_m:
        Radius of gyration r = sqrt(I/A), in metres.

    Returns
    -------
    float
        Dimensionless slenderness ratio.
    """
    K = _positive(effective_length_factor, "Effective length factor K")
    length = _positive(length_m, "Member length")
    radius = _positive(radius_of_gyration_m, "Radius of gyration")

    return (K * length) / radius


def euler_critical_load(
    elastic_modulus_pa: float,
    second_moment_m4: float,
    effective_length_factor: float,
    length_m: float,
) -> float:
    """
    Calculate Euler elastic buckling load.

    Pcr = π² E I / (K L)²

    Returns
    -------
    float
        Euler critical load in newtons.
    """
    E = _positive(elastic_modulus_pa, "Elastic modulus")
    I = _positive(second_moment_m4, "Second moment of area")
    K = _positive(effective_length_factor, "Effective length factor K")
    length = _positive(length_m, "Member length")

    effective_length = K * length

    return (math.pi**2 * E * I) / (effective_length**2)


def euler_critical_stress(
    critical_load_n: float,
    area_m2: float,
) -> float:
    """
    Convert a critical load into average critical stress.

    σcr = Pcr / A

    Returns
    -------
    float
        Critical stress in pascals.
    """
    load = _non_negative(critical_load_n, "Critical load")
    area = _positive(area_m2, "Cross-sectional area")

    return load / area


def johnson_critical_stress(
    slenderness_ratio: float,
    elastic_modulus_pa: float,
    yield_stress_pa: float,
) -> float:
    """
    Calculate Johnson parabolic-column critical stress.

    σJ = σy [1 - σy λ² / (4 π² E)]

    The Johnson equation is intended mainly for short-to-intermediate
    compression members. The result is limited to the range 0 to σy.

    Returns
    -------
    float
        Johnson critical stress in pascals.
    """
    lam = _non_negative(slenderness_ratio, "Slenderness ratio")
    E = _positive(elastic_modulus_pa, "Elastic modulus")
    sigma_y = _positive(yield_stress_pa, "Yield stress")

    reduction = (sigma_y * lam**2) / (4.0 * math.pi**2 * E)
    sigma_j = sigma_y * (1.0 - reduction)

    return max(0.0, min(sigma_j, sigma_y))


def combined_stress(
    axial_load_n: float,
    area_m2: float,
    bending_moment_nm: float,
    extreme_fibre_distance_m: float,
    second_moment_m4: float,
) -> Tuple[float, float, float]:
    """
    Calculate combined axial and bending stress.

    σa = P/A
    σb = M c/I
    σcombined = |σa| + |σb|

    The conservative maximum absolute stress is returned because the app
    uses the result for screening and utilization calculations.

    Returns
    -------
    tuple
        combined_stress_pa, axial_stress_pa, bending_stress_pa
    """
    axial_load = float(axial_load_n)
    moment = float(bending_moment_nm)

    if not math.isfinite(axial_load):
        raise ValueError("Axial load must be finite.")

    if not math.isfinite(moment):
        raise ValueError("Bending moment must be finite.")

    area = _positive(area_m2, "Cross-sectional area")
    c = _non_negative(
        extreme_fibre_distance_m,
        "Extreme-fibre distance",
    )
    I = _positive(second_moment_m4, "Second moment of area")

    axial_stress = axial_load / area
    bending_stress = moment * c / I

    maximum_absolute_stress = (
        abs(axial_stress) + abs(bending_stress)
    )

    return (
        maximum_absolute_stress,
        axial_stress,
        bending_stress,
    )


def imperfection_knockdown(
    ideal_critical_load_n: float,
    imperfection_mm: float,
) -> Tuple[float, float]:
    """
    Reduce ideal buckling capacity for initial geometric imperfection.

    The app currently supplies only imperfection amplitude, not member
    length or section depth. Therefore, this uses a bounded screening
    relationship rather than a code-specific design equation:

        knockdown = 1 / (1 + imperfection_mm / 10)

    The factor is limited to a minimum of 0.20 so that invalid or unusually
    large input does not cause numerical collapse.

    Examples
    --------
    0 mm  -> factor 1.00
    2 mm  -> factor 0.833
    5 mm  -> factor 0.667
    10 mm -> factor 0.50

    Returns
    -------
    tuple
        adjusted_critical_load_n, knockdown_factor
    """
    ideal_load = _non_negative(
        ideal_critical_load_n,
        "Ideal critical load",
    )
    imperfection = _non_negative(
        imperfection_mm,
        "Imperfection",
    )

    knockdown_factor = 1.0 / (1.0 + imperfection / 10.0)
    knockdown_factor = max(0.20, min(1.0, knockdown_factor))

    adjusted_load = ideal_load * knockdown_factor

    return adjusted_load, knockdown_factor


def lambda_critical(
    elastic_modulus_pa: float,
    yield_stress_pa: float,
) -> float:
    """
    Calculate the Johnson–Euler transition slenderness.

    Equating the Johnson parabola with the Euler curve gives:

        λc = sqrt(2 π² E / σy)

    Returns
    -------
    float
        Dimensionless transition slenderness.
    """
    E = _positive(elastic_modulus_pa, "Elastic modulus")
    sigma_y = _positive(yield_stress_pa, "Yield stress")

    return math.sqrt((2.0 * math.pi**2 * E) / sigma_y)


def recommend_regime(
    slenderness_ratio: float,
    critical_slenderness: float,
    eccentricity_mm: float = 0.0,
    imperfection_mm: float = 0.0,
) -> str:
    """
    Recommend the governing analysis regime for display in the app.

    Parameters
    ----------
    slenderness_ratio:
        Calculated K L/r value.
    critical_slenderness:
        Johnson–Euler transition slenderness.
    eccentricity_mm:
        Load eccentricity in millimetres.
    imperfection_mm:
        Initial member imperfection in millimetres.

    Returns
    -------
    str
        Human-readable regime description.
    """
    lam = _non_negative(slenderness_ratio, "Slenderness ratio")
    lam_crit = _positive(
        critical_slenderness,
        "Critical slenderness",
    )
    eccentricity = _non_negative(eccentricity_mm, "Eccentricity")
    imperfection = _non_negative(imperfection_mm, "Imperfection")

    if eccentricity > 0.0 or imperfection > 0.0:
        qualifier = " with eccentricity/imperfection"
    else:
        qualifier = ""

    if lam < 0.50 * lam_crit:
        return f"Short member / material strength{qualifier}"

    if lam < lam_crit:
        return f"Intermediate member / Johnson regime{qualifier}"

    return f"Slender member / Euler buckling regime{qualifier}"