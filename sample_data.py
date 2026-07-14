DEFAULT_MEMBERS = [
    {"id": "U1", "type": "upright", "x1": 80, "y1": 60, "x2": 80, "y2": 430},
    {"id": "U2", "type": "upright", "x1": 320, "y1": 60, "x2": 320, "y2": 430},
    {"id": "S1", "type": "beam", "x1": 80, "y1": 180, "x2": 320, "y2": 180},
    {"id": "S2", "type": "beam", "x1": 80, "y1": 300, "x2": 320, "y2": 300},
    {"id": "B1", "type": "brace", "x1": 80, "y1": 430, "x2": 320, "y2": 60},
]

DEFAULT_PROJECT = {
    "project_id": "demo_shelf_001",
    "project_name": "Demo Kitchen Shelf",
    "members": DEFAULT_MEMBERS,
    "material_name": "Mild Steel",
    "reference_pixels": 370.0,
    "reference_length_m": 1.8,
}