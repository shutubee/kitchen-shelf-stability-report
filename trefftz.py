from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional
import math


@dataclass
class TrefftzMode:
    name: str
    description: str
    order: int
    mode_type: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


TREFFTZ_LIBRARY = [
    TrefftzMode("axial_linear", "Linear axial trial function", 1, "axial"),
    TrefftzMode("buckling_sine_1", "First sine buckling mode", 1, "buckling"),
    TrefftzMode("buckling_sine_2", "Second sine buckling mode", 2, "buckling"),
    TrefftzMode("cantilever_poly_3", "Third-order cantilever polynomial", 3, "bending"),
]


def list_trefftz_modes() -> List[Dict[str, Any]]:
    return [m.to_dict() for m in TREFFTZ_LIBRARY]


def sine_mode(x: float, L: float, n: int = 1) -> float:
    if L <= 0:
        return 0.0
    return math.sin(n * math.pi * x / L)


def cantilever_poly_mode(x: float, L: float) -> float:
    if L <= 0:
        return 0.0
    xi = x / L
    return xi**2 * (3 - 2 * xi)


def eval_trefftz_mode(mode_name: str, x: float, L: float) -> float:
    if mode_name == "buckling_sine_1":
        return sine_mode(x, L, 1)
    if mode_name == "buckling_sine_2":
        return sine_mode(x, L, 2)
    if mode_name == "cantilever_poly_3":
        return cantilever_poly_mode(x, L)
    if mode_name == "axial_linear":
        return x / L if L > 0 else 0.0
    raise ValueError(f"Unknown Trefftz mode: {mode_name}")


def approximate_mode_shape(mode_name: str, L: float, n_points: int = 100) -> Dict[str, List[float]]:
    xs = [L * i / (n_points - 1) for i in range(n_points)]
    ys = [eval_trefftz_mode(mode_name, x, L) for x in xs]
    return {"x": xs, "y": ys}
