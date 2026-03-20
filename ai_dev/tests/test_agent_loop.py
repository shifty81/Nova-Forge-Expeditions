"""Tests for ai_dev/core/agent_loop.py"""
import json, os, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core.agent_loop import AgentLoop


class TestExtractFileChanges(unittest.TestCase):
    def test_single_cpp_block(self):
        response = "```cpp cpp_server/src/systems/foo.cpp\nint x = 1;\n```\n"
        changes = AgentLoop._extract_file_changes(response)
        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0]["path"], "cpp_server/src/systems/foo.cpp")

    def test_multiple_blocks(self):
        response = ("```cpp cpp_server/include/a.h\n#pragma once\n```\n"
                    "```cpp cpp_server/src/a.cpp\n// impl\n```\n")
        changes = AgentLoop._extract_file_changes(response)
        self.assertEqual(len(changes), 2)

    def test_no_path_in_block(self):
        changes = AgentLoop._extract_file_changes("```cpp\nint x = 1;\n```\n")
        self.assertEqual(len(changes), 0)

    def test_empty_response(self):
        self.assertEqual(AgentLoop._extract_file_changes(""), [])

    def test_unclosed_block(self):
        changes = AgentLoop._extract_file_changes("```cpp cpp_server/src/x.cpp\nint x = 1;\n")
        self.assertEqual(len(changes), 0)


class TestAgentLoopInit(unittest.TestCase):
    def test_default_init(self):
        a = AgentLoop()
        self.assertFalse(a.auto_approve)
        self.assertEqual(a.max_iterations, 5)

    def test_auto_approve_init(self):
        a = AgentLoop(auto_approve=True, max_iterations=10)
        self.assertTrue(a.auto_approve)
        self.assertEqual(a.max_iterations, 10)


class TestAutoApprove(unittest.TestCase):
    def test_ask_yes_no_auto(self):
        a = AgentLoop(auto_approve=True)
        self.assertTrue(a._ask_yes_no("any question"))


class TestDispatch(unittest.TestCase):
    def test_help_dispatch(self):
        a = AgentLoop()
        with patch.object(a, "_print_help") as m:
            a._dispatch("help")
            m.assert_called_once()

    def test_build_dispatch(self):
        a = AgentLoop()
        with patch.object(a, "_cmd_build") as m:
            a._dispatch("build")
            m.assert_called_once()

    def test_clear_dispatch(self):
        a = AgentLoop()
        a.session_history = [{"role": "user", "content": "test"}]
        a._dispatch("clear")
        self.assertEqual(len(a.session_history), 0)

    def test_prompt_dispatch(self):
        a = AgentLoop()
        with patch.object(a, "_handle_prompt") as m:
            a._dispatch("Show me all ECS systems")
            m.assert_called_once_with("Show me all ECS systems")

    def test_scaffold_dispatch(self):
        a = AgentLoop()
        with patch.object(a, "_cmd_scaffold") as m:
            a._dispatch("scaffold fleet_debrief fleet_components.h")
            m.assert_called_once_with("fleet_debrief fleet_components.h")


if __name__ == "__main__": unittest.main()
