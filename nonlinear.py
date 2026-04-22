import math
from typing import Dict, Any


def secant_formula_utilization(P: float, E: float, A: float, c: float, e: float, I: float, L: float, K: float) -> float:
    """
    Very simplified secant-style amplification proxy for eccentric compression.
    """
    if min(E, A, I, L, K) <= 0:
        return 0.0
    Pcr = math.pi**2 * E * I / ((K * L) ** 2)
    if Pcr <= 0 or P >= Pcr:
        return 1.0
    amp = 1.0 / max(1e-9, (1.0 - P / Pcr))
    sigma = (P / A) + (P * e * c / I) * amp
    return sigma


def perry_robertson_reduction(slenderness: float, imperf_factor: float = 0.2) -> float:
    phi = 0.5 * (1 + imperf_factor * (slenderness / 100.0) + (slenderness / 100.0) ** 2)
    chi = 1.0 / (phi + math.sqrt(max(1e-9, phi**2 - (slenderness / 100.0) ** 2)))
    return max(0.1, min(1.0, chi))


def tangent_modulus(E: float, hardening_ratio: float = 0.01) -> float:
    return E * max(0.0, hardening_ratio)


def nonlinear_summary(slenderness: float, imperf_mm: float, load_ratio: float) -> Dict[str, Any]:
    sensitivity = min(1.0, 0.5 * slenderness / 180.0 + 0.5 * imperf_mm / 10.0)
    unstable = load_ratio > 0.85 and sensitivity > 0.5
    return {
        "imperfection_sensitivity": sensitivity,
        "likely_unstable": unstable,
        "recommendation": "Use nonlinear or imperfection-sensitive analysis." if unstable else "Linear check may be sufficient for screening.",
    }
