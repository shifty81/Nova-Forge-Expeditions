"""
NovaForge Dev AI — PCG Learner (Phase 4)
Records user-approved object placements for procedural generation learning.
"""
import json
import logging
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)


class PCGLearner:
    def __init__(self, repo_root: Path):
        self._db_path = repo_root / "ai_dev" / "workspace" / "pcg_placements.json"
        self._records: list = self._load()

    def record_placement(self, object_type, room_type, position_relative,
                         wall_proximity=0.5, orientation_deg=0, style_tags=None, approved=True):
        record = {"object_type": object_type, "room_type": room_type,
                  "position_relative": list(position_relative),
                  "wall_proximity": round(wall_proximity, 3),
                  "orientation_deg": orientation_deg,
                  "style_tags": style_tags or [], "approved": approved}
        self._records.append(record)
        self._save()

    def suggest_placement(self, object_type, room_type) -> Optional[dict]:
        matches = [r for r in self._records
                   if r["object_type"] == object_type and r["room_type"] == room_type and r["approved"]]
        if not matches:
            matches = [r for r in self._records
                       if r["object_type"] == object_type and r["approved"]]
        if not matches:
            return None
        xs = [r["position_relative"][0] for r in matches]
        ys = [r["position_relative"][1] for r in matches]
        zs = [r["position_relative"][2] for r in matches]
        avg_wall = sum(r["wall_proximity"] for r in matches) / len(matches)
        return {"position_relative": [round(sum(xs)/len(xs), 3),
                                       round(sum(ys)/len(ys), 3),
                                       round(sum(zs)/len(zs), 3)],
                "wall_proximity": round(avg_wall, 3),
                "orientation_deg": matches[-1]["orientation_deg"],
                "based_on": len(matches)}

    def stats(self) -> dict:
        return {"total": len(self._records),
                "approved": sum(1 for r in self._records if r["approved"]),
                "unique_types": len({r["object_type"] for r in self._records})}

    def _load(self) -> list:
        if self._db_path.exists():
            try:
                return json.loads(self._db_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                pass
        return []

    def _save(self):
        try:
            self._db_path.parent.mkdir(parents=True, exist_ok=True)
            self._db_path.write_text(json.dumps(self._records, indent=2), encoding="utf-8")
        except OSError as e:
            log.warning(f"Could not save PCG data: {e}")
