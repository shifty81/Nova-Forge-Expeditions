"""
NovaForge Dev AI — Build Runner (Phase 0+2)
Runs CMake builds, test executables, Python/Lua/Blender/C#, and GLSL validation.
"""
import os
import subprocess
import logging
from pathlib import Path
from typing import Optional, Tuple

log = logging.getLogger(__name__)
_SERVER_BUILD_DIR = "cpp_server/build"


class BuildRunner:
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root

    def configure_server(self, build_type: str = "Release") -> Tuple[str, bool]:
        build_dir = self.repo_root / _SERVER_BUILD_DIR
        build_dir.mkdir(parents=True, exist_ok=True)
        cmd = ["cmake", "..", f"-DCMAKE_BUILD_TYPE={build_type}",
               "-DBUILD_TESTS=ON", "-DUSE_STEAM_SDK=OFF"]
        return self._run(cmd, cwd=build_dir)

    def build_server(self, target: Optional[str] = None, jobs: Optional[int] = None) -> Tuple[str, bool]:
        build_dir = self.repo_root / _SERVER_BUILD_DIR
        if not (build_dir / "CMakeCache.txt").exists():
            out, ok = self.configure_server()
            if not ok:
                return out, False
        j = jobs or os.cpu_count() or 4
        cmd = ["cmake", "--build", ".", f"-j{j}"]
        if target:
            cmd += ["--target", target]
        return self._run(cmd, cwd=build_dir)

    def run_test(self, test_name: str) -> Tuple[str, bool]:
        bin_path = self.repo_root / _SERVER_BUILD_DIR / "bin" / test_name
        if not bin_path.exists():
            out, ok = self.build_server(target=test_name)
            if not ok:
                return out, False
        return self._run([str(bin_path)], cwd=self.repo_root / _SERVER_BUILD_DIR)

    def run_all_tests(self) -> Tuple[str, bool]:
        return self.run_test("test_systems")

    def run_python(self, rel_script: str, args: Optional[list] = None) -> Tuple[str, bool]:
        script = self.repo_root / rel_script
        if not script.exists():
            return f"Script not found: {rel_script}", False
        return self._run(["python", str(script)] + (args or []), cwd=self.repo_root)

    def run_lua(self, rel_script: str, args: Optional[list] = None) -> Tuple[str, bool]:
        script = self.repo_root / rel_script
        if not script.exists():
            return f"Script not found: {rel_script}", False
        return self._run(["lua", str(script)] + (args or []), cwd=self.repo_root)

    def run_blender(self, rel_script: str, args: Optional[list] = None) -> Tuple[str, bool]:
        script = self.repo_root / rel_script
        if not script.exists():
            return f"Blender script not found: {rel_script}", False
        cmd = ["blender", "--background", "--python", str(script)]
        if args:
            cmd += ["--"] + args
        return self._run(cmd, cwd=self.repo_root)

    def run_glsl_validate(self, rel_shader: str) -> Tuple[str, bool]:
        shader = self.repo_root / rel_shader
        if not shader.exists():
            return f"Shader not found: {rel_shader}", False
        return self._run(["glslangValidator", "-V", str(shader)], cwd=self.repo_root)

    def run_dotnet_build(self, rel_project: str = "", configuration: str = "Debug") -> Tuple[str, bool]:
        cwd = self.repo_root / rel_project if rel_project else self.repo_root
        if cwd.is_file():
            cmd = ["dotnet", "build", str(cwd), "-c", configuration]
            cwd = cwd.parent
        else:
            cmd = ["dotnet", "build", "-c", configuration]
        return self._run(cmd, cwd=cwd)

    def run_dotnet_test(self, rel_project: str = "", filter_expr: str = "") -> Tuple[str, bool]:
        cwd = self.repo_root / rel_project if rel_project else self.repo_root
        if cwd.is_file():
            cmd = ["dotnet", "test", str(cwd)]
            cwd = cwd.parent
        else:
            cmd = ["dotnet", "test"]
        if filter_expr:
            cmd += ["--filter", filter_expr]
        return self._run(cmd, cwd=cwd)

    def validate_glsl_dir(self, rel_dir: str = "engine/shaders") -> Tuple[str, bool]:
        shader_dir = self.repo_root / rel_dir
        if not shader_dir.is_dir():
            return f"Shader directory not found: {rel_dir}", False
        results: list[str] = []
        all_ok = True
        exts = {".vert", ".frag", ".glsl", ".geom", ".tesc", ".tese", ".comp"}
        for path in sorted(shader_dir.rglob("*")):
            if path.suffix.lower() not in exts:
                continue
            rel = str(path.relative_to(self.repo_root))
            out, ok = self.run_glsl_validate(rel)
            if ok:
                results.append(f"  ✓ {rel}")
            else:
                results.append(f"  ✗ {rel}\n    {out}")
                all_ok = False
        if not results:
            return f"No shaders found in {rel_dir}", True
        return f"GLSL validation ({len(results)} shader(s)):\n" + "\n".join(results), all_ok

    def run_command(self, cmd: list, cwd: Optional[str] = None) -> Tuple[str, bool]:
        work_dir = Path(cwd) if cwd else self.repo_root
        return self._run(cmd, cwd=work_dir)

    def _run(self, cmd: list, cwd: Path, timeout: int = 300) -> Tuple[str, bool]:
        log.info(f"Running: {' '.join(str(c) for c in cmd)}")
        try:
            result = subprocess.run([str(c) for c in cmd], cwd=str(cwd),
                                    capture_output=True, text=True, timeout=timeout)
            combined = ""
            if result.stdout:
                combined += result.stdout
            if result.stderr:
                combined += ("\n" if combined else "") + result.stderr
            return combined.strip(), result.returncode == 0
        except subprocess.TimeoutExpired:
            return f"Command timed out after {timeout}s", False
        except FileNotFoundError as e:
            return f"Command not found: {cmd[0]} — {e}", False
        except Exception as e:
            return f"Command failed: {e}", False
