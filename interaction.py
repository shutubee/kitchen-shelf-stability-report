from typing import Dict, Any, List


def make_member_record(
    member_id: str,
    member_type: str,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
) -> Dict[str, Any]:
    return {
        "id": member_id,
        "type": member_type,
        "x1": x1,
        "y1": y1,
        "x2": x2,
        "y2": y2,
    }


def shift_member(member: Dict[str, Any], dx: float, dy: float) -> Dict[str, Any]:
    out = dict(member)
    out["x1"] += dx
    out["x2"] += dx
    out["y1"] += dy
    out["y2"] += dy
    return out


def relabel_members(members: List[Dict[str, Any]], prefix: str = "M") -> List[Dict[str, Any]]:
    out = []
    for i, m in enumerate(members, start=1):
        x = dict(m)
        x["id"] = f"{prefix}{i}"
        out.append(x)
    return out
