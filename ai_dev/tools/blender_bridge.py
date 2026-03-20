"""
NovaForge Dev AI — Blender Bridge (Phase 6)
Generates 3D props/ships by calling Blender Python API headlessly.
"""
import json
import logging
import tempfile
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)


class BlenderBridge:
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.generated_dir = repo_root / "assets" / "props" / "generated"
        self.generated_dir.mkdir(parents=True, exist_ok=True)
        self._blender_exe = self._find_blender()

    def is_available(self) -> bool:
        return self._blender_exe is not None

    def generate_prop(self, name, description=None, dimensions_m=None,
                      style_tags=None, output_path=None):
        if not self.is_available():
            log.error("Blender not found.")
            return None
        out = (self.repo_root / output_path if output_path
               else self.generated_dir / f"{name.lower().replace(' ', '_')}.glb")
        script = self._build_prop_script(name, description or "", dimensions_m, style_tags, str(out))
        return self._run_blender_script(script, out)

    def generate_ship(self, faction="generic", ship_class="frigate", output_path=None):
        if not self.is_available():
            log.error("Blender not found.")
            return None
        out = (self.repo_root / output_path if output_path
               else self.generated_dir / f"ship_{faction}_{ship_class}.glb")
        script = f'''
import bpy, sys, json
sys.path.insert(0, r"{self.repo_root / 'tools' / 'BlenderSpaceshipGenerator'}")
import generate_ship_cli
generate_ship_cli.generate(faction="{faction}", ship_class="{ship_class}", output=r"{out}")
'''
        return self._run_blender_script(script, out)

    def _build_prop_script(self, name, description, dimensions_m, style_tags, output_path):
        w, h, d = dimensions_m if dimensions_m else (1.0, 1.0, 1.0)
        tags = json.dumps(style_tags or [])
        return f'''
import bpy
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()
bpy.ops.mesh.primitive_cube_add(size=1)
obj = bpy.context.active_object
obj.name = "{name}"
obj.scale = ({w/2}, {d/2}, {h/2})
obj["ai_description"] = "{description}"
obj["ai_style_tags"] = {tags}
bpy.ops.export_scene.gltf(filepath=r"{output_path}", export_format="GLB", use_selection=True)
'''

    def _run_blender_script(self, script, expected_output):
        from tools.build_runner import BuildRunner
        runner = BuildRunner(self.repo_root)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
            f.write(script)
            temp_path = f.name
        try:
            cmd = [self._blender_exe, "--background", "--python", temp_path]
            out, ok = runner.run_command(cmd)
            if ok and Path(expected_output).exists():
                rel = str(Path(expected_output).relative_to(self.repo_root))
                return rel
            log.error(f"[BlenderBridge] Generation failed: {out}")
            return None
        finally:
            import os
            try:
                os.unlink(temp_path)
            except OSError:
                pass

    @staticmethod
    def _find_blender():
        import os, shutil
        custom = os.environ.get("BLENDER_PATH")
        if custom and Path(custom).exists():
            return custom
        found = shutil.which("blender")
        if found:
            return found
        for candidate in [
            r"C:\Program Files\Blender Foundation\Blender 4.2\blender.exe",
            r"C:\Program Files\Blender Foundation\Blender 4.0\blender.exe",
        ]:
            if Path(candidate).exists():
                return candidate
        return None
