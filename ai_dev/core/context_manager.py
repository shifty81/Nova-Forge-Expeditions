"""
NovaForge Dev AI — Context Manager (Phase 0)

Builds relevant project context to include with every LLM prompt.
Indexes source files by type and prioritises the most relevant ones
based on keywords in the prompt.
"""

import os
import json
import logging
from pathlib import Path
from typing import Optional, Dict

log = logging.getLogger(__name__)

# Files / dirs to always skip
_SKIP_DIRS = {
    ".git", "build", "bin", "obj", ".cache", "__pycache__",
    "node_modules", ".vs", ".vscode", "CMakeFiles", "_deps",
    "workspace", "snapshots",
}
_SKIP_EXTS = {
    ".o", ".obj", ".a", ".lib", ".so", ".dll", ".exe",
    ".png", ".jpg", ".jpeg", ".bmp", ".tga", ".dds",
    ".fbx", ".glb", ".gltf", ".blend",
    ".wav", ".ogg", ".mp3",
    ".zip", ".7z", ".tar", ".gz",
    ".pyc", ".pyd",
}

# Source file categories
_SOURCE_EXTS = {".cpp", ".h", ".hpp", ".py", ".lua", ".cs",
                ".vert", ".frag", ".glsl", ".json", ".cmake", ".txt"}

# Maximum characters fed into the context window per prompt
MAX_CONTEXT_CHARS = 12_000


class ContextManager:
    """
    Maintains a searchable index of the project's source files and assembles
    focused context snippets for each AI prompt.
    """

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self._index: "Dict[str, str]" = {}  # relative_path → content
        self._memory_path = repo_root / "ai_dev" / "workspace" / "project_memory.json"
        self._memory: dict = self._load_memory()
        self._index_built = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def build_index(self, force: bool = False):
        """Scan the repository and index all source files."""
        if self._index_built and not force:
            return
        log.info(f"Indexing repository at {self.repo_root} ...")
        count = 0
        for path in self.repo_root.rglob("*"):
            if not path.is_file():
                continue
            if any(part in _SKIP_DIRS for part in path.parts):
                continue
            if path.suffix.lower() in _SKIP_EXTS:
                continue
            if path.suffix.lower() not in _SOURCE_EXTS:
                continue
            try:
                rel = str(path.relative_to(self.repo_root))
                self._index[rel] = path.read_text(encoding="utf-8", errors="replace")
                count += 1
            except (OSError, PermissionError):
                pass
        self._index_built = True
        log.info(f"Indexed {count} files.")

    def get_context_for_prompt(self, prompt: str, max_chars: int = MAX_CONTEXT_CHARS) -> str:
        """
        Return a context string of the most relevant source files for the prompt.
        Includes project memory, coding conventions, and scored file snippets.
        """
        if not self._index_built:
            self.build_index()

        # Score every indexed file by keyword relevance
        scored = self._score_files(prompt)
        scored.sort(key=lambda x: x[1], reverse=True)

        # Build context up to budget
        parts = []

        # Always include coding guidelines summary
        guidelines = self._get_guidelines_summary()
        if guidelines:
            parts.append(f"=== CODING CONVENTIONS ===\n{guidelines}\n")
            max_chars -= len(guidelines)

        # Include per-project memory notes
        if self._memory.get("notes"):
            mem_text = "\n".join(self._memory["notes"][-10:])
            parts.append(f"=== PROJECT MEMORY ===\n{mem_text}\n")
            max_chars -= len(mem_text)

        remaining = max_chars
        for rel_path, _score in scored[:20]:
            if remaining <= 0:
                break
            content = self._index.get(rel_path, "")
            snippet = content[:min(len(content), remaining, 3000)]
            entry = f"=== FILE: {rel_path} ===\n{snippet}\n"
            parts.append(entry)
            remaining -= len(entry)

        return "\n".join(parts)

    def get_file(self, rel_path: str) -> Optional[str]:
        """Return the content of a specific file (by relative path)."""
        full = self.repo_root / rel_path
        if full.exists():
            try:
                return full.read_text(encoding="utf-8", errors="replace")
            except OSError:
                pass
        return self._index.get(rel_path)

    def list_systems_missing_cpp(self) -> list:
        """Return a list of system header names that have no matching .cpp."""
        systems_h = [
            p for p in self._index
            if p.startswith("cpp_server/include/systems/") and p.endswith(".h")
        ]
        result = []
        for h in systems_h:
            base = Path(h).stem  # e.g. fleet_debrief_system
            cpp = f"cpp_server/src/systems/{base}.cpp"
            test = f"cpp_server/tests/test_{base}.cpp"
            if cpp not in self._index or test not in self._index:
                result.append({
                    "header": h,
                    "has_cpp": cpp in self._index,
                    "has_test": test in self._index,
                })
        return result

    def add_memory_note(self, note: str):
        """Persist a project-scoped note for future sessions."""
        self._memory.setdefault("notes", []).append(note)
        self._save_memory()

    def invalidate_file(self, rel_path: str):
        """Re-read a specific file (after an edit)."""
        full = self.repo_root / rel_path
        if full.exists():
            try:
                self._index[rel_path] = full.read_text(encoding="utf-8", errors="replace")
            except OSError:
                pass

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _score_files(self, prompt: str) -> list:
        """
        Score each indexed file by how many prompt keywords appear in its
        path or content.  Returns list of (rel_path, score).
        """
        # Extract meaningful words from the prompt
        words = set(
            w.lower().strip(".,?!/()[]{}\"'")
            for w in prompt.split()
            if len(w) > 3
        )
        scored = []
        for rel_path, content in self._index.items():
            path_lower = rel_path.lower()
            content_lower = content.lower()
            score = 0.0
            for word in words:
                if word in path_lower:
                    score += 3.0
                count = content_lower.count(word)
                score += min(count * 0.1, 2.0)
            if score > 0:
                scored.append((rel_path, score))
        return scored

    def _get_guidelines_summary(self) -> str:
        """Return a concise summary of the coding guidelines."""
        # Try to read the actual guidelines file
        g = self.repo_root / "docs" / "CODING_GUIDELINES.md"
        if g.exists():
            try:
                text = g.read_text(encoding="utf-8", errors="replace")
                return text[:2000]
            except OSError:
                pass
        # Fallback inline summary
        return (
            "snake_case filenames/methods/vars in cpp_server/ and cpp_client/.\n"
            "PascalCase filenames/methods in engine/ and editor/.\n"
            "m_camelCase members in engine/editor/. Trailing snake_case_ in cpp_server/.\n"
            "All code in namespace atlas. Sub-namespaces: ecs, systems, components, network, pcg, sim.\n"
            "ECS systems extend SingleComponentSystem<TComponent>.\n"
            "Use #ifndef NOVAFORGE_<SUBSYSTEM>_<FILE>_H include guards.\n"
            "Use atlas::Logger, never std::cout.\n"
        )

    def _load_memory(self) -> dict:
        if self._memory_path.exists():
            try:
                return json.loads(self._memory_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                pass
        return {}

    def _save_memory(self):
        try:
            self._memory_path.parent.mkdir(parents=True, exist_ok=True)
            self._memory_path.write_text(
                json.dumps(self._memory, indent=2), encoding="utf-8"
            )
        except OSError as e:
            log.warning(f"Could not save project memory: {e}")
