"""
NovaForge Dev AI — File Operations (Phase 0)
Safe read/write/snapshot/rollback for project files.
"""
import os
import shutil
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)


class FileOps:
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.snapshots_dir = repo_root / "ai_dev" / "workspace" / "snapshots"
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)

    def read_file(self, rel_path: str) -> Optional[str]:
        full = self.repo_root / rel_path
        if not full.exists():
            log.warning(f"File not found: {rel_path}")
            return None
        try:
            return full.read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            log.error(f"Cannot read {rel_path}: {e}")
            return None

    def list_dir(self, rel_path: str = "") -> list:
        target = self.repo_root / rel_path
        if not target.is_dir():
            return []
        entries = []
        for item in sorted(target.iterdir()):
            rel = str(item.relative_to(self.repo_root))
            entries.append({"path": rel, "is_dir": item.is_dir(),
                             "size": item.stat().st_size if item.is_file() else 0})
        return entries

    def file_exists(self, rel_path: str) -> bool:
        return (self.repo_root / rel_path).exists()

    def write_file(self, rel_path: str, content: str, snapshot_label: str = "auto") -> bool:
        full = self.repo_root / rel_path
        if full.exists():
            self._snapshot_single_file(rel_path, snapshot_label)
        full.parent.mkdir(parents=True, exist_ok=True)
        try:
            full.write_text(content, encoding="utf-8")
            log.info(f"Written: {rel_path}")
            return True
        except OSError as e:
            log.error(f"Cannot write {rel_path}: {e}")
            return False

    def create_file(self, rel_path: str, content: str) -> bool:
        full = self.repo_root / rel_path
        if full.exists():
            log.warning(f"File already exists: {rel_path}")
            return False
        return self.write_file(rel_path, content)

    def delete_file(self, rel_path: str, snapshot_label: str = "before_delete") -> bool:
        full = self.repo_root / rel_path
        if not full.exists():
            return False
        self._snapshot_single_file(rel_path, snapshot_label)
        try:
            full.unlink()
            return True
        except OSError:
            return False

    def apply_diff(self, rel_path: str, old_str: str, new_str: str) -> bool:
        content = self.read_file(rel_path)
        if content is None:
            return False
        if old_str not in content:
            log.warning(f"Patch target not found in {rel_path}.")
            return False
        return self.write_file(rel_path, content.replace(old_str, new_str, 1))

    def list_snapshots(self) -> list:
        if not self.snapshots_dir.exists():
            return []
        return [d.name for d in sorted(self.snapshots_dir.iterdir()) if d.is_dir()]

    def rollback_snapshot(self, snapshot_name: str) -> bool:
        snap_dir = self.snapshots_dir / snapshot_name
        if not snap_dir.is_dir():
            return False
        restored = 0
        for snap_file in snap_dir.rglob("*"):
            if not snap_file.is_file():
                continue
            rel = str(snap_file.relative_to(snap_dir))
            dest = self.repo_root / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            try:
                shutil.copy2(snap_file, dest)
                restored += 1
            except OSError:
                pass
        return restored > 0

    def _snapshot_single_file(self, rel_path: str, label: str, ts=None) -> bool:
        full = self.repo_root / rel_path
        if not full.exists():
            return False
        if ts is None:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        snap_dest = self.snapshots_dir / f"{label}_{ts}" / rel_path
        snap_dest.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copy2(full, snap_dest)
            return True
        except OSError:
            return False
