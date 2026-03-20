"""
NovaForge Dev AI — Plugin / Extension Loader
Loads optional agent plugins from ai_dev/plugins/.
"""
import json
import importlib.util
import logging
from pathlib import Path
from typing import Callable, Optional, List

log = logging.getLogger(__name__)


class PluginTool:
    __slots__ = ("name", "description", "run", "plugin_name")

    def __init__(self, name, description, run_fn, plugin_name):
        self.name = name
        self.description = description
        self.run = run_fn
        self.plugin_name = plugin_name


class PluginLoader:
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.plugins_dir = repo_root / "ai_dev" / "plugins"
        self._tools: dict = {}
        self._loaded_plugins: List[str] = []

    def load_all(self) -> int:
        if not self.plugins_dir.exists():
            return 0
        loaded = 0
        for entry in sorted(self.plugins_dir.iterdir()):
            if not entry.is_dir():
                continue
            if not (entry / "plugin.json").exists():
                continue
            if self._load_plugin(entry):
                loaded += 1
        return loaded

    def get_tool(self, name: str) -> Optional[PluginTool]:
        return self._tools.get(name)

    def list_tools(self) -> List[PluginTool]:
        return list(self._tools.values())

    def list_plugins(self) -> List[str]:
        return list(self._loaded_plugins)

    def _load_plugin(self, plugin_dir: Path) -> bool:
        manifest_path = plugin_dir / "plugin.json"
        init_path = plugin_dir / "__init__.py"
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            log.warning(f"Plugin {plugin_dir.name}: bad manifest — {e}")
            return False
        name = manifest.get("name", plugin_dir.name)
        if not init_path.exists():
            log.warning(f"Plugin {name}: missing __init__.py")
            return False
        try:
            spec = importlib.util.spec_from_file_location(f"novaforge_plugin_{name}", init_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        except Exception as e:
            log.error(f"Plugin {name}: failed to load — {e}")
            return False
        tool_names = manifest.get("tools", [])
        registered = 0
        for tool_name in tool_names:
            tool_module = getattr(module, tool_name, None)
            if tool_module is None:
                continue
            run_fn = getattr(tool_module, "run", None)
            if run_fn is None:
                continue
            desc = getattr(tool_module, "TOOL_DESCRIPTION", tool_name)
            full_name = getattr(tool_module, "TOOL_NAME", tool_name)
            self._tools[full_name] = PluginTool(full_name, desc, run_fn, name)
            registered += 1
        if registered:
            self._loaded_plugins.append(name)
        return registered > 0
