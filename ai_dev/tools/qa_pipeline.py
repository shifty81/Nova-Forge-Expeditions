"""
QA Pipeline — automated testing, build capture, and asset validation.
"""
import json
import os
import re
import subprocess
from pathlib import Path


class QAPipeline:
    """Automated QA helpers for builds, tests, and asset validation."""

    def run_unit_tests(self, test_binary_path, output_file=None):
        try:
            result = subprocess.run([test_binary_path], capture_output=True,
                                    text=True, timeout=120)
            out = result.stdout + result.stderr
            if output_file:
                Path(output_file).write_text(out, encoding="utf-8")
            return result.returncode == 0, out
        except Exception as e:
            return False, str(e)

    def run_all_server_tests(self, build_dir):
        bin_dir = Path(build_dir) / "bin"
        results = {}
        if not bin_dir.exists():
            return results
        for binary in sorted(bin_dir.glob("test_*")):
            if binary.is_file() and os.access(binary, os.X_OK):
                ok, out = self.run_unit_tests(str(binary))
                results[binary.name] = {"passed": ok, "lines": len(out.splitlines())}
        return results

    def check_media_files(self, asset_dir):
        valid_exts = {".png", ".jpg", ".jpeg", ".dds", ".wav", ".ogg", ".mp3",
                      ".glb", ".fbx", ".obj", ".glsl", ".hlsl", ".json"}
        issues = []
        for f in Path(asset_dir).rglob("*"):
            if f.is_file():
                if f.suffix.lower() not in valid_exts:
                    issues.append(f"Unknown extension: {f}")
                elif f.stat().st_size == 0:
                    issues.append(f"Empty file: {f}")
        return issues

    def validate_json_schema(self, json_path, schema_path=None):
        try:
            with open(json_path, encoding="utf-8") as fh:
                json.load(fh)
            return True, None
        except (json.JSONDecodeError, OSError) as e:
            return False, str(e)

    def run_build_and_capture(self, build_dir, target=None):
        cmd = ["cmake", "--build", build_dir, "--parallel"]
        if target:
            cmd += ["--target", target]
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            return r.returncode == 0, r.stdout + r.stderr
        except Exception as e:
            return False, str(e)

    def analyse_build_output(self, output):
        lines = output.splitlines()
        errors = [l for l in lines if "error:" in l.lower()]
        warnings = [l for l in lines if "warning:" in l.lower()]
        return {"errors": len(errors), "warnings": len(warnings),
                "error_lines": errors[:10], "warning_lines": warnings[:10]}
