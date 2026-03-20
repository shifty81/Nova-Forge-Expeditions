"""Tests for ai_dev/tools/hot_reload.py"""
import shutil, tempfile, unittest
from pathlib import Path
from unittest.mock import MagicMock
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tools.hot_reload import HotReloadManager
from tools.ipc_bridge import IPCBridge


class TestHotReloadInit(unittest.TestCase):
    def test_default_init(self):
        mgr = HotReloadManager(Path("/tmp/test"))
        self.assertEqual(mgr._stats, {})

    def test_custom_ipc(self):
        ipc = IPCBridge(port=9999)
        mgr = HotReloadManager(Path("/tmp/test"), ipc=ipc)
        self.assertEqual(mgr._ipc.port, 9999)


class TestHotReloadIPC(unittest.TestCase):
    def setUp(self):
        self.ipc = MagicMock(spec=IPCBridge)
        self.mgr = HotReloadManager(Path("/tmp/test"), ipc=self.ipc)

    def test_reload_lua_calls_ipc(self):
        self.ipc.reload_lua.return_value = (True, "ok")
        self.assertTrue(self.mgr.reload_lua("scripts/equip.lua"))
        self.ipc.reload_lua.assert_called_once()

    def test_reload_glsl_calls_ipc(self):
        self.ipc.reload_glsl.return_value = (True, "ok")
        self.assertTrue(self.mgr.reload_glsl("shaders/pbr.frag"))

    def test_reload_json_calls_ipc(self):
        self.ipc.reload_json.return_value = (True, "ok")
        self.assertTrue(self.mgr.reload_json("data/ships.json"))


class TestHotReloadStats(unittest.TestCase):
    def setUp(self):
        self.ipc = MagicMock(spec=IPCBridge)
        self.ipc.reload_lua.return_value = (True, "ok")
        self.mgr = HotReloadManager(Path("/tmp/test"), ipc=self.ipc)

    def test_stats_empty(self): self.assertEqual(self.mgr.get_stats(), {})

    def test_stats_increment(self):
        self.mgr.reload_lua("scripts/a.lua")
        self.assertEqual(self.mgr.get_stats()["scripts/a.lua"], 1)

    def test_stats_multiple(self):
        for _ in range(3): self.mgr.reload_lua("scripts/a.lua")
        self.assertEqual(self.mgr.get_stats()["scripts/a.lua"], 3)


class TestTypeDetection(unittest.TestCase):
    def setUp(self): self.mgr = HotReloadManager(Path("/tmp/test"))
    def test_lua(self): self.assertEqual(self.mgr._detect_type("x.lua"), "lua")
    def test_frag(self): self.assertEqual(self.mgr._detect_type("x.frag"), "glsl")
    def test_json(self): self.assertEqual(self.mgr._detect_type("x.json"), "json")
    def test_cpp(self): self.assertEqual(self.mgr._detect_type("x.cpp"), "cpp")


if __name__ == "__main__": unittest.main()
