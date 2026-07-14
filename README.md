# Kitchen Shelf Stability Report

A comprehensive Python toolkit for analyzing the structural stability of kitchen shelves using computer vision, materials science, and finite element principles.

## Features

- **Photo-Assisted Geometry Extraction**: Automatically detect shelf members (uprights, beams, braces) from images using Hough line detection
- **Stress-Slenderness Mapping**: Calculate structural stresses and slenderness ratios for shelf members
- **Imperfection-Sensitive Buckling Assessment**: Evaluate buckling risk accounting for geometric imperfections
- **Kitchen Shelf Structural Diagnostics**: Comprehensive risk assessment combining multiple failure modes
- **Material Library**: Pre-configured materials (steel, aluminum, wood, composites) with environment-aware properties
- **Risk Scoring**: Weighted multi-factor risk analysis with color-coded risk bands (green/amber/red)

## Installation

### Requirements
- Python 3.8+
- NumPy
- Pillow (PIL)
- OpenCV (for vision analysis)

### Quick Start

```bash
# Clone the repository
git clone https://github.com/shutubee/kitchen-shelf-stability-report.git
cd kitchen-shelf-stability-report

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Basic Example: Detect Shelf Members from Image

```python
from PIL import Image
from vision import detect_shelf_members, draw_detected_lines

# Load and analyze an image of your shelf
image = Image.open("shelf_photo.jpg")
lines = detect_shelf_members(image, min_line_length=80, merge=True)

# Draw results
annotated = draw_detected_lines(image, lines, show_labels=True)
annotated.save("shelf_annotated.jpg")

# Print detected members
for line in lines:
    print(f"{line.orientation} line: {line.length_px:.1f}px @ {line.angle_deg:.1f}°")
```

### Advanced Example: Full Stability Assessment

```python
from materials import get_material
from risk import compute_risk_breakdown

# Define shelf configuration
material = get_material("Structural Steel")
load_per_mm = 100  # Newtons

# Calculate structural parameters
stress_ratio = 0.65
buckling_util = 0.45
slenderness = 85
imperfection_mm = 2.5

# Compute risk
risk = compute_risk_breakdown(
    normalized_stress=stress_ratio,
    buckling_utilization=buckling_util,
    slenderness=slenderness,
    imperf_mm=imperfection_mm,
    avg_tilt_deg=2.5,
    corrosion_level=0.2,
    moisture_level=0.1,
    confidence_score=0.85
)

print(f"Risk Band: {risk['risk_band'].upper()}")
print(f"Total Score: {risk['total_score']:.2f}")
print(f"Assessment: {risk['note']}")
```

## Module Reference

### `vision.py`
Computer vision tools for shelf geometry extraction from images.

**Key Functions:**
- `detect_shelf_members(image, min_line_length=80, merge=True)` - Main detector for shelf structural members
- `detect_lines_hough(image, ...)` - Hough line detection with configurable parameters
- `merge_similar_lines(lines, pos_tol=20, angle_tol=10)` - Merge near-duplicate line detections
- `draw_detected_lines(image, lines, show_labels=True)` - Visualize detected members on image

### `materials.py`
Material property database and environment-aware material modification.

**Key Functions:**
- `get_material(name)` - Retrieve material properties
- `list_material_names()` - Get available materials
- `add_custom_material(...)` - Define custom materials
- `apply_environment_to_material(...)` - Adjust properties for moisture/corrosion/temperature

**Available Materials:**
- Metals: Mild Steel, Structural Steel, Stainless Steel, Aluminum
- Wood: Plywood, MDF, Particle Board
- Polymers: PVC

### `risk.py`
Multi-factor structural risk assessment engine.

**Risk Components:**
- Stress utilization
- Buckling stability
- Slenderness ratio
- Geometric imperfections
- Tilt/deviation from vertical
- Environmental degradation
- Confidence/measurement uncertainty

**Risk Bands:**
- **Green** (score < 0.35): Low risk, routine inspection
- **Amber** (score 0.35-0.65): Moderate risk, inspection recommended
- **Red** (score ≥ 0.65): High risk, immediate remediation advised

### `geometry.py`
Geometric calculations for shelf analysis.

### `validation.py`
Input validation and error checking.

## Risk Assessment Methodology

The system computes a composite risk score [0, 1] combining:

1. **Stress Risk** (22% weight): Actual stress vs. material yield
2. **Buckling Risk** (22% weight): Column/beam stability assessment
3. **Slenderness Risk** (16% weight): Length-to-dimension ratio effects
4. **Imperfection Risk** (12% weight): Initial misalignment amplification
5. **Tilt Risk** (8% weight): Out-of-vertical deviation
6. **Degradation Risk** (10% weight): Environmental effects
7. **Confidence Penalty** (10% weight): Measurement uncertainty

Higher scores indicate greater risk. All inputs are normalized to [0, 1] before aggregation.

## Contributing

Contributions welcome! Please:
1. Add tests for new features
2. Follow PEP 8 style guidelines
3. Update documentation
4. Use type hints

## License

MIT License - See LICENSE file for details

## Disclaimer

This tool provides analytical assessment only. **Always consult a structural engineer** before making decisions affecting physical safety. The authors assume no liability for shelf failures or injuries.

## References

- Timoshenko & Gere: "Theory of Elastic Stability"
- Eurocode 3: Steel Construction
- AISC Steel Design Guide
