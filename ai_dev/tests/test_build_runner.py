"""Tests for ai_dev/tools/build_runner.py"""
import shutil, tempfile, unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tools.build_runner import BuildRunner


class TestDotnetBuild(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.runner = BuildRunner(Path(self.tmp))
    def tearDown(self): shutil.rmtree(self.tmp, ignore_errors=True)

    @patch.object(BuildRunner, "_run")
    def test_dotnet_build_default(self, mock_run):
        mock_run.return_value = ("Build succeeded.", True)
        _, ok = self.runner.run_dotnet_build()
        self.assertTrue(ok)
        cmd = mock_run.call_args[0][0]
        self.assertIn("dotnet", cmd)
        self.assertIn("build", cmd)

    @patch.object(BuildRunner, "_run")
    def test_dotnet_build_release(self, mock_run):
        mock_run.return_value = ("Build succeeded.", True)
        self.runner.run_dotnet_build(configuration="Release")
        cmd = mock_run.call_args[0][0]
        self.assertIn("Release", cmd)

    @patch.object(BuildRunner, "_run")
    def test_dotnet_test_default(self, mock_run):
        mock_run.return_value = ("Passed: 10", True)
        _, ok = self.runner.run_dotnet_test()
        self.assertTrue(ok)
        cmd = mock_run.call_args[0][0]
        self.assertIn("test", cmd)

    @patch.object(BuildRunner, "_run")
    def test_dotnet_test_with_filter(self, mock_run):
        mock_run.return_value = ("Passed: 5", True)
        self.runner.run_dotnet_test(filter_expr="Category=Unit")
        cmd = mock_run.call_args[0][0]
        self.assertIn("--filter", cmd)
        self.assertIn("Category=Unit", cmd)


class TestGLSLDirValidation(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.runner = BuildRunner(Path(self.tmp))
    def tearDown(self): shutil.rmtree(self.tmp, ignore_errors=True)

    def test_missing_shader_dir(self):
        out, ok = self.runner.validate_glsl_dir("nonexistent/dir")
        self.assertFalse(ok)
        self.assertIn("not found", out)

    def test_empty_shader_dir(self):
        (Path(self.tmp) / "engine/shaders").mkdir(parents=True)
        out, ok = self.runner.validate_glsl_dir("engine/shaders")
        self.assertTrue(ok)
        self.assertIn("No shaders found", out)

    @patch.object(BuildRunner, "run_glsl_validate")
    def test_all_shaders_pass(self, mock_validate):
        mock_validate.return_value = ("", True)
        shader_dir = Path(self.tmp) / "engine/shaders"
        shader_dir.mkdir(parents=True)
        (shader_dir / "test.vert").write_text("")
        (shader_dir / "test.frag").write_text("")
        out, ok = self.runner.validate_glsl_dir("engine/shaders")
        self.assertTrue(ok)
        self.assertIn("✓", out)


if __name__ == "__main__": unittest.main()
