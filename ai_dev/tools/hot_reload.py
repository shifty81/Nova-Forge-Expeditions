"""
NovaForge Dev AI — Hot Reload Manager (Phase 1 + Phase 2)
Watches source files for changes and triggers appropriate reload mechanisms.
"""
import logging
import sys
import time
import importlib
import importlib.util
import threading
from pathlib import Path
from typing import Callable, Optional

from tools.ipc_bridge import IPCBridge

log = logging.getLogger(__name__)


class HotReloadManager:
    def __init__(self, repo_root: Path, ipc: Optional[IPCBridge] = None):
        self.repo_root = repo_root
        self._watches: dict = {}
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._interval = 0.5
        self._ipc = ipc or IPCBridge()
        self._stats: dict = {}

    def watch(self, rel_path: str, file_type: str = "auto",
              callback: Optional[Callable[[str], None]] = None):
        if file_type == "auto":
            ext = Path(rel_path).suffix.lower()
            file_type = {".lua": "lua", ".py": "python", ".vert": "glsl",
                         ".frag": "glsl", ".glsl": "glsl", ".json": "json",
                         ".cpp": "cpp", ".h": "cpp"}.get(ext, "unknown")
        full = self.repo_root / rel_path
        mtime = full.stat().st_mtime if full.exists() else 0.0
        self._watches[rel_path] = {"type": file_type, "mtime": mtime, "callback": callback}

    def unwatch(self, rel_path: str):
        self._watches.pop(rel_path, None)

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)

    def check_all(self):
        for rel_path in list(self._watches.keys()):
            self._check_file(rel_path)

    def reload_lua(self, rel_path: str) -> bool:
        ok, _ = self._ipc.reload_lua(rel_path)
        self._record_reload(rel_path)
        return ok

    def reload_python(self, module_name: str) -> bool:
        try:
            mod = sys.modules.get(module_name)
            if mod:
                importlib.reload(mod)
                return True
        except Exception as e:
            log.warning(f"Python reload failed for {module_name}: {e}")
        return False

    def reload_glsl(self, rel_path: str) -> bool:
        ok, _ = self._ipc.reload_glsl(rel_path)
        self._record_reload(rel_path)
        return ok

    def reload_json(self, rel_path: str) -> bool:
        ok, _ = self._ipc.reload_json(rel_path)
        self._record_reload(rel_path)
        return ok

    def reload_ui(self, rel_path: str) -> bool:
        ok, _ = self._ipc.reload_ui(rel_path)
        self._record_reload(rel_path)
        return ok

    def reload_batch(self, paths: list) -> dict:
        results = {}
        for rel_path in paths:
            info = self._watches.get(rel_path)
            ftype = info["type"] if info else self._detect_type(rel_path)
            results[rel_path] = self._reload_by_type(ftype, rel_path)
        return results

    def get_stats(self) -> dict:
        return dict(self._stats)

    def _poll_loop(self):
        while self._running:
            for rel_path in list(self._watches.keys()):
                self._check_file(rel_path)
            time.sleep(self._interval)

    def _check_file(self, rel_path: str):
        info = self._watches.get(rel_path)
        if not info:
            return
        full = self.repo_root / rel_path
        try:
            mtime = full.stat().st_mtime
        except OSError:
            return
        if mtime == info["mtime"]:
            return
        info["mtime"] = mtime
        self._dispatch(rel_path, info)

    def _dispatch(self, rel_path: str, info: dict):
        ftype = info["type"]
        self._reload_by_type(ftype, rel_path)
        callback = info.get("callback")
        if callback:
            try:
                callback(rel_path)
            except Exception as e:
                log.warning(f"Hot-reload callback error for {rel_path}: {e}")

    def _reload_by_type(self, ftype: str, rel_path: str) -> bool:
        if ftype == "lua":
            return self.reload_lua(rel_path)
        elif ftype == "python":
            return self.reload_python(Path(rel_path).stem)
        elif ftype == "glsl":
            return self.reload_glsl(rel_path)
        elif ftype == "json":
            return self.reload_json(rel_path)
        elif ftype == "ui":
            return self.reload_ui(rel_path)
        return False

    def _detect_type(self, rel_path: str) -> str:
        ext = Path(rel_path).suffix.lower()
        return {".lua": "lua", ".py": "python", ".vert": "glsl", ".frag": "glsl",
                ".glsl": "glsl", ".json": "json", ".xml": "ui",
                ".cpp": "cpp", ".h": "cpp"}.get(ext, "unknown")

    def _record_reload(self, rel_path: str):
        self._stats[rel_path] = self._stats.get(rel_path, 0) + 1
