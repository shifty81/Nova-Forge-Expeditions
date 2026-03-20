"""
NovaForge Dev AI — Agent Loop (Phase 0 + Phase 1)

Main entry point for the offline AI development assistant.
Runs an interactive prompt session using a local LLM (Ollama / LM Studio).

Features added in Phase 1:
  - Auto-iterate: prompt → code → build → parse errors → LLM fix (up to N rounds)
  - Test runner: build and run per-system or all tests
  - ECS scaffold: generate system stubs from a single command
  - Git operations: status, diff, commit changes made by AI
  - Session resume: reload previous session history on startup
  - CLI / batch mode: pass prompts on the command line for non-interactive use
  - Status dashboard: show project health at a glance

Usage:
    # Interactive mode
    python core/agent_loop.py

    # CLI mode (non-interactive)
    python core/agent_loop.py --prompt "Add a stub FleetDebriefSystem"
    python core/agent_loop.py --auto "Fix all build errors in the server"

Environment:
    LLM_MODEL      - Model name (default: deepseek-coder)
    LLM_BASE_URL   - API endpoint (default: http://localhost:11434)
    NOVAFORGE_ROOT - Repository root (default: auto-detected)
"""

import argparse
import os
import sys
import json
from pathlib import Path

# ---------------------------------------------------------------------------
# Bootstrap: locate the repository root
# ---------------------------------------------------------------------------
_this_dir = Path(__file__).resolve().parent
_repo_root = _this_dir.parent.parent  # ai_dev/core/ -> ai_dev/ -> repo root
sys.path.insert(0, str(_this_dir.parent))

from core.llm_interface import LocalLLM
from core.context_manager import ContextManager
from core.prompt_templates import PromptTemplates
from tools.file_ops import FileOps
from tools.build_runner import BuildRunner
from tools.feedback_parser import FeedbackParser
from tools.git_ops import GitOps
from tools.ecs_scaffold import ECSScaffold
from tools.hot_reload import HotReloadManager
from tools.ipc_bridge import IPCBridge

WORKSPACE_DIR = _this_dir.parent / "workspace"
SESSION_LOG = WORKSPACE_DIR / "session_log.json"

# Maximum auto-iterate rounds to prevent infinite loops
DEFAULT_MAX_ITERATIONS = 5


class AgentLoop:
    """Core prompt → plan → execute → feedback loop."""

    def __init__(self, auto_approve: bool = False, max_iterations: int = DEFAULT_MAX_ITERATIONS):
        repo_root = Path(os.environ.get("NOVAFORGE_ROOT", str(_repo_root)))
        self.repo_root = repo_root
        self.llm = LocalLLM()
        self.context = ContextManager(repo_root)
        self.file_ops = FileOps(repo_root)
        self.build_runner = BuildRunner(repo_root)
        self.feedback_parser = FeedbackParser()
        self.git_ops = GitOps(repo_root)
        self.scaffold = ECSScaffold(repo_root)
        self.templates = PromptTemplates()
        self.ipc = IPCBridge()
        self.hot_reload = HotReloadManager(repo_root, ipc=self.ipc)
        self.session_history = []
        self.auto_approve = auto_approve
        self.max_iterations = max_iterations
        WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self):
        """Start the interactive prompt loop."""
        self._load_session_log()

        print("=" * 60)
        print("  NovaForge Dev AI — Offline Development Assistant")
        print("  Type 'help' for commands, 'exit' to quit.")
        if self.session_history:
            turns = len([h for h in self.session_history if h["role"] == "user"])
            print(f"  Resumed session with {turns} previous prompt(s).")
        print("=" * 60)
        print()

        while True:
            try:
                user_input = input("NovaForge Dev AI> ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\nExiting.")
                break

            if not user_input:
                continue

            self._dispatch(user_input)

        self._save_session_log()

    def run_single(self, prompt: str):
        """Run a single prompt non-interactively and exit."""
        self._load_session_log()
        self._handle_prompt(prompt)
        self._save_session_log()

    def run_auto(self, prompt: str):
        """Run auto-iterate: prompt → code → build → fix → rebuild (up to N rounds)."""
        self._load_session_log()
        self._cmd_auto_iterate(prompt)
        self._save_session_log()

    # ------------------------------------------------------------------
    # Command dispatch
    # ------------------------------------------------------------------

    def _dispatch(self, user_input: str):
        """Route user input to the correct handler."""
        cmd = user_input.lower()

        if cmd in ("exit", "quit", "q"):
            print("Goodbye.")
            self._save_session_log()
            sys.exit(0)
        elif cmd == "help":
            self._print_help()
        elif cmd == "build":
            self._cmd_build()
        elif cmd.startswith("test"):
            arg = user_input[len("test"):].strip()
            self._cmd_test(arg if arg else None)
        elif cmd.startswith("auto "):
            prompt = user_input[len("auto "):].strip()
            if prompt:
                self._cmd_auto_iterate(prompt)
            else:
                print("[Auto] Usage: auto <prompt>")
        elif cmd.startswith("scaffold "):
            args = user_input[len("scaffold "):].strip()
            self._cmd_scaffold(args)
        elif cmd.startswith("snapshot"):
            label = user_input[len("snapshot"):].strip() or "manual"
            self.file_ops.snapshot_workspace(label)
            print(f"[Snapshot] Workspace snapshotted as '{label}'.")
        elif cmd == "rollback":
            self._cmd_rollback()
        elif cmd == "history":
            self._print_history()
        elif cmd == "status":
            self._cmd_status()
        elif cmd == "missing":
            self._cmd_missing()
        elif cmd.startswith("git "):
            subcmd = user_input[len("git "):].strip()
            self._cmd_git(subcmd)
        elif cmd.startswith("watch "):
            arg = user_input[len("watch "):].strip()
            self._cmd_watch(arg)
        elif cmd.startswith("reload "):
            arg = user_input[len("reload "):].strip()
            self._cmd_reload(arg)
        elif cmd == "clear":
            self.session_history.clear()
            print("[Session] History cleared.")
        else:
            self._handle_prompt(user_input)

    # ------------------------------------------------------------------
    # Command handlers
    # ------------------------------------------------------------------

    def _handle_prompt(self, prompt: str):
        """Send a prompt to the LLM and handle the response."""
        print("[AI] Gathering project context...")
        ctx = self.context.get_context_for_prompt(prompt)

        # Enrich prompt with language-specific template if a file path is mentioned
        enriched = self.templates.enrich_prompt(prompt)

        print("[AI] Querying local LLM...")
        response = self.llm.query(enriched, ctx, self.session_history)
        if response is None:
            print("[AI] LLM unavailable. Is Ollama running? Try: ollama serve")
            return

        print()
        print("-" * 60)
        print(response)
        print("-" * 60)

        # Record in session history
        self.session_history.append({"role": "user", "content": prompt})
        self.session_history.append({"role": "assistant", "content": response})

        # Check if the response contains a file change suggestion
        file_changes = self._extract_file_changes(response)
        if file_changes:
            self._offer_apply(file_changes)

    def _cmd_build(self):
        """Run the server build and feed errors back to the LLM."""
        print("[Build] Running cmake --build cpp_server/build ...")
        output, success = self.build_runner.build_server()
        print(output)
        if success:
            print("[Build] ✓ Build succeeded.")
        else:
            errors = self.feedback_parser.parse(output)
            print(f"[Build] ✗ Build failed with {len(errors)} error(s).")
            if errors and self._ask_yes_no("Send errors to AI for analysis?"):
                error_prompt = "Build failed. Errors:\n" + "\n".join(
                    f"- {e.file}:{e.line}: {e.message}"
                    for e in errors
                )
                self._handle_prompt(error_prompt)

    def _cmd_test(self, test_name=None):
        """Build and run a test binary."""
        if test_name:
            print(f"[Test] Building and running {test_name} ...")
            output, success = self.build_runner.run_test(test_name)
        else:
            print("[Test] Building and running all tests ...")
            output, success = self.build_runner.run_all_tests()
        print(output)
        if success:
            print("[Test] ✓ Tests passed.")
        else:
            errors = self.feedback_parser.parse(output)
            if errors:
                print(f"[Test] ✗ {len(errors)} error(s) found.")
            else:
                print("[Test] ✗ Test run failed (see output above).")
            if self._ask_yes_no("Send output to AI for analysis?"):
                error_prompt = f"Test failed. Output:\n{output[-3000:]}"
                self._handle_prompt(error_prompt)

    def _cmd_auto_iterate(self, prompt: str):
        """
        Auto-iteration loop: prompt → code → build → parse errors →
        LLM fix → rebuild, up to max_iterations rounds.
        """
        print(f"[Auto] Starting auto-iterate (max {self.max_iterations} rounds)...")
        self.file_ops.snapshot_workspace("before_auto")

        for iteration in range(1, self.max_iterations + 1):
            print(f"\n{'='*60}")
            print(f"  Auto-Iterate — Round {iteration}/{self.max_iterations}")
            print(f"{'='*60}")

            # Step 1: Prompt the LLM
            print("[Auto] Gathering context...")
            ctx = self.context.get_context_for_prompt(prompt)

            print("[Auto] Querying LLM...")
            response = self.llm.query(prompt, ctx, self.session_history)
            if response is None:
                print("[Auto] LLM unavailable. Stopping.")
                return

            print()
            print("-" * 40)
            print(response[:2000])
            if len(response) > 2000:
                print(f"... ({len(response) - 2000} chars truncated)")
            print("-" * 40)

            self.session_history.append({"role": "user", "content": prompt})
            self.session_history.append({"role": "assistant", "content": response})

            # Step 2: Extract and apply file changes
            file_changes = self._extract_file_changes(response)
            if file_changes:
                print(f"\n[Auto] Applying {len(file_changes)} file change(s):")
                for change in file_changes:
                    self.file_ops.write_file(change["path"], change["content"])
                    self.context.invalidate_file(change["path"])
                    print(f"  ✓ {change['path']}")
            else:
                print("[Auto] No file changes extracted from LLM response.")
                if iteration > 1:
                    print("[Auto] LLM did not propose more changes. Stopping.")
                    return
                continue

            # Step 3: Build
            print("\n[Auto] Building...")
            output, success = self.build_runner.build_server()
            if success:
                print("[Auto] ✓ Build succeeded!")
                # Step 3b: Optionally run tests
                print("[Auto] Running tests...")
                test_out, test_ok = self.build_runner.run_all_tests()
                if test_ok:
                    print("[Auto] ✓ All tests passed! Auto-iterate complete.")
                else:
                    print("[Auto] ⚠ Build OK but tests failed.")
                    print(test_out[-1000:])
                return

            # Step 4: Parse errors and build the next prompt
            errors = self.feedback_parser.parse(output)
            print(f"[Auto] Build failed with {len(errors)} error(s).")

            error_text = self.feedback_parser.format_for_llm(errors)
            prompt = (
                f"The previous code changes did not compile. "
                f"Fix the following errors:\n\n{error_text}\n\n"
                f"Show the corrected file(s) using the ```lang path/to/file``` format."
            )

        print(f"\n[Auto] Reached max iterations ({self.max_iterations}). Stopping.")
        print("[Auto] Use 'rollback' to undo all auto-iterate changes.")

    def _cmd_scaffold(self, args: str):
        """Generate ECS system boilerplate files."""
        parts = args.split()
        if not parts:
            print("[Scaffold] Usage: scaffold <system_name> [component_file]")
            print("  Example: scaffold fleet_debrief fleet_components.h")
            return

        system_name = parts[0]
        component_file = parts[1] if len(parts) > 1 else "game_components.h"

        print(f"[Scaffold] Generating {system_name} (component file: {component_file})...")
        files = self.scaffold.generate(system_name, component_file, dry_run=False)

        for rel_path, _content in files.items():
            if rel_path.startswith("__"):
                continue
            print(f"  ✓ {rel_path}")

        # Show the component snippet for manual insertion
        snippet = files.get("__component_snippet__", "")
        if snippet:
            print(f"\n[Scaffold] Add this component to cpp_server/include/components/{component_file}:")
            print(snippet)

        # Show registration instructions
        print(self.scaffold.registration_instructions(system_name))

    def _cmd_status(self):
        """Show project status dashboard."""
        print("\n=== NovaForge Dev AI — Status ===\n")

        # Git status
        branch = self.git_ops.current_branch()
        print(f"Branch:  {branch}")
        status_out, _ = self.git_ops.status()
        if status_out.strip():
            changed_count = len(status_out.strip().splitlines())
            print(f"Changed: {changed_count} file(s)")
        else:
            print("Changed: working tree clean")

        # LLM status
        if self.llm.is_available():
            print(f"LLM:     ✓ available ({self.llm.model} @ {self.llm.base_url})")
        else:
            print("LLM:     ✗ not reachable (run: ollama serve)")

        # Engine IPC status
        if self.ipc.is_engine_running():
            print(f"Engine:  ✓ IPC connected ({self.ipc.host}:{self.ipc.port})")
        else:
            print(f"Engine:  ✗ IPC not reachable ({self.ipc.host}:{self.ipc.port})")

        # Hot-reload watches
        watch_count = len(self.hot_reload._watches)
        if watch_count:
            print(f"Watches: {watch_count} file(s) watched for hot-reload")
        else:
            print("Watches: none (use: watch <path>)")

        # Build status
        build_dir = self.repo_root / "cpp_server" / "build"
        if (build_dir / "CMakeCache.txt").exists():
            print("CMake:   ✓ configured")
        else:
            print("CMake:   ✗ not configured (run: build)")

        # Missing systems count
        missing = self.scaffold.list_missing_systems()
        if missing:
            no_cpp = sum(1 for m in missing if not m["has_cpp"])
            no_test = sum(1 for m in missing if not m["has_test"])
            print(f"Missing: {no_cpp} system(s) without .cpp, {no_test} without test")
        else:
            print("Missing: all systems complete ✓")

        # Session
        turns = len([h for h in self.session_history if h["role"] == "user"])
        print(f"Session: {turns} prompt(s) this session")
        print()

    def _cmd_missing(self):
        """List ECS systems missing implementation or test files."""
        missing = self.scaffold.list_missing_systems()
        if not missing:
            print("[Missing] All systems have header, .cpp, and test. ✓")
            return
        print(f"\n[Missing] {len(missing)} system(s) with gaps:\n")
        for m in missing:
            markers = []
            if not m["has_cpp"]:
                markers.append("no .cpp")
            if not m["has_test"]:
                markers.append("no test")
            print(f"  {m['system']:40s} [{', '.join(markers)}]")
        print()

    def _cmd_git(self, subcmd: str):
        """Handle git sub-commands."""
        parts = subcmd.split(None, 1)
        action = parts[0] if parts else ""
        arg = parts[1] if len(parts) > 1 else ""

        if action == "status":
            out, _ = self.git_ops.status()
            print(out if out.strip() else "Working tree clean.")
        elif action == "diff":
            out, _ = self.git_ops.diff(path=arg if arg else None)
            print(out if out.strip() else "No changes.")
        elif action == "log":
            count = int(arg) if arg.isdigit() else 10
            out, _ = self.git_ops.log_oneline(count)
            print(out)
        elif action == "branch":
            print(f"Current branch: {self.git_ops.current_branch()}")
        elif action == "commit":
            if not arg:
                print("[Git] Usage: git commit <message>")
                return
            out, ok = self.git_ops.checkpoint(arg)
            print(out)
            if ok:
                print("[Git] ✓ Committed.")
        elif action == "stash":
            out, ok = self.git_ops.stash()
            print(out)
        elif action == "stash-pop":
            out, ok = self.git_ops.stash_pop()
            print(out)
        else:
            print("""Git sub-commands:
  git status           — Show changed files
  git diff [path]      — Show unified diff
  git log [count]      — Show recent commits
  git branch           — Show current branch
  git commit <message> — Stage all and commit
  git stash            — Stash working changes
  git stash-pop        — Pop stashed changes
""")

    def _cmd_watch(self, args: str):
        """Add a file to the hot-reload watch list."""
        parts = args.split()
        if not parts:
            # Show current watch list
            watches = self.hot_reload._watches
            if not watches:
                print("[Watch] No files being watched. Usage: watch <path> [type]")
                return
            print(f"\n[Watch] {len(watches)} file(s) watched:\n")
            for path, info in watches.items():
                count = self.hot_reload._stats.get(path, 0)
                print(f"  [{info['type']:6s}] {path}  (reloaded {count}x)")
            print()
            return

        rel_path = parts[0]
        file_type = parts[1] if len(parts) > 1 else "auto"
        try:
            self.hot_reload.watch(rel_path, file_type)
            print(f"[Watch] Now watching: {rel_path} [{file_type}]")
        except OSError as e:
            print(f"[Watch] Error: {e}")

    def _cmd_reload(self, args: str):
        """Manually trigger a hot-reload for a file."""
        if not args:
            print("[Reload] Usage: reload <path>")
            return

        rel_path = args.strip()
        info = self.hot_reload._watches.get(rel_path)
        if info:
            ftype = info["type"]
        else:
            ftype = self.hot_reload._detect_type(rel_path)

        ok = self.hot_reload._reload_by_type(ftype, rel_path)
        if ok:
            print(f"[Reload] ✓ Reloaded {rel_path} [{ftype}]")
        else:
            print(f"[Reload] ⚠ Reload signal sent for {rel_path} [{ftype}] "
                  "(engine may not be running)")

    def _cmd_rollback(self):
        """List snapshots and roll back to a chosen one."""
        snapshots = self.file_ops.list_snapshots()
        if not snapshots:
            print("[Rollback] No snapshots found.")
            return
        print("[Rollback] Available snapshots:")
        for i, s in enumerate(snapshots):
            print(f"  {i + 1}. {s}")
        choice = input("Enter snapshot number (or 'cancel'): ").strip()
        if choice.lower() == "cancel":
            return
        try:
            idx = int(choice) - 1
            self.file_ops.rollback_snapshot(snapshots[idx])
            print(f"[Rollback] ✓ Rolled back to '{snapshots[idx]}'.")
        except (ValueError, IndexError):
            print("[Rollback] Invalid selection.")

    def _offer_apply(self, file_changes: list):
        """Show proposed file changes and ask for approval."""
        print()
        print(f"[AI] Proposed changes to {len(file_changes)} file(s):")
        for change in file_changes:
            print(f"  • {change['path']}")
        print()

        if self.auto_approve:
            choice = "yes"
            print("[Auto-approve] Applying changes...")
        else:
            choice = input("Apply these changes? [yes/no/show]: ").strip().lower()

        if choice == "show":
            for change in file_changes:
                print(f"\n--- {change['path']} ---")
                print(change.get("content", "(no content)"))
            choice = input("\nApply? [yes/no]: ").strip().lower()
        if choice in ("yes", "y"):
            self.file_ops.snapshot_workspace("before_ai_edit")
            for change in file_changes:
                self.file_ops.write_file(change["path"], change["content"])
                self.context.invalidate_file(change["path"])
                print(f"[Apply] Wrote {change['path']}")
            print("[Apply] ✓ Changes applied.")
            if not self.auto_approve and self._ask_yes_no("Run build now?"):
                self._cmd_build()
        else:
            print("[Apply] Changes discarded.")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_file_changes(response: str) -> list:
        """
        Naively extract fenced code blocks labelled with a file path.
        Expected format from LLM:
            ```cpp path/to/file.cpp
            ... content ...
            ```
        Returns list of {"path": str, "content": str}.
        """
        changes = []
        lines = response.splitlines()
        in_block = False
        current_path = None
        current_lines = []
        for line in lines:
            if not in_block and line.startswith("```") and len(line) > 3:
                rest = line[3:].strip()
                parts = rest.split(None, 1)
                if len(parts) >= 2:
                    # e.g. ```cpp cpp_server/src/systems/foo_system.cpp
                    current_path = parts[1].strip()
                    current_lines = []
                    in_block = True
                elif len(parts) == 1 and ("/" in parts[0] or "." in parts[0]):
                    # e.g. ```cpp_server/src/systems/foo_system.cpp
                    current_path = parts[0].strip()
                    current_lines = []
                    in_block = True
            elif in_block and line.startswith("```"):
                if current_path:
                    changes.append(
                        {"path": current_path, "content": "\n".join(current_lines)}
                    )
                in_block = False
                current_path = None
                current_lines = []
            elif in_block:
                current_lines.append(line)
        return changes

    def _ask_yes_no(self, question: str) -> bool:
        if self.auto_approve:
            return True
        ans = input(f"{question} [yes/no]: ").strip().lower()
        return ans in ("yes", "y")

    def _print_history(self):
        if not self.session_history:
            print("[History] No history this session.")
            return
        for entry in self.session_history:
            role = entry["role"].upper()
            print(f"\n[{role}] {entry['content'][:200]}{'...' if len(entry['content']) > 200 else ''}")

    def _load_session_log(self):
        """Load previous session history if available."""
        if SESSION_LOG.exists() and not self.session_history:
            try:
                data = json.loads(SESSION_LOG.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    self.session_history = data
            except (OSError, json.JSONDecodeError):
                pass

    def _save_session_log(self):
        try:
            WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)
            with open(SESSION_LOG, "w", encoding="utf-8") as f:
                json.dump(self.session_history, f, indent=2)
        except OSError:
            pass

    @staticmethod
    def _print_help():
        print("""
Commands:
  <prompt>                — Send a natural language prompt to the AI
  build                   — Run cmake build and optionally send errors to AI
  test [name]             — Build and run tests (all, or a specific test binary)
  auto <prompt>           — Auto-iterate: prompt → code → build → fix → repeat
  scaffold <name> [comp]  — Generate ECS system stubs (header, .cpp, test)
  status                  — Show project dashboard (git, LLM, build, missing)
  missing                 — List ECS systems missing .cpp or test files
  git <subcmd>            — Git operations (status/diff/log/commit/branch/stash)
  watch [path] [type]     — Watch a file for hot-reload (or list watched files)
  reload <path>           — Manually trigger hot-reload for a file
  snapshot [label]        — Snapshot the workspace
  rollback                — Roll back files to a previous snapshot
  history                 — Show this session's prompt/response history
  clear                   — Clear session history
  help                    — Show this help message
  exit                    — Exit the agent loop

Auto-iterate example:
  auto Add a stub FleetDebriefSystem with tests and register in CMakeLists

Scaffold example:
  scaffold fleet_debrief fleet_components.h

Watch / Reload examples:
  watch assets/scripts/equip.lua       — Watch a Lua script for changes
  watch shaders/pbr.frag glsl          — Watch with explicit type
  watch                                — List all watched files
  reload assets/scripts/equip.lua      — Manually trigger reload

Git examples:
  git status              — Show changed files
  git diff                — Show working tree diff
  git commit "AI: add fleet_debrief_system"

Example prompts:
  Show me all ECS systems missing a .cpp implementation.
  Add a stub FleetDebriefSystem following the existing pattern.
  The Upgrade button in EquipmentPanel does nothing. Suggest a fix.
  Build fails with a linker error on test_fleet_debrief_system. Fix it.
  Generate CaptainStaminaState component in social_components.h
""")


def _parse_args():
    parser = argparse.ArgumentParser(
        description="NovaForge Dev AI — Offline Development Assistant",
    )
    parser.add_argument(
        "--prompt", "-p",
        help="Run a single prompt non-interactively and exit.",
    )
    parser.add_argument(
        "--auto", "-a",
        dest="auto_prompt",
        help="Run auto-iterate on a prompt (prompt → code → build → fix → repeat).",
    )
    parser.add_argument(
        "--max-iterations", "-n",
        type=int,
        default=DEFAULT_MAX_ITERATIONS,
        help=f"Maximum auto-iterate rounds (default: {DEFAULT_MAX_ITERATIONS}).",
    )
    parser.add_argument(
        "--auto-approve",
        action="store_true",
        help="Auto-approve all AI-proposed changes (skip confirmation prompts).",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    agent = AgentLoop(
        auto_approve=args.auto_approve,
        max_iterations=args.max_iterations,
    )

    if args.auto_prompt:
        agent.run_auto(args.auto_prompt)
    elif args.prompt:
        agent.run_single(args.prompt)
    else:
        agent.run()
