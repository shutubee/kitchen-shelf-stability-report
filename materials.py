from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional, List


@dataclass
class Material:
    name: str
    category: str
    E_GPa: float
    yield_MPa: float
    density: float
    nu: float = 0.30
    shear_G_GPa: Optional[float] = None
    hardening_GPa: Optional[float] = None
    moisture_sensitive: float = 0.0
    corrosion_sensitive: float = 0.0
    temperature_sensitive: float = 0.0
    notes: str = ""

    def resolved_shear_G_GPa(self) -> float:
        if self.shear_G_GPa is not None:
            return self.shear_G_GPa
        return self.E_GPa / (2.0 * (1.0 + self.nu))

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["shear_G_GPa_resolved"] = self.resolved_shear_G_GPa()
        return data

    def to_solver_dict(self) -> Dict[str, float]:
        return {
            "E_GPa": self.E_GPa,
            "yield_MPa": self.yield_MPa,
            "density": self.density,
            "nu": self.nu,
            "shear_G_GPa": self.resolved_shear_G_GPa(),
            "hardening_GPa": self.hardening_GPa or 0.0,
        }


def _build_material_library() -> Dict[str, Material]:
    mats = [
        Material(
            name="Mild Steel",
            category="metal",
            E_GPa=200.0,
            yield_MPa=250.0,
            density=7850.0,
            nu=0.30,
            corrosion_sensitive=0.70,
            temperature_sensitive=0.20,
            notes="General structural steel preset for racks and tubular members.",
        ),
        Material(
            name="Structural Steel",
            category="metal",
            E_GPa=210.0,
            yield_MPa=355.0,
            density=7850.0,
            nu=0.30,
            corrosion_sensitive=0.70,
            temperature_sensitive=0.20,
            notes="Higher-strength structural steel.",
        ),
        Material(
            name="Stainless Steel",
            category="metal",
            E_GPa=193.0,
            yield_MPa=215.0,
            density=8000.0,
            nu=0.29,
            corrosion_sensitive=0.15,
            temperature_sensitive=0.20,
            notes="Good kitchen-facing preset where corrosion resistance matters.",
        ),
        Material(
            name="Aluminum",
            category="metal",
            E_GPa=69.0,
            yield_MPa=95.0,
            density=2700.0,
            nu=0.33,
            corrosion_sensitive=0.20,
            temperature_sensitive=0.35,
            notes="Lightweight sections; lower stiffness than steel.",
        ),
        Material(
            name="Plywood",
            category="wood",
            E_GPa=10.0,
            yield_MPa=35.0,
            density=600.0,
            nu=0.25,
            moisture_sensitive=0.55,
            temperature_sensitive=0.15,
            notes="Useful for shelf boards; stiffness varies by grain and quality.",
        ),
        Material(
            name="MDF",
            category="wood",
            E_GPa=4.0,
            yield_MPa=18.0,
            density=750.0,
            nu=0.28,
            moisture_sensitive=0.85,
            temperature_sensitive=0.20,
            notes="High moisture sensitivity; common in budget shelving.",
        ),
        Material(
            name="Particle Board",
            category="wood",
            E_GPa=3.0,
            yield_MPa=14.0,
            density=680.0,
            nu=0.28,
            moisture_sensitive=0.90,
            temperature_sensitive=0.20,
            notes="Low-cost shelving material with poor moisture robustness.",
        ),
        Material(
            name="PVC",
            category="polymer",
            E_GPa=3.0,
            yield_MPa=50.0,
            density=1380.0,
            nu=0.38,
            moisture_sensitive=0.10,
            temperature_sensitive=0.65,
            notes="Can soften under heat; useful for light-duty racks only.",
        ),
    ]
    return {m.name: m for m in mats}


MATERIAL_LIBRARY: Dict[str, Material] = _build_material_library()

MATERIALS: Dict[str, Dict[str, Any]] = {
    name: {
        "E_GPa": mat.E_GPa,
        "yield_MPa": mat.yield_MPa,
        "density": mat.density,
    }
    for name, mat in MATERIAL_LIBRARY.items()
}


def list_material_names() -> List[str]:
    return list(MATERIAL_LIBRARY.keys())


def get_material(name: str) -> Material:
    if name not in MATERIAL_LIBRARY:
        raise KeyError(f"Unknown material: {name}")
    return MATERIAL_LIBRARY[name]


def get_material_dict(name: str) -> Dict[str, Any]:
    return get_material(name).to_dict()


def get_solver_material(name: str) -> Dict[str, float]:
    return get_material(name).to_solver_dict()


def add_custom_material(
    name: str,
    category: str,
    E_GPa: float,
    yield_MPa: float,
    density: float,
    nu: float = 0.30,
    shear_G_GPa: Optional[float] = None,
    hardening_GPa: Optional[float] = None,
    moisture_sensitive: float = 0.0,
    corrosion_sensitive: float = 0.0,
    temperature_sensitive: float = 0.0,
    notes: str = "",
) -> None:
    mat = Material(
        name=name,
        category=category,
        E_GPa=E_GPa,
        yield_MPa=yield_MPa,
        density=density,
        nu=nu,
        shear_G_GPa=shear_G_GPa,
        hardening_GPa=hardening_GPa,
        moisture_sensitive=moisture_sensitive,
        corrosion_sensitive=corrosion_sensitive,
        temperature_sensitive=temperature_sensitive,
        notes=notes,
    )
    MATERIAL_LIBRARY[name] = mat
    MATERIALS[name] = {
        "E_GPa": mat.E_GPa,
        "yield_MPa": mat.yield_MPa,
        "density": mat.density,
    }


def validate_material_properties(
    E_GPa: float,
    yield_MPa: float,
    density: float,
    nu: float,
) -> Dict[str, Any]:
    errors = []
    warnings = []

    if E_GPa <= 0:
        errors.append("Young's modulus must be positive.")
    if yield_MPa <= 0:
        errors.append("Yield/allowable stress must be positive.")
    if density <= 0:
        warnings.append("Density is non-positive; self-weight calculations may be invalid.")
    if not (0.0 <= nu <= 0.5):
        warnings.append("Poisson ratio is outside the usual engineering range [0, 0.5].")
    if E_GPa < 1.0:
        warnings.append("Very low stiffness detected; check units.")
    if yield_MPa < 5.0:
        warnings.append("Very low strength detected; check units or material assumptions.")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
    }


def material_environment_modifier(
    material_name: str,
    moisture_level: float = 0.0,
    corrosion_level: float = 0.0,
    temperature_level: float = 0.0,
) -> Dict[str, float]:
    """
    Returns simple reduction factors in [0,1] for stiffness and strength.
    Higher environment levels mean more severe conditions.
    """
    mat = get_material(material_name)

    moisture_level = max(0.0, min(1.0, moisture_level))
    corrosion_level = max(0.0, min(1.0, corrosion_level))
    temperature_level = max(0.0, min(1.0, temperature_level))

    stiffness_reduction = (
        0.35 * mat.moisture_sensitive * moisture_level
        + 0.25 * mat.corrosion_sensitive * corrosion_level
        + 0.25 * mat.temperature_sensitive * temperature_level
    )
    strength_reduction = (
        0.25 * mat.moisture_sensitive * moisture_level
        + 0.40 * mat.corrosion_sensitive * corrosion_level
        + 0.30 * mat.temperature_sensitive * temperature_level
    )

    stiffness_factor = max(0.4, 1.0 - stiffness_reduction)
    strength_factor = max(0.4, 1.0 - strength_reduction)

    return {
        "stiffness_factor": stiffness_factor,
        "strength_factor": strength_factor,
    }


def apply_environment_to_material(
    material_name: str,
    moisture_level: float = 0.0,
    corrosion_level: float = 0.0,
    temperature_level: float = 0.0,
) -> Dict[str, Any]:
    mat = get_material(material_name)
    mods = material_environment_modifier(
        material_name=material_name,
        moisture_level=moisture_level,
        corrosion_level=corrosion_level,
        temperature_level=temperature_level,
    )

    return {
        "name": mat.name,
        "category": mat.category,
        "E_GPa_effective": mat.E_GPa * mods["stiffness_factor"],
        "yield_MPa_effective": mat.yield_MPa * mods["strength_factor"],
        "density": mat.density,
        "nu": mat.nu,
        "shear_G_GPa_effective": mat.resolved_shear_G_GPa() * mods["stiffness_factor"],
        "stiffness_factor": mods["stiffness_factor"],
        "strength_factor": mods["strength_factor"],
        "notes": mat.notes,
    }
