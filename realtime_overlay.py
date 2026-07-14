from typing import Dict, Any, List


def build_overlay_payload(members: List[Dict[str, Any]], results: List[Dict[str, Any]]) -> Dict[str, Any]:
    by_id = {r["id"]: r for r in results}
    payload = []
    for m in members:
        r = by_id.get(m["id"], {})
        payload.append({
            "id": m["id"],
            "x1": m["x1"],
            "y1": m["y1"],
            "x2": m["x2"],
            "y2": m["y2"],
            "risk_band": r.get("risk_band", "green"),
            "risk_score": r.get("risk_score", 0.0),
        })
    return {"overlay": payload}