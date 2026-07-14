import json
from typing import Dict, Any


def export_project_json(project: Dict[str, Any]) -> str:
    return json.dumps(project, indent=2)


def import_project_json(text: str) -> Dict[str, Any]:
    return json.loads(text)