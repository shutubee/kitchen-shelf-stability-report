from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional, List
import copy


# ---------------------------------------------------------
# Base preset dataclasses
# ---------------------------------------------------------

@dataclass
class GeometryPreset:
    name: str
    description: str
    section_shape: str
    section_params: Dict[str, float]
    reference_height_m: float
    member_layout: str = "standard_frame"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class BoundaryPreset:
    name: str
    description: str
    K: float
    top: str
    bottom: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class LoadPreset:
    name: str
    description: str
    axial_load_N: float
    eccentricity_mm: float = 0.0
    extra_moment_Nm: float = 0.0
    load_distribution: str = "uniform"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ShelfPreset:
    preset_id: str
    name: str
    description: str
    material_name: str
    geometry: Dict[str, Any]
    boundary: Dict[str, Any]
    load: Dict[str, Any]
    imperfection_mm: float = 2.0
    environment: Optional[Dict[str, float]] = None
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------
# Geometry presets
# ---------------------------------------------------------

GEOMETRY_PRESETS: Dict[str, GeometryPreset] = {
    "steel_tube_light": GeometryPreset(
        name="steel_tube_light",
        description="Light steel tubular rack geometry for kitchen shelves.",
        section_shape="rectangular",
        section_params={"width_m": 0.020, "depth_m": 0.020},
        reference_height_m=1.80,
        member_layout="2_uprights_2_beams_1_brace",
    ),
    "steel_tube_medium": GeometryPreset(
        name="steel_tube_medium",
        description="Medium steel tubular kitchen rack.",
        section_shape="rectangular",
        section_params={"width_m": 0.025, "depth_m": 0.025},
        reference_height_m=1.90,
        member_layout="2_uprights_3_beams_1_brace",
    ),
    "stainless_round_light": GeometryPreset(
        name="stainless_round_light",
        description="Light stainless round-tube shelf frame.",
        section_shape="circular",
        section_params={"diameter_m": 0.020},
        reference_height_m=1.70,
        member_layout="2_uprights_2_beams",
    ),
    "plywood_board_light": GeometryPreset(
        name="plywood_board_light",
        description="Simple plywood shelf board section.",
        section_shape="rectangular",
        section_params={"width_m": 0.300, "depth_m": 0.018},
        reference_height_m=1.50,
        member_layout="board_only",
    ),
    "mdf_board_budget": GeometryPreset(
        name="mdf_board_budget",
        description="Budget MDF shelf board section.",
        section_shape="rectangular",
        section_params={"width_m": 0.300, "depth_m": 0.015},
        reference_height_m=1.50,
        member_layout="board_only",
    ),
    "hollow_round_heavy": GeometryPreset(
        name="hollow_round_heavy",
        description="Heavy-duty hollow circular tube frame.",
        section_shape="hollow_circular",
        section_params={"outer_d_m": 0.030, "inner_d_m": 0.024},
        reference_height_m=1.95,
        member_layout="2_uprights_3_beams_2_braces",
    ),
}


# ---------------------------------------------------------
# Boundary presets
# ---------------------------------------------------------

BOUNDARY_PRESETS: Dict[str, BoundaryPreset] = {
    "fixed_fixed": BoundaryPreset(
        name="fixed_fixed",
        description="Both ends effectively fixed.",
        K=0.5,
        top="fixed",
        bottom="fixed",
    ),
    "fixed_pinned": BoundaryPreset(
        name="fixed_pinned",
        description="One end fixed, one pinned.",
        K=0.7,
        top="fixed",
        bottom="pinned",
    ),
    "pinned_pinned": BoundaryPreset(
        name="pinned_pinned",
        description="Both ends pinned.",
        K=1.0,
        top="pinned",
        bottom="pinned",
    ),
    "fixed_free": BoundaryPreset(
        name="fixed_free",
        description="Cantilever condition.",
        K=2.0,
        top="free",
        bottom="fixed",
    ),
    "wall_bracketed": BoundaryPreset(
        name="wall_bracketed",
        description="Wall-supported shelf or bracketed rack; semi-restrained idealization.",
        K=0.8,
        top="guided",
        bottom="fixed",
    ),
}


# ---------------------------------------------------------
# Load presets
# ---------------------------------------------------------

LOAD_PRESETS: Dict[str, LoadPreset] = {
    "light_utensils": LoadPreset(
        name="light_utensils",
        description="Light kitchen utensil loading.",
        axial_load_N=250.0,
        eccentricity_mm=3.0,
        extra_moment_Nm=2.0,
        load_distribution="uniform",
    ),
    "mixed_kitchen_items": LoadPreset(
        name="mixed_kitchen_items",
        description="Typical mixed kitchen shelf loading.",
        axial_load_N=600.0,
        eccentricity_mm=5.0,
        extra_moment_Nm=5.0,
        load_distribution="semi_uniform",
    ),
    "heavy_appliances": LoadPreset(
        name="heavy_appliances",
        description="Heavier loading with appliance eccentricity.",
        axial_load_N=1200.0,
        eccentricity_mm=15.0,
        extra_moment_Nm=20.0,
        load_distribution="concentrated",
    ),
    "top_heavy_storage": LoadPreset(
        name="top_heavy_storage",
        description="Top-heavy jars or containers causing instability sensitivity.",
        axial_load_N=850.0,
        eccentricity_mm=20.0,
        extra_moment_Nm=18.0,
        load_distribution="eccentric_top",
    ),
    "empty_shelf": LoadPreset(
        name="empty_shelf",
        description="Near-empty shelf, baseline loading.",
        axial_load_N=80.0,
        eccentricity_mm=0.0,
        extra_moment_Nm=0.0,
        load_distribution="uniform",
    ),
}


# ---------------------------------------------------------
# Composite shelf presets
# ---------------------------------------------------------

SHELF_PRESETS: Dict[str, ShelfPreset] = {
    "P1": ShelfPreset(
        preset_id="P1",
        name="Light Steel Kitchen Rack",
        description="Light tubular steel rack with common kitchen item loading.",
        material_name="Mild Steel",
        geometry=GEOMETRY_PRESETS["steel_tube_light"].to_dict(),
        boundary=BOUNDARY_PRESETS["pinned_pinned"].to_dict(),
        load=LOAD_PRESETS["mixed_kitchen_items"].to_dict(),
        imperfection_mm=2.0,
        environment={"moisture_level": 0.20, "corrosion_level": 0.15, "temperature_level": 0.10},
        notes="Good starting preset for generic light steel kitchen racks.",
    ),
    "P2": ShelfPreset(
        preset_id="P2",
        name="Medium Steel Rack Heavy Load",
        description="Medium tubular rack under heavier appliance-like loading.",
        material_name="Mild Steel",
        geometry=GEOMETRY_PRESETS["steel_tube_medium"].to_dict(),
        boundary=BOUNDARY_PRESETS["fixed_pinned"].to_dict(),
        load=LOAD_PRESETS["heavy_appliances"].to_dict(),
        imperfection_mm=3.0,
        environment={"moisture_level": 0.25, "corrosion_level": 0.20, "temperature_level": 0.15},
        notes="Useful when users store mixers, cooker vessels, or denser metal loads.",
    ),
    "P3": ShelfPreset(
        preset_id="P3",
        name="Stainless Kitchen Shelf",
        description="Stainless shelf frame for wet kitchen environments.",
        material_name="Stainless Steel",
        geometry=GEOMETRY_PRESETS["stainless_round_light"].to_dict(),
        boundary=BOUNDARY_PRESETS["wall_bracketed"].to_dict(),
        load=LOAD_PRESETS["mixed_kitchen_items"].to_dict(),
        imperfection_mm=1.5,
        environment={"moisture_level": 0.35, "corrosion_level": 0.05, "temperature_level": 0.10},
        notes="Better corrosion performance in wet areas.",
    ),
    "P4": ShelfPreset(
        preset_id="P4",
        name="Plywood Shelf Board",
        description="Simple plywood shelf board under light to moderate loading.",
        material_name="Plywood",
        geometry=GEOMETRY_PRESETS["plywood_board_light"].to_dict(),
        boundary=BOUNDARY_PRESETS["wall_bracketed"].to_dict(),
        load=LOAD_PRESETS["light_utensils"].to_dict(),
        imperfection_mm=1.0,
        environment={"moisture_level": 0.25, "corrosion_level": 0.0, "temperature_level": 0.10},
        notes="Useful for shelf boards rather than freestanding frames.",
    ),
    "P5": ShelfPreset(
        preset_id="P5",
        name="Budget MDF Shelf",
        description="Budget MDF shelf in moisture-sensitive environment.",
        material_name="MDF",
        geometry=GEOMETRY_PRESETS["mdf_board_budget"].to_dict(),
        boundary=BOUNDARY_PRESETS["wall_bracketed"].to_dict(),
        load=LOAD_PRESETS["light_utensils"].to_dict(),
        imperfection_mm=1.0,
        environment={"moisture_level": 0.45, "corrosion_level": 0.0, "temperature_level": 0.15},
        notes="Use carefully in humid kitchens.",
    ),
    "P6": ShelfPreset(
        preset_id="P6",
        name="Heavy Hollow Tube Rack",
        description="Heavy hollow circular rack with bracing and high load capacity.",
        material_name="Structural Steel",
        geometry=GEOMETRY_PRESETS["hollow_round_heavy"].to_dict(),
        boundary=BOUNDARY_PRESETS["fixed_fixed"].to_dict(),
        load=LOAD_PRESETS["heavy_appliances"].to_dict(),
        imperfection_mm=2.5,
        environment={"moisture_level": 0.15, "corrosion_level": 0.20, "temperature_level": 0.10},
        notes="Heavy-duty storage case.",
    ),
    "P7": ShelfPreset(
        preset_id="P7",
        name="Top-Heavy Risk Case",
        description="Preset intentionally biased toward top-heavy storage instability.",
        material_name="Mild Steel",
        geometry=GEOMETRY_PRESETS["steel_tube_light"].to_dict(),
        boundary=BOUNDARY_PRESETS["pinned_pinned"].to_dict(),
        load=LOAD_PRESETS["top_heavy_storage"].to_dict(),
        imperfection_mm=4.0,
        environment={"moisture_level": 0.20, "corrosion_level": 0.20, "temperature_level": 0.15},
        notes="Useful for demonstrating instability sensitivity.",
    ),
}


# ---------------------------------------------------------
# Public helpers
# ---------------------------------------------------------

def list_geometry_presets() -> List[str]:
    return list(GEOMETRY_PRESETS.keys())


def list_boundary_presets() -> List[str]:
    return list(BOUNDARY_PRESETS.keys())


def list_load_presets() -> List[str]:
    return list(LOAD_PRESETS.keys())


def list_shelf_presets() -> List[str]:
    return list(SHELF_PRESETS.keys())


def get_geometry_preset(name: str) -> Dict[str, Any]:
    if name not in GEOMETRY_PRESETS:
        raise KeyError(f"Unknown geometry preset: {name}")
    return copy.deepcopy(GEOMETRY_PRESETS[name].to_dict())


def get_boundary_preset(name: str) -> Dict[str, Any]:
    if name not in BOUNDARY_PRESETS:
        raise KeyError(f"Unknown boundary preset: {name}")
    return copy.deepcopy(BOUNDARY_PRESETS[name].to_dict())


def get_load_preset(name: str) -> Dict[str, Any]:
    if name not in LOAD_PRESETS:
        raise KeyError(f"Unknown load preset: {name}")
    return copy.deepcopy(LOAD_PRESETS[name].to_dict())


def get_shelf_preset(preset_id: str) -> Dict[str, Any]:
    if preset_id not in SHELF_PRESETS:
        raise KeyError(f"Unknown shelf preset: {preset_id}")
    return copy.deepcopy(SHELF_PRESETS[preset_id].to_dict())


# ---------------------------------------------------------
# Override helpers
# ---------------------------------------------------------

def apply_overrides(base: Dict[str, Any], overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Shallow-recursive override for nested preset dictionaries.
    """
    result = copy.deepcopy(base)
    overrides = overrides or {}

    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = apply_overrides(result[key], value)
        else:
            result[key] = value
    return result


def build_active_configuration(
    preset_id: Optional[str] = None,
    material_name: Optional[str] = None,
    geometry_name: Optional[str] = None,
    boundary_name: Optional[str] = None,
    load_name: Optional[str] = None,
    overrides: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Build a final active config either from:
    - a composite shelf preset, or
    - separate module presets
    """
    if preset_id is not None:
        config = get_shelf_preset(preset_id)
    else:
        if material_name is None:
            material_name = "Mild Steel"
        if geometry_name is None:
            geometry_name = "steel_tube_light"
        if boundary_name is None:
            boundary_name = "pinned_pinned"
        if load_name is None:
            load_name = "mixed_kitchen_items"

        config = {
            "preset_id": None,
            "name": "Custom Assembled Configuration",
            "description": "Configuration built from separate preset modules.",
            "material_name": material_name,
            "geometry": get_geometry_preset(geometry_name),
            "boundary": get_boundary_preset(boundary_name),
            "load": get_load_preset(load_name),
            "imperfection_mm": 2.0,
            "environment": {
                "moisture_level": 0.20,
                "corrosion_level": 0.10,
                "temperature_level": 0.10,
            },
            "notes": "",
        }

    return apply_overrides(config, overrides)


# ---------------------------------------------------------
# Import / export helpers
# ---------------------------------------------------------

def export_preset_config(config: Dict[str, Any]) -> Dict[str, Any]:
    return copy.deepcopy(config)


def import_preset_config(config: Dict[str, Any]) -> Dict[str, Any]:
    required = ["material_name", "geometry", "boundary", "load"]
    missing = [k for k in required if k not in config]
    if missing:
        raise ValueError(f"Imported preset config missing keys: {missing}")
    return copy.deepcopy(config)


# ---------------------------------------------------------
# Preset descriptions for UI
# ---------------------------------------------------------

def preset_summary_table() -> List[Dict[str, Any]]:
    rows = []
    for pid, preset in SHELF_PRESETS.items():
        rows.append({
            "preset_id": pid,
            "name": preset.name,
            "material": preset.material_name,
            "geometry": preset.geometry["name"],
            "boundary": preset.boundary["name"],
            "load": preset.load["name"],
            "imperfection_mm": preset.imperfection_mm,
        })
    return rows
