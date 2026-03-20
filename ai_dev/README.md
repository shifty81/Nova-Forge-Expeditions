# NovaForge Dev AI — Quick-Start Guide

Fully offline, in-project AI development assistant for NovaForge.
All inference runs locally via [Ollama](https://ollama.com) or LM Studio — no
internet required after the initial model download.

---

## Prerequisites

**Python 3.8+** required. Python 3.10+ recommended.

### 1. Install Ollama (recommended)
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### 2. Pull a coding model
```bash
# Best results for C++:
ollama pull deepseek-coder

# Alternatives:
ollama pull codellama:13b
ollama pull qwen2.5-coder:7b
ollama pull mistral:7b
```

### 3. Python dependencies
```bash
pip install requests
```

---

## Running the Agent Loop

### Interactive mode (default)

```bash
cd Nova-Forge-Expeditions/ai_dev
python core/agent_loop.py
```

### CLI mode (non-interactive)

```bash
python core/agent_loop.py --prompt "Show me all ECS systems missing a .cpp"
python core/agent_loop.py --auto "Add a stub FleetDebriefSystem with tests" --auto-approve
python core/agent_loop.py --auto "Fix the linker errors" -n 10 --auto-approve
```

---

## Commands

| Command | Description |
|---------|-------------|
| `<prompt>` | Send a natural language prompt to the AI |
| `build` | Run cmake build and optionally send errors to AI |
| `test [name]` | Build and run tests (all, or a specific test binary) |
| `auto <prompt>` | Auto-iterate: prompt → code → build → fix → repeat |
| `scaffold <name> [comp]` | Generate ECS system stubs (header, .cpp, test) |
| `status` | Show project dashboard (git, LLM, IPC, build, missing) |
| `missing` | List ECS systems missing .cpp or test files |
| `git <subcmd>` | Git operations (status/diff/log/commit/branch/stash) |
| `watch [path] [type]` | Watch a file for hot-reload (or list watched files) |
| `reload <path>` | Manually trigger hot-reload for a file |
| `snapshot [label]` | Snapshot the workspace |
| `rollback` | Roll back files to a previous snapshot |
| `history` | Show session's prompt/response history |
| `clear` | Clear session history |
| `help` | Show help message |
| `exit` | Exit the agent loop |

---

## Implementation Phases

See [docs/design/NOVADEV_AI.md](../docs/design/NOVADEV_AI.md) for the full
7-phase design specification.

| Phase | Goal | Status |
|-------|------|--------|
| 0 | Seed Baseline — agent loop, LLM, file ops, build runner | ✅ Complete |
| 1 | Iteration Tools — auto-iterate, test runner, git ops, scaffold, CLI mode | ✅ Complete |
| 2 | Hot Reload + Multi-Lang — IPC bridge, C#/.NET, GLSL validation, prompt templates | ✅ Complete |
| 3 | Overlay — AIPromptPanel + AISuggestionPanel in tooling overlay | 📋 Planned |
| 4 | Placement + PCG — free-move placement, PCG learning | 📋 Planned |
| 5 | GUI + Shaders — Atlas UI / GLSL generation on the fly | 📋 Planned |
| 6 | Asset Generation — Blender bridge for props from prompts | 📋 Planned |
| 7 | Full Automation — test-gen, release pipeline, multi-agent | 📋 Planned |

---

## Running Tests

```bash
cd Nova-Forge-Expeditions
python -m unittest discover -s ai_dev/tests -v
```

---

## Models

See [`models/README.md`](models/README.md) for recommended model selection and
hardware requirements.
