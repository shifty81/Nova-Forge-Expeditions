"""Tests for ai_dev/tools/git_ops.py"""
import subprocess, unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tools.git_ops import GitOps


class TestGitOps(unittest.TestCase):
    def setUp(self):
        self.git = GitOps(Path("/tmp/test_repo"))

    @patch("subprocess.run")
    def test_status(self, mock_run):
        mock_run.return_value = MagicMock(stdout=" M file.cpp\n", stderr="", returncode=0)
        out, ok = self.git.status()
        self.assertTrue(ok)
        self.assertIn("file.cpp", out)

    @patch("subprocess.run")
    def test_current_branch(self, mock_run):
        mock_run.return_value = MagicMock(stdout="main\n", stderr="", returncode=0)
        self.assertEqual(self.git.current_branch(), "main")

    @patch("subprocess.run")
    def test_current_branch_failure(self, mock_run):
        mock_run.return_value = MagicMock(stdout="", stderr="err", returncode=1)
        self.assertEqual(self.git.current_branch(), "(unknown)")

    @patch("subprocess.run")
    def test_is_clean_true(self, mock_run):
        mock_run.return_value = MagicMock(stdout="", stderr="", returncode=0)
        self.assertTrue(self.git.is_clean())

    @patch("subprocess.run")
    def test_is_clean_false(self, mock_run):
        mock_run.return_value = MagicMock(stdout=" M dirty.py", stderr="", returncode=0)
        self.assertFalse(self.git.is_clean())

    def test_commit_empty_message(self):
        out, ok = self.git.commit("")
        self.assertFalse(ok)

    @patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="git", timeout=30))
    def test_timeout(self, mock_run):
        out, ok = self.git.status()
        self.assertFalse(ok)
        self.assertIn("timed out", out)

    @patch("subprocess.run", side_effect=FileNotFoundError("git"))
    def test_git_not_found(self, mock_run):
        out, ok = self.git.status()
        self.assertFalse(ok)
        self.assertIn("not found", out)


if __name__ == "__main__": unittest.main()
