"""
NovaForge Dev AI — Feedback Parser (Phase 0)
Parses raw compiler/linker/runtime output into structured error records.
"""
import re
import logging
from typing import NamedTuple, List

log = logging.getLogger(__name__)


class BuildError(NamedTuple):
    file: str
    line: int
    col: int
    severity: str
    code: str
    message: str


_GCC_RE = re.compile(
    r"^(?P<file>[^:\n]+):(?P<line>\d+):(?P<col>\d+):\s*(?P<sev>error|warning|note):\s*(?P<msg>.+)$",
    re.MULTILINE)
_MSVC_RE = re.compile(
    r"^(?P<file>[^\n(]+)\((?P<line>\d+)(?:,(?P<col>\d+))?\)\s*:\s*(?P<sev>error|warning|note)\s+(?P<code>[A-Z0-9]+):\s*(?P<msg>.+)$",
    re.MULTILINE)
_LINKER_RE = re.compile(
    r"(?:undefined reference to|unresolved external symbol)\s+[`'\"]?([^\s`\'\"])+[`\'\"]?",
    re.MULTILINE)
_PYTHON_RE = re.compile(r'File "(?P<file>[^"]+)", line (?P<line>\d+)', re.MULTILINE)


class FeedbackParser:
    def parse(self, output: str) -> List[BuildError]:
        errors: List[BuildError] = []
        errors.extend(self._parse_gcc(output))
        errors.extend(self._parse_msvc(output))
        errors.extend(self._parse_linker(output))
        errors.extend(self._parse_python(output))
        seen: set = set()
        unique: List[BuildError] = []
        for e in errors:
            key = (e.file, e.line, e.message[:80])
            if key not in seen:
                seen.add(key)
                unique.append(e)
        return unique

    def format_for_llm(self, errors: List[BuildError], max_errors: int = 10) -> str:
        if not errors:
            return "Build succeeded — no errors."
        lines = [f"Build failed with {len(errors)} error(s):\n"]
        for i, e in enumerate(errors[:max_errors]):
            loc = f"{e.file}:{e.line}" if e.line else e.file
            code = f" [{e.code}]" if e.code else ""
            lines.append(f"  {i+1}. [{e.severity.upper()}]{code} {loc}: {e.message}")
        if len(errors) > max_errors:
            lines.append(f"  ... and {len(errors) - max_errors} more.")
        return "\n".join(lines)

    def has_errors(self, errors: List[BuildError]) -> bool:
        return any(e.severity == "error" for e in errors)

    def has_linker_errors(self, output: str) -> bool:
        return bool(_LINKER_RE.search(output))

    def extract_missing_symbols(self, output: str) -> List[str]:
        return [m.group(1) for m in _LINKER_RE.finditer(output)]

    @staticmethod
    def _parse_gcc(output: str) -> List[BuildError]:
        errors = []
        for m in _GCC_RE.finditer(output):
            errors.append(BuildError(file=m.group("file").strip(), line=int(m.group("line")),
                                     col=int(m.group("col")), severity=m.group("sev"),
                                     code="", message=m.group("msg").strip()))
        return errors

    @staticmethod
    def _parse_msvc(output: str) -> List[BuildError]:
        errors = []
        for m in _MSVC_RE.finditer(output):
            errors.append(BuildError(file=m.group("file").strip(), line=int(m.group("line")),
                                     col=int(m.group("col") or "0"), severity=m.group("sev").lower(),
                                     code=m.group("code"), message=m.group("msg").strip()))
        return errors

    @staticmethod
    def _parse_linker(output: str) -> List[BuildError]:
        errors = []
        for m in _LINKER_RE.finditer(output):
            errors.append(BuildError(file="(linker)", line=0, col=0, severity="error",
                                     code="LNK", message=f"Undefined symbol: {m.group(1)}"))
        return errors

    @staticmethod
    def _parse_python(output: str) -> List[BuildError]:
        errors = []
        for m in _PYTHON_RE.finditer(output):
            errors.append(BuildError(file=m.group("file"), line=int(m.group("line")), col=0,
                                     severity="error", code="PY",
                                     message="Python exception (see traceback)"))
        return errors
