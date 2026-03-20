"""
NovaForge Dev AI — Git Operations (Phase 1)
"""
import logging
import subprocess
from pathlib import Path
from typing import Optional, Tuple, List

log = logging.getLogger(__name__)


class GitOps:
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root

    def status(self) -> Tuple[str, bool]:
        return self._run(["git", "status", "--short"])

    def diff(self, staged: bool = False, path: Optional[str] = None) -> Tuple[str, bool]:
        cmd = ["git", "diff", "--no-color"]
        if staged:
            cmd.append("--cached")
        if path:
            cmd += ["--", path]
        return self._run(cmd)

    def log_oneline(self, count: int = 10) -> Tuple[str, bool]:
        return self._run(["git", "log", "--oneline", f"-{count}"])

    def current_branch(self) -> str:
        out, ok = self._run(["git", "rev-parse", "--abbrev-ref", "HEAD"])
        return out.strip() if ok else "(unknown)"

    def is_clean(self) -> bool:
        out, ok = self.status()
        return ok and out.strip() == ""

    def changed_files(self) -> List[str]:
        out, _ = self._run(["git", "diff", "--name-only"])
        staged, _ = self._run(["git", "diff", "--cached", "--name-only"])
        files = set()
        for line in (out + "\n" + staged).splitlines():
            line = line.strip()
            if line:
                files.add(line)
        return sorted(files)

    def add(self, paths: Optional[List[str]] = None) -> Tuple[str, bool]:
        cmd = ["git", "add"]
        if paths:
            cmd += paths
        else:
            cmd.append("-A")
        return self._run(cmd)

    def commit(self, message: str) -> Tuple[str, bool]:
        if not message.strip():
            return "Empty commit message.", False
        return self._run(["git", "commit", "-m", message])

    def create_branch(self, name: str) -> Tuple[str, bool]:
        return self._run(["git", "checkout", "-b", name])

    def checkout(self, target: str) -> Tuple[str, bool]:
        return self._run(["git", "checkout", target])

    def stash(self) -> Tuple[str, bool]:
        return self._run(["git", "stash"])

    def stash_pop(self) -> Tuple[str, bool]:
        return self._run(["git", "stash", "pop"])

    def checkpoint(self, message: str) -> Tuple[str, bool]:
        out_add, ok_add = self.add()
        if not ok_add:
            return out_add, False
        return self.commit(message)

    def summary_for_llm(self) -> str:
        branch = self.current_branch()
        status_out, _ = self.status()
        lines = [
            f"Branch: {branch}",
            f"Changed files:\n{status_out}" if status_out.strip() else "Working tree clean.",
        ]
        return "\n".join(lines)

    def _run(self, cmd: list, timeout: int = 30) -> Tuple[str, bool]:
        log.debug(f"Git: {' '.join(cmd)}")
        try:
            result = subprocess.run(cmd, cwd=str(self.repo_root),
                                    capture_output=True, text=True, timeout=timeout)
            combined = ""
            if result.stdout:
                combined += result.stdout
            if result.stderr:
                combined += ("\n" if combined else "") + result.stderr
            return combined.strip(), result.returncode == 0
        except subprocess.TimeoutExpired:
            return f"Git command timed out after {timeout}s", False
        except FileNotFoundError:
            return "git not found on PATH", False
        except Exception as e:
            return f"Git error: {e}", False
