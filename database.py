from typing import Dict, Any, List


class InMemoryProjectDB:
    def __init__(self):
        self._store: Dict[str, Dict[str, Any]] = {}

    def save(self, project_id: str, project: Dict[str, Any]) -> None:
        self._store[project_id] = dict(project)

    def load(self, project_id: str) -> Dict[str, Any]:
        if project_id not in self._store:
            raise KeyError(f"Project not found: {project_id}")
        return dict(self._store[project_id])

    def list_ids(self) -> List[str]:
        return sorted(self._store.keys())

    def delete(self, project_id: str) -> None:
        if project_id in self._store:
            del self._store[project_id]