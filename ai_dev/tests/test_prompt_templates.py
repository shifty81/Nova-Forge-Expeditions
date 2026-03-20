"""Tests for ai_dev/core/prompt_templates.py"""
import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core.prompt_templates import PromptTemplates


class TestSubsystemDetection(unittest.TestCase):
    def setUp(self): self.t = PromptTemplates()
    def test_cpp_server_header(self):
        self.assertEqual(self.t.detect_subsystem("cpp_server/include/systems/foo.h"), "cpp_server")
    def test_cpp_client(self):
        self.assertEqual(self.t.detect_subsystem("cpp_client/src/camera.cpp"), "cpp_client")
    def test_engine(self):
        self.assertEqual(self.t.detect_subsystem("engine/src/ECS.cpp"), "engine")
    def test_editor(self):
        self.assertEqual(self.t.detect_subsystem("editor/src/Main.cpp"), "editor")
    def test_python_ai_dev(self):
        self.assertEqual(self.t.detect_subsystem("ai_dev/tools/build_runner.py"), "python")
    def test_glsl_frag(self):
        self.assertEqual(self.t.detect_subsystem("shaders/pbr.frag"), "glsl")
    def test_lua_script(self):
        self.assertEqual(self.t.detect_subsystem("scripts/equipment.lua"), "lua")
    def test_csharp(self):
        self.assertEqual(self.t.detect_subsystem("tools/Editor.cs"), "csharp")
    def test_json_data(self):
        self.assertEqual(self.t.detect_subsystem("data/ships.json"), "json")
    def test_unknown(self):
        self.assertEqual(self.t.detect_subsystem("file.xyz"), "")


class TestForSubsystem(unittest.TestCase):
    def setUp(self): self.t = PromptTemplates()
    def test_cpp_server(self):
        t = self.t.for_subsystem("cpp_server")
        self.assertIn("snake_case", t)
        self.assertIn("SingleComponentSystem", t)
    def test_engine(self):
        t = self.t.for_subsystem("engine")
        self.assertIn("PascalCase", t)
    def test_unknown(self):
        self.assertEqual(self.t.for_subsystem("nonexistent"), "")


class TestEnrichPrompt(unittest.TestCase):
    def setUp(self): self.t = PromptTemplates()
    def test_enrich_with_subsystem(self):
        r = self.t.enrich_prompt("Fix bug", subsystem="cpp_server")
        self.assertIn("Fix bug", r)
    def test_enrich_no_match(self):
        r = self.t.enrich_prompt("Hello world")
        self.assertEqual(r, "Hello world")


class TestAvailableSubsystems(unittest.TestCase):
    def test_returns_sorted_list(self):
        t = PromptTemplates()
        s = t.available_subsystems()
        self.assertEqual(s, sorted(s))
        self.assertIn("cpp_server", s)
        self.assertIn("engine", s)
        self.assertIn("python", s)


if __name__ == "__main__": unittest.main()
