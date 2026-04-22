import math
from dataclasses import dataclass, asdict
from typing import List, Tuple, Optional, Dict, Any

import numpy as np
from PIL import Image, ImageDraw

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False


@dataclass
class DetectedLine:
    x1: int
    y1: int
    x2: int
    y2: int
    length_px: float
    angle_deg: float
    orientation: str
    confidence: float = 0.5

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def pil_to_cv(image: Image.Image) -> np.ndarray:
    img = np.array(image.convert("RGB"))
    return cv2.cvtColor(img, cv2.COLOR_RGB2BGR) if CV2_AVAILABLE else img


def cv_to_pil(image: np.ndarray) -> Image.Image:
    if CV2_AVAILABLE:
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        return Image.fromarray(rgb)
    return Image.fromarray(image)


def preprocess_image(
    image: Image.Image,
    blur_ksize: int = 5,
    use_clahe: bool = True,
) -> Dict[str, np.ndarray]:
    """
    Returns grayscale, blurred, and edge maps for line detection.
    """
    if not CV2_AVAILABLE:
        raise ImportError("OpenCV is required for vision.py. Install opencv-python.")

    img_bgr = pil_to_cv(image)
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)

    if use_clahe:
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        gray = clahe.apply(gray)

    blur_ksize = max(3, blur_ksize)
    if blur_ksize % 2 == 0:
        blur_ksize += 1

    blurred = cv2.GaussianBlur(gray, (blur_ksize, blur_ksize), 0)
    edges = cv2.Canny(blurred, threshold1=50, threshold2=150)

    return {
        "gray": gray,
        "blurred": blurred,
        "edges": edges,
    }


def line_length(x1: int, y1: int, x2: int, y2: int) -> float:
    return math.hypot(x2 - x1, y2 - y1)


def line_angle_deg(x1: int, y1: int, x2: int, y2: int) -> float:
    angle = math.degrees(math.atan2(y2 - y1, x2 - x1))
    return angle


def classify_orientation(angle_deg: float, vertical_tol: float = 20.0, horizontal_tol: float = 20.0) -> str:
    """
    Classify line orientation approximately as vertical, horizontal, or diagonal.
    """
    a = angle_deg % 180.0

    if abs(a - 90.0) <= vertical_tol:
        return "vertical"
    if abs(a - 0.0) <= horizontal_tol or abs(a - 180.0) <= horizontal_tol:
        return "horizontal"
    return "diagonal"


def detect_lines_hough(
    image: Image.Image,
    min_line_length: int = 60,
    max_line_gap: int = 15,
    hough_threshold: int = 60,
    vertical_tol: float = 20.0,
    horizontal_tol: float = 20.0,
) -> List[DetectedLine]:
    """
    Detect line candidates using probabilistic Hough transform.
    """
    if not CV2_AVAILABLE:
        raise ImportError("OpenCV is required for vision.py. Install opencv-python.")

    processed = preprocess_image(image)
    edges = processed["edges"]

    raw_lines = cv2.HoughLinesP(
        edges,
        rho=1,
        theta=np.pi / 180,
        threshold=hough_threshold,
        minLineLength=min_line_length,
        maxLineGap=max_line_gap,
    )

    results: List[DetectedLine] = []
    if raw_lines is None:
        return results

    for item in raw_lines:
        x1, y1, x2, y2 = item[0]
        length_px = line_length(x1, y1, x2, y2)
        angle_deg = line_angle_deg(x1, y1, x2, y2)
        orientation = classify_orientation(angle_deg, vertical_tol, horizontal_tol)

        confidence = min(1.0, 0.3 + length_px / 500.0)
        results.append(
            DetectedLine(
                x1=int(x1),
                y1=int(y1),
                x2=int(x2),
                y2=int(y2),
                length_px=float(length_px),
                angle_deg=float(angle_deg),
                orientation=orientation,
                confidence=float(confidence),
            )
        )
    return results


def normalize_line_endpoints(line: DetectedLine) -> DetectedLine:
    """
    Normalize endpoints so sorting/merging is easier.
    For vertical-ish lines, smaller y first; otherwise smaller x first.
    """
    if line.orientation == "vertical":
        if line.y1 <= line.y2:
            return line
        return DetectedLine(
            x1=line.x2, y1=line.y2, x2=line.x1, y2=line.y1,
            length_px=line.length_px,
            angle_deg=line.angle_deg,
            orientation=line.orientation,
            confidence=line.confidence,
        )
    else:
        if line.x1 <= line.x2:
            return line
        return DetectedLine(
            x1=line.x2, y1=line.y2, x2=line.x1, y2=line.y1,
            length_px=line.length_px,
            angle_deg=line.angle_deg,
            orientation=line.orientation,
            confidence=line.confidence,
        )


def lines_close(
    a: DetectedLine,
    b: DetectedLine,
    pos_tol: float = 20.0,
    angle_tol: float = 10.0,
) -> bool:
    """
    Decide whether two lines are similar enough to merge.
    """
    if a.orientation != b.orientation:
        return False

    angle_diff = abs((a.angle_deg % 180) - (b.angle_deg % 180))
    angle_diff = min(angle_diff, 180 - angle_diff)
    if angle_diff > angle_tol:
        return False

    if a.orientation == "vertical":
        avg_x_a = (a.x1 + a.x2) / 2.0
        avg_x_b = (b.x1 + b.x2) / 2.0
        return abs(avg_x_a - avg_x_b) <= pos_tol

    if a.orientation == "horizontal":
        avg_y_a = (a.y1 + a.y2) / 2.0
        avg_y_b = (b.y1 + b.y2) / 2.0
        return abs(avg_y_a - avg_y_b) <= pos_tol

    mid_ax = (a.x1 + a.x2) / 2.0
    mid_ay = (a.y1 + a.y2) / 2.0
    mid_bx = (b.x1 + b.x2) / 2.0
    mid_by = (b.y1 + b.y2) / 2.0
    return math.hypot(mid_ax - mid_bx, mid_ay - mid_by) <= pos_tol


def merge_two_lines(a: DetectedLine, b: DetectedLine) -> DetectedLine:
    """
    Merge two similar lines into one longer representative line.
    """
    a = normalize_line_endpoints(a)
    b = normalize_line_endpoints(b)

    if a.orientation == "vertical":
        avg_x = int(round((a.x1 + a.x2 + b.x1 + b.x2) / 4.0))
        ys = [a.y1, a.y2, b.y1, b.y2]
        y1, y2 = min(ys), max(ys)
        x1 = x2 = avg_x
    elif a.orientation == "horizontal":
        avg_y = int(round((a.y1 + a.y2 + b.y1 + b.y2) / 4.0))
        xs = [a.x1, a.x2, b.x1, b.x2]
        x1, x2 = min(xs), max(xs)
        y1 = y2 = avg_y
    else:
        pts = [(a.x1, a.y1), (a.x2, a.y2), (b.x1, b.y1), (b.x2, b.y2)]
        pts_sorted = sorted(pts, key=lambda p: (p[0], p[1]))
        x1, y1 = pts_sorted[0]
        x2, y2 = pts_sorted[-1]

    length_px = line_length(x1, y1, x2, y2)
    angle_deg = line_angle_deg(x1, y1, x2, y2)
    orientation = classify_orientation(angle_deg)
    confidence = min(1.0, max(a.confidence, b.confidence) + 0.1)

    return DetectedLine(
        x1=x1,
        y1=y1,
        x2=x2,
        y2=y2,
        length_px=length_px,
        angle_deg=angle_deg,
        orientation=orientation,
        confidence=confidence,
    )


def merge_similar_lines(
    lines: List[DetectedLine],
    pos_tol: float = 20.0,
    angle_tol: float = 10.0,
) -> List[DetectedLine]:
    """
    Greedy merging for overlapping/near-duplicate line detections.
    """
    if not lines:
        return []

    pending = [normalize_line_endpoints(l) for l in lines]
    merged: List[DetectedLine] = []

    while pending:
        base = pending.pop(0)
        changed = True
        while changed:
            changed = False
            remaining = []
            for other in pending:
                if lines_close(base, other, pos_tol=pos_tol, angle_tol=angle_tol):
                    base = merge_two_lines(base, other)
                    changed = True
                else:
                    remaining.append(other)
            pending = remaining
        merged.append(base)

    return merged


def filter_lines(
    lines: List[DetectedLine],
    keep_orientations: Optional[List[str]] = None,
    min_length_px: float = 80.0,
) -> List[DetectedLine]:
    keep_orientations = keep_orientations or ["vertical", "horizontal", "diagonal"]
    return [
        l for l in lines
        if l.orientation in keep_orientations and l.length_px >= min_length_px
    ]


def detect_shelf_members(
    image: Image.Image,
    min_line_length: int = 80,
    merge: bool = True,
) -> List[DetectedLine]:
    """
    Main high-level detector for shelf member candidates.
    Keeps vertical, horizontal, and diagonal lines that are likely to be
    uprights, shelf beams, or braces.
    """
    lines = detect_lines_hough(
        image=image,
        min_line_length=min_line_length,
        max_line_gap=20,
        hough_threshold=60,
    )

    lines = filter_lines(lines, keep_orientations=["vertical", "horizontal", "diagonal"], min_length_px=min_line_length)

    if merge:
        lines = merge_similar_lines(lines, pos_tol=18.0, angle_tol=10.0)

    lines.sort(key=lambda l: l.length_px, reverse=True)
    return lines


def suggest_member_type(line: DetectedLine) -> str:
    """
    Heuristic mapping from line orientation to likely structural role.
    """
    if line.orientation == "vertical":
        return "upright"
    if line.orientation == "horizontal":
        return "beam"
    return "brace"


def convert_detected_lines_to_members(
    lines: List[DetectedLine],
    prefix: str = "M",
) -> List[Dict[str, Any]]:
    members = []
    for idx, line in enumerate(lines, start=1):
        members.append({
            "id": f"{prefix}{idx}",
            "type": suggest_member_type(line),
            "x1": int(line.x1),
            "y1": int(line.y1),
            "x2": int(line.x2),
            "y2": int(line.y2),
            "length_px": float(line.length_px),
            "angle_deg": float(line.angle_deg),
            "orientation": line.orientation,
            "confidence": float(line.confidence),
        })
    return members


def draw_detected_lines(
    image: Image.Image,
    lines: List[DetectedLine],
    show_labels: bool = True,
) -> Image.Image:
    """
    Draw detected line candidates onto the image.
    """
    out = image.copy().convert("RGB")
    draw = ImageDraw.Draw(out)

    color_map = {
        "vertical": (0, 180, 0),
        "horizontal": (220, 120, 0),
        "diagonal": (180, 0, 0),
    }

    for i, line in enumerate(lines, start=1):
        color = color_map.get(line.orientation, (0, 0, 255))
        draw.line((line.x1, line.y1, line.x2, line.y2), fill=color, width=4)
        if show_labels:
            mx = int((line.x1 + line.x2) / 2)
            my = int((line.y1 + line.y2) / 2)
            label = f"L{i}:{line.orientation[0].upper()}"
            draw.text((mx + 4, my + 4), label, fill=color)

    return out


def estimate_tilt_from_verticals(lines: List[DetectedLine]) -> Optional[float]:
    """
    Estimate average deviation from perfect vertical among vertical lines.
    Returns average tilt in degrees, or None if no vertical lines.
    """
    verticals = [l for l in lines if l.orientation == "vertical"]
    if not verticals:
        return None

    tilts = []
    for line in verticals:
        a = line.angle_deg % 180.0
        tilt = abs(a - 90.0)
        tilts.append(tilt)

    return float(np.mean(tilts)) if tilts else None


def detect_and_summarize(image: Image.Image) -> Dict[str, Any]:
    """
    Convenience pipeline:
    - detect lines
    - merge duplicates
    - propose shelf members
    - estimate tilt
    """
    lines = detect_shelf_members(image)
    members = convert_detected_lines_to_members(lines)
    avg_tilt_deg = estimate_tilt_from_verticals(lines)

    return {
        "lines": [l.to_dict() for l in lines],
        "members": members,
        "avg_vertical_tilt_deg": avg_tilt_deg,
        "count_vertical": sum(1 for l in lines if l.orientation == "vertical"),
        "count_horizontal": sum(1 for l in lines if l.orientation == "horizontal"),
        "count_diagonal": sum(1 for l in lines if l.orientation == "diagonal"),
    }
