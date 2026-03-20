"""Tests for ai_dev/tools/ecs_scaffold.py"""
import os, shutil, tempfile, unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tools.ecs_scaffold import ECSScaffold, _snake_to_pascal, _pascal_to_snake


class TestNamingHelpers(unittest.TestCase):
    def test_snake_to_pascal(self):
        self.assertEqual(_snake_to_pascal("fleet_debrief"), "FleetDebrief")
        self.assertEqual(_snake_to_pascal("combat"), "Combat")
    def test_pascal_to_snake(self):
        self.assertEqual(_pascal_to_snake("FleetDebrief"), "fleet_debrief")


class TestECSScaffold(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.repo = Path(self.tmp)
        for d in ["cpp_server/include/systems", "cpp_server/include/components",
                  "cpp_server/src/systems", "cpp_server/tests"]:
            (self.repo / d).mkdir(parents=True)
        self.scaffold = ECSScaffold(self.repo)

    def tearDown(self): shutil.rmtree(self.tmp, ignore_errors=True)

    def test_generate_dry_run(self):
        files = self.scaffold.generate("fleet_debrief", dry_run=True)
        self.assertIn("cpp_server/include/systems/fleet_debrief_system.h", files)
        self.assertIn("cpp_server/src/systems/fleet_debrief_system.cpp", files)
        self.assertIn("cpp_server/tests/test_fleet_debrief_system.cpp", files)
        self.assertFalse((self.repo / "cpp_server/include/systems/fleet_debrief_system.h").exists())

    def test_generate_writes_files(self):
        self.scaffold.generate("fleet_debrief")
        self.assertTrue((self.repo / "cpp_server/include/systems/fleet_debrief_system.h").exists())
        self.assertTrue((self.repo / "cpp_server/src/systems/fleet_debrief_system.cpp").exists())
        self.assertTrue((self.repo / "cpp_server/tests/test_fleet_debrief_system.cpp").exists())

    def test_auto_adds_system_suffix(self):
        files = self.scaffold.generate("mining_laser", dry_run=True)
        self.assertIn("cpp_server/include/systems/mining_laser_system.h", files)

    def test_header_contains_guard(self):
        files = self.scaffold.generate("fleet_debrief", dry_run=True)
        h = files["cpp_server/include/systems/fleet_debrief_system.h"]
        self.assertIn("#ifndef NOVAFORGE_SYSTEMS_FLEET_DEBRIEF_SYSTEM_H", h)

    def test_header_contains_class(self):
        files = self.scaffold.generate("fleet_debrief", dry_run=True)
        h = files["cpp_server/include/systems/fleet_debrief_system.h"]
        self.assertIn("class FleetDebriefSystem", h)
        self.assertIn("FleetDebriefState", h)

    def test_cpp_contains_implementation(self):
        files = self.scaffold.generate("fleet_debrief", dry_run=True)
        cpp = files["cpp_server/src/systems/fleet_debrief_system.cpp"]
        self.assertIn("FleetDebriefSystem::FleetDebriefSystem", cpp)
        self.assertIn("namespace atlas", cpp)

    def test_component_snippet(self):
        files = self.scaffold.generate("fleet_debrief", dry_run=True)
        self.assertIn("FleetDebriefState", files["__component_snippet__"])

    def test_registration_instructions(self):
        instr = self.scaffold.registration_instructions("fleet_debrief")
        self.assertIn("CMakeLists.txt", instr)
        self.assertIn("fleet_debrief_system", instr)

    def test_list_missing_systems(self):
        h = self.repo / "cpp_server/include/systems/orphan_system.h"
        h.write_text("// orphan")
        missing = self.scaffold.list_missing_systems()
        self.assertEqual(len(missing), 1)
        self.assertEqual(missing[0]["system"], "orphan_system")


if __name__ == "__main__": unittest.main()
