# Nova-Forge: Expeditions — Development Roadmap
### Engine · Tooling · GUI · PCG · AI
> **Scope**: This roadmap covers only Dev Infrastructure, GUI Systems, Procedural Content Generation (PCG), and AI/AtlasForgeAI integration. No game-specific mechanics, combat, economy, or gameplay features are included until all four pillars are solid and refined.

---

## Current State Snapshot

| Pillar | Status | Notes |
|--------|--------|-------|
| Dev Infrastructure | 🔧 In Progress | Build system solid; spaghetti cleanup ~40% done |
| GUI System | ✅ Foundation complete | Widget system, DSL, layout solver, ToolingLayer done |
| PCG | ✅ Foundation complete | WorldGraph, noise, terrain, galaxy done; expansion needed |
| AI / AtlasForgeAI | 🔧 Partial | HttpLLMBackend, editor assistant done; offline loop not built |

---

## Roadmap Overview

```
Phase A  →  Phase B  →  Phase C  →  Phase D  →  Phase E
  Dev          GUI         PCG       AtlasForgeAI  Integration
 Health      Hardening   Expansion   Agent Loop    & Polish
```

All phases can have sub-tasks running in parallel. Phase A must be substantially complete before Phase D. Phases B and C are independent and can advance in parallel.

---

## Phase A — Dev Infrastructure & Code Health

> **Goal**: Clean, fast, maintainable codebase that is easy to build, test, and extend. Every later phase depends on this foundation.

### A1 — Spaghetti Code Cleanup (🔧 Active)

Based on `docs/SPAGHETTI_CODE_AUDIT.md`.

- [x] Extract `novaforge_core` static library from CMakeLists.txt (deduplication)
- [x] Split monolithic `test_systems.cpp` (35K lines → 23 per-domain test files)
- [x] Create `test_framework.h` with shared `assertTrue`, `approxEqual`, `addComp`
- [x] Create `json_helpers.h` for shared JSON parsing across data layer
- [x] Begin `SingleComponentSystem<C>` template migration (CapacitorSystem, ShieldRechargeSystem)
- [ ] Complete `SingleComponentSystem<C>` migration across all applicable systems (~60 remaining)
- [ ] Create `StateMachineSystem<C, PhaseEnum>` template for phase-driven systems
- [ ] Create `RechargeSystem<C>` template for recharge-pattern systems
- [ ] Migrate all 164 server systems to appropriate template bases
- [ ] Create `TestFixture` base class to eliminate remaining test boilerplate
- [ ] Decompose `GameSession` god object into `CombatHandler`, `StationHandler`, `MovementHandler`, `MissionHandler`, `ScannerHandler`
- [ ] CMakeLists.txt: reduce from 668 to < 250 lines; per-subdirectory CMakeLists files

**Target metrics:**
- Largest single source file: < 500 lines
- Average system boilerplate: ~20 lines (down from ~80)
- `GameSession` forward declarations: 0
- CMakeLists.txt lines: < 250

---

### A2 — Build System Consolidation

- [ ] Unify `build.sh` across Atlas-NovaForge and Nova-Forge-Expeditions into a single parameterized script
- [ ] Add `./build.sh ai` target — builds AtlasForgeAI Python stubs alongside C++ targets
- [ ] Add `./build.sh tools` target — builds font atlas generator, contract scanner, replay minimizer standalone
- [ ] Add incremental build support: skip unchanged modules via CMake dependency tracking
- [ ] Add build timing breakdown (per-module compile time report at end of build)
- [ ] Docker-based reproducible build environment (`Dockerfile.dev`) for Linux/Windows cross-build
- [ ] One-command dev environment bootstrap: `./setup.sh --full` installs all dependencies, builds all targets, runs all tests
- [ ] Build artifact signing for certified builds (hash + timestamp manifest)

---

### A3 — Test Infrastructure

- [ ] Per-domain CTest suites: `ctest -R gui`, `ctest -R pcg`, `ctest -R ai` run only relevant tests
- [ ] Add fuzz test harness for GUI DSL parser (libFuzzer or AFL integration)
- [ ] Property-based test harness for PCG node evaluation (random seeds, invariant checks)
- [ ] Add headless UI replay test runner to CI (run all `.atlasreplay` files, assert frame hashes)
- [ ] Add mutation testing target (verify test suite catches real bugs by mutating source)
- [ ] Automated test coverage reporting (gcov/llvm-cov → HTML report in `dist/coverage/`)
- [ ] Contract scanner in CI: fail PR if any layer-boundary violation detected
- [ ] Golden replay CI gate: determinism check on every merge to main

---

### A4 — Developer Tooling

- [ ] `atlas doctor` CLI — diagnose build environment, missing deps, config issues
- [ ] `atlas new-system <name>` CLI — scaffold a new ECS system from template with header, source, test file
- [ ] `atlas new-tool <name>` CLI — scaffold a new editor ToolingLayer tool
- [ ] `atlas new-node <type> <name>` CLI — scaffold a new PCG/UI/Flow graph node
- [ ] Live diagnostics server: expose engine metrics over HTTP (tick rate, memory, system timings) for browser-based monitoring
- [ ] Dev console autocomplete: all registered system names, component types, and PCG node types available via tab completion
- [ ] `atlas diff <replay_a> <replay_b>` CLI — compare two replay files and output divergence report
- [ ] `atlas audit` CLI — run contract scan + determinism check + schema validation in one command

---

### A5 — Documentation & Conventions

- [ ] Auto-generated API docs from source (Doxygen or custom extractor → `docs/api/`)
- [ ] Architecture decision record (ADR) template and process (`docs/adr/` directory)
- [ ] Naming conventions lint rule in CI (enforce `ATLAS_NAMING_CONVENTIONS.md` rules automatically)
- [ ] Living changelog: auto-generated from commit messages, filtered by system tag
- [ ] Contribution guide updated: new contributor bootstrap, first system tutorial, coding contract

---

## Phase B — GUI System Hardening & Expansion

> **Goal**: A production-grade, extensible GUI system that covers all editor and game UI needs with live preview, full theming, animation, and accessibility support. The current foundation is solid; this phase refines and extends it significantly.

### B1 — Widget System Expansion

Current widgets: Panel, Button, Text, Image, List, SlotGrid, InputField.

- [ ] `Checkbox` widget — binary toggle with label, deterministic state
- [ ] `RadioGroup` widget — mutually exclusive option set
- [ ] `Dropdown` / `ComboBox` widget — scrollable option list with search filter
- [ ] `Slider` widget — float/int range input with snap-to-grid support
- [ ] `ProgressBar` widget — determinate and indeterminate modes
- [ ] `TreeView` widget — collapsible hierarchical list (used by ECS inspector, asset browser)
- [ ] `Tooltip` widget — deferred hover text with configurable delay and placement
- [ ] `ContextMenu` widget — right-click popup with nested submenu support
- [ ] `ColorPicker` widget — HSV wheel + RGB hex input (for material editor, theme editor)
- [ ] `NumberField` widget — typed numeric input with increment/decrement arrows and unit labels
- [ ] `SplitView` widget — user-resizable two-pane view (replaces current hardcoded split nodes)
- [ ] `ScrollArea` widget — virtualized scrolling for large lists (1000+ items at no fps cost)
- [ ] `Notification` widget — toast messages with timeout and action buttons
- [ ] `Modal` / `Dialog` widget — blocking overlay with focus trap and keyboard dismiss
- [ ] `TabBar` widget — refactor existing tab groups into a first-class widget
- [ ] `Canvas2D` widget — arbitrary 2D draw surface for graph editors and curve editors

---

### B2 — Layout Solver Hardening

- [ ] Anchored layouts: pin edges to parent (top/bottom/left/right/center) in addition to ratio splits
- [ ] Min/max constraints per axis independently (width range separate from height range)
- [ ] Flex-style wrapping: horizontal/vertical lists that wrap onto new lines when space runs out
- [ ] Overflow handling: scroll, clip, or expand parent — configurable per widget
- [ ] Responsive breakpoints: define layout variants at viewport width thresholds (useful for wide-monitor vs narrow panel layouts)
- [ ] Multi-monitor awareness: correct DPI scaling per monitor, no blurry text on mixed-DPI setups
- [ ] Layout solver formal invariant tests: automated proofs that No-Overlap and Full-Coverage hold after every operation
- [ ] Layout performance budget: O(n) solver pass even for deeply nested trees; profile regression test

---

### B3 — Theme Engine

- [ ] Theme definition format: `theme.atlas.json` with color palette, spacing scale, border radii, font stack
- [ ] Multiple built-in themes: `atlas-dark` (current), `atlas-light`, `atlas-high-contrast`
- [ ] Live theme hot-reload: change `theme.atlas.json` → UI updates without restart
- [ ] Per-panel theme overrides: individual tools can override specific theme tokens
- [ ] Theme editor panel (in ToolingLayer): visual editor for all theme tokens with live preview
- [ ] Token-based system: all widget styles reference semantic tokens (`color.accent`, `spacing.md`) not literal values
- [ ] CSS-like specificity: widget type < class < instance override chain
- [ ] Icon system: SVG icon set compiled to a deterministic sprite atlas; no hardcoded pixel positions
- [ ] DPI-aware icons: 1x / 2x / 3x variants, selected automatically by display DPI

---

### B4 — Animation & Transitions

- [ ] Widget transition system: fade-in/out, slide, scale — expressed as deterministic keyframe data, not float lerps
- [ ] Panel open/close animations: ToolingLayer tools animate in/out smoothly
- [ ] Scroll physics: configurable inertia and easing for scroll areas
- [ ] Loading spinners and skeleton loaders: for async operations (asset loading, AI generation)
- [ ] Cursor-responsive interactions: hover highlight, press scale, release bounce — all data-driven
- [ ] Replay compatibility: all animation state is recorded and replayable (no hidden float accumulator)

---

### B5 — GUI DSL Enhancements

- [ ] `@include` directive: split large layout files into composable fragments
- [ ] `@theme` directive: declare which theme a layout uses
- [ ] Conditional blocks: `@if BUILD_FLAG { ... }` for platform-specific UI variants
- [ ] Data binding syntax: `text = "{{entity.name}}"` — bind widget properties to ECS data
- [ ] Event handler syntax: `on_click = "cmd:OpenInventory"` — link widget events to command bus
- [ ] DSL formatter / pretty-printer: auto-format layout files on save
- [ ] DSL language server: autocomplete and error checking in VS Code via LSP adapter
- [ ] Schema migration: `migrate_dsl.py` tool to upgrade layout files between DSL versions
- [ ] DSL round-trip fidelity test: parse → serialize → compare, must be identical

---

### B6 — Editor UI Panels Refinement

> Refine existing panels; no new game-specific panels.

- [ ] **ECS Inspector**: component tree with inline editing, entity search, pin-entity feature
- [ ] **Graph Editor**: minimap, multi-node select + drag, node group/comment boxes, port type colors
- [ ] **Asset Browser**: thumbnail previews, tag-based filtering, drag-to-scene placement
- [ ] **Console**: REPL with history, syntax highlighting, multi-line input, output filtering by severity
- [ ] **Profiler Panel**: flame graph view, per-system allocation tracking, GPU timing integration
- [ ] **Atlas Assistant Panel**: streaming response display, prompt library, conversation history, diff preview inline
- [ ] **Replay Timeline**: waveform-style input visualization, multi-track comparison, divergence markers
- [ ] **Proof Viewer**: TLA+ syntax highlighting with error underlines, invariant status badges
- [ ] **CI Dashboard**: per-workflow run status, test result breakdown, coverage delta
- [ ] **Theme Editor**: live token editor with immediate preview (new panel)
- [ ] **DSL Editor**: syntax-highlighted `.atlas.layout` file editor with parse errors inline (new panel)

---

### B7 — Headless & CI GUI Mode

- [ ] Headless GUI tick: run full widget tree evaluation per tick with no renderer (already exists for server mode) — expand test coverage
- [ ] Snapshot testing: capture widget tree state at tick N as JSON; compare against golden snapshot
- [ ] Visual regression testing: render GUI to offscreen framebuffer in CI; pixel-compare against golden images
- [ ] GUI coverage report: which widgets/panels were exercised in each test run
- [ ] Replay video export: CI pipeline exports `.mp4` from headless replay + GUI replay combined

---

## Phase C — PCG System Expansion & Refinement

> **Goal**: A comprehensive, data-driven, AI-augmentable PCG pipeline covering worlds, interiors, props, materials, sounds, and placement. All generators are graph-based, seed-reproducible, and hot-reloadable.

### C1 — WorldGraph Node Library Expansion

Current nodes: Perlin, FBM, HeightField, DensityField, Mask, cube-sphere, voxel, terrain mesher.

- [ ] **Voronoi** node — Worley noise with configurable distance metric (Euclidean, Manhattan, Chebyshev)
- [ ] **Domain Warp** node — warp input coordinates before evaluation (organic terrain shapes)
- [ ] **Erosion** node — hydraulic and thermal erosion simulation on heightfields
- [ ] **Ridged FBM** node — sharp mountain ridges
- [ ] **Curl Noise** node — divergence-free noise for fluid-like flow patterns
- [ ] **Blend** node — weighted mix of two value channels with mask
- [ ] **Remap** node — curve-based remap with editable spline (replaces hardcoded linear remaps)
- [ ] **Threshold** / **Classify** node — segment a field into discrete biome bands
- [ ] **Scatter** node — Poisson-disc or stratified sample placement on a surface
- [ ] **Slope** node — derive slope angle from a heightfield gradient
- [ ] **Curvature** node — local concavity/convexity of a surface (useful for erosion, snow, moss placement)
- [ ] **Distance Field** node — signed distance from a shape primitive or mesh
- [ ] **Mask From Biome** node — combine multiple threshold/classify outputs into a biome mask
- [ ] **Combine** node — boolean union/intersection/subtraction of density fields
- [ ] **Tile** node — repeat a sub-graph result across a grid with optional variation
- [ ] Node palette categorization in WorldGraph panel: Noise / Shape / Filter / Combine / Output

---

### C2 — Material & Shader PCG

- [ ] **MaterialGraph** node library: albedo gen, normal gen, roughness gen, AO bake, emissive mask
- [ ] Procedural material blending based on biome mask (rock/sand blend at threshold)
- [ ] Triplanar projection node: eliminate UV stretching on steep terrain
- [ ] Detail material layer: close-up surface variation composited on base material
- [ ] Shader graph hot-reload: change `.atlasshader` → GPU recompile in < 1 second
- [ ] Shader graph debugger: visualize intermediate channel values per-pixel in editor
- [ ] `AtlasShaderIR` determinism test: verify shader output is bit-identical across platforms
- [ ] Material LOD graph: automatically simplify material as camera distance increases
- [ ] Decal system graph: layered world-space decals (damage, weathering, markings)

---

### C3 — Interior & Structural PCG

> For modular architectural space generation (ships, stations, bunkers). Not FPS gameplay — this is the generator system itself.

- [ ] **Grammar-based room graph**: L-system / shape grammar rules that produce room connectivity graphs
- [ ] **Room solver**: pack room graph into 3D space respecting adjacency and size constraints
- [ ] **Corridor connector**: A*-based corridor routing between room entrances
- [ ] **Module palette system**: define a set of modular mesh pieces (wall, corner, door, window) per style tag
- [ ] **Style tag propagation**: assign style (industrial, sci-fi, derelict) at region level; all modules within inherit
- [ ] **Interior detail scatter**: place props, decals, and lights within rooms via scatter + constraint nodes
- [ ] **Structural integrity simulation**: detect floating or unsupported rooms; auto-reinforce
- [ ] **Interior→WorldGraph bridge node**: interior PCG result feeds back into world streaming as a chunk type

---

### C4 — Placement & Scatter Learning

- [ ] **PCG Placement Learner**: observe manual placements in MapEditorTool → extract placement rules as WorldGraph parameters
- [ ] **Constraint-based scatter**: define keep-out zones, required clearances, and surface type requirements per object class
- [ ] **Density map**: author per-area object density with a painted mask in the editor
- [ ] **Hierarchical scatter**: coarse scatter of large objects → fine scatter of small objects that avoid large object footprints
- [ ] **Variation seeding**: each placed instance receives a unique sub-seed for local variation (rotation, scale, material variation)
- [ ] **Placement history log**: every PCG-placed object records its seed, rules applied, and position — enables exact reproduction and delta editing
- [ ] **DeltaEditStore integration**: manual overrides layer on top of PCG placements; PCG re-runs preserve overrides

---

### C5 — PCG Performance & Streaming

- [ ] Async PCG evaluation: WorldGraph nodes execute on worker threads; results stream into the chunk cache
- [ ] GPU-accelerated nodes: noise, erosion, and heightfield nodes optionally run as compute shaders
- [ ] Node result caching: content-addressed cache keyed by (node hash + input hash); skip re-evaluation when inputs unchanged
- [ ] Progressive LOD generation: low-resolution result available immediately; high-resolution refines in background
- [ ] Memory budget tracking: each PCG node declares output memory bounds; total per-chunk budget enforced
- [ ] PCG profiler panel: per-node execution time, cache hit rate, memory usage — integrated in Profiler Panel

---

### C6 — PCG Quality & Debugging

- [ ] **WorldGraph debugger**: breakpoints on nodes, single-step execution, per-node output visualized in viewport
- [ ] **Seed explorer**: UI to sweep a parameter over a range and thumbnail the results
- [ ] **Biome preview panel**: show biome mask, height distribution, moisture, and slope as 2D color maps
- [ ] **Determinism stress test**: run the same WorldGraph with the same seed 1000 times on multiple threads; assert bit-identical output
- [ ] **PCG validation node**: declare output invariants (height in [0,1], density non-negative) — fail fast on rule violation
- [ ] **Regression suite**: golden heightfield snapshots per test scene; CI fails if PCG output drifts

---

### C7 — Audio PCG

- [ ] **SoundGraph expansion**: new nodes for granular synthesis, spectral morphing, and convolution reverb
- [ ] **Environment audio system**: ambient soundscape generated from biome mask (wind strength from height + slope, water from moisture)
- [ ] **Procedural music graph**: melody/harmony/rhythm composed from game state parameters
- [ ] SoundGraph debugger: oscilloscope and frequency spectrum visualization per node
- [ ] Offline audio baking: pre-render common SoundGraph states to `.wav` cache for runtime performance

---

## Phase D — AtlasForgeAI Integration

> **Goal**: Build the full AtlasForgeAI agent loop — an offline-first, multi-language, media-capable AI development assistant that integrates with the engine's ToolingLayer, PCG systems, and build pipeline. This is the "Swiss-army knife" dev system described in the Chat.md planning sessions.

### D1 — Offline LLM Integration

- [ ] **Ollama adapter**: `OllamaLLMBackend` implementing `IAssistantBackend` — connects to local Ollama server on `localhost:11434`
- [ ] **llama.cpp adapter**: `LlamaCppLLMBackend` — direct in-process llama.cpp embedding (no server required)
- [ ] **Model manager panel** (ToolingLayer tool): list available local models, pull new models, set active model
- [ ] **Backend fallback chain**: `[LocalLLM → HttpLLM → OfflineStub]` — auto-downgrade gracefully
- [ ] **Context window budgeting**: estimate token count before sending; truncate context intelligently
- [ ] **Model capability registry**: per-model caps (context length, code quality tier, speed) — influence prompt strategy
- [ ] **Offline knowledge base**: local vector index of engine docs, schema files, and source headers — queried before LLM
- [ ] Documentation indexer: `atlas index-docs` CLI command re-indexes `docs/` and engine headers into local knowledge base
- [ ] **First-run model download**: `./setup.sh --ai` pulls a default coding model (DeepSeek Coder or Code Llama) via Ollama

---

### D2 — AtlasForgeAI Agent Core

The agent loop: read prompt → decide action → call tools → parse response → apply → loop.

- [ ] `AtlasForgeAI/core/agent_loop.py` — main agent loop with tool dispatch
- [ ] `AtlasForgeAI/core/context_manager.py` — build structured context snapshots for LLM prompts
- [ ] `AtlasForgeAI/core/response_parser.py` — parse structured LLM output (JSON tool calls, DSL, AST diffs)
- [ ] `AtlasForgeAI/core/approval_gate.py` — every agent action requires explicit user approval before apply
- [ ] `AtlasForgeAI/core/action_history.py` — undo stack for applied AI actions
- [ ] Agent loop integrated into ToolingLayer: `Alt+F12` toggles AtlasForgeAI overlay panel
- [ ] Streaming response display: tokens appear in real-time as the model generates
- [ ] Interrupt support: user can stop a generation mid-stream
- [ ] Session persistence: agent context saved across editor restarts

---

### D3 — Tool System

All tools are sandboxed; the agent may only call tools that have been explicitly registered and granted permission.

**File Tools**
- [ ] `tool_read_file(path)` — read file content into agent context
- [ ] `tool_write_file(path, content)` — write file with diff preview and user approval
- [ ] `tool_patch_file(path, diff)` — apply a unified diff to a file
- [ ] `tool_list_dir(path)` — list directory contents
- [ ] `tool_search_code(query, path_glob)` — grep-style search across project files

**Build Tools**
- [ ] `tool_build(target, config)` — trigger `./build.sh <target>` and capture output
- [ ] `tool_run_tests(filter)` — run `ctest -R <filter>` and return results
- [ ] `tool_compile_check(file)` — syntax-check a single file without full build

**Editor Tools**
- [ ] `tool_spawn_entity(component_json)` — create an entity via EditorCommandBus
- [ ] `tool_add_component(entity_id, component_json)` — add component via command bus
- [ ] `tool_set_property(entity_id, component, field, value)` — set component property
- [ ] `tool_get_ecs_snapshot()` — return current ECS state as JSON context

**PCG Tools**
- [ ] `tool_run_worldgraph(graph_path, seed)` — evaluate a WorldGraph and return output summary
- [ ] `tool_set_node_param(graph, node, param, value)` — tweak a WorldGraph node parameter
- [ ] `tool_preview_pcg(graph_path, seed)` — generate a 2D thumbnail of PCG output

**Asset Tools**
- [ ] `tool_list_assets(type_filter)` — list registered assets by type
- [ ] `tool_generate_asset(schema, params)` — create a new asset file from a schema template
- [ ] `tool_validate_asset(path)` — run schema validation on an asset file

---

### D4 — Code Generation Pipeline

- [ ] **System scaffolding**: given a description, generate header + source + test for a new ECS system
- [ ] **Component scaffolding**: generate a component struct with serialization and schema
- [ ] **WorldGraph node scaffolding**: generate a new PCG node with typed ports and evaluation stub
- [ ] **GUI layout generation**: generate `.atlas.layout` DSL from natural language description
- [ ] **FlowGraph generation**: generate a Flow Graph JSON from description of desired behavior
- [ ] **Schema generation**: generate `.atlas.json` schema from a description of data
- [ ] **Diff-first workflow**: all generated code shown as unified diff before any file is written
- [ ] **Iterative refinement**: "make the shield regeneration faster" → agent diffs the specific lines only
- [ ] Multi-language stubs:
  - [ ] C++ system/component/node stubs
  - [ ] Python tool/pipeline stubs
  - [ ] Lua script stubs
  - [ ] GLSL/AtlasShader stubs

---

### D5 — Dev Mode Overlay

The in-engine, always-accessible AI development interface.

- [ ] `Alt+F12` opens/closes the full AtlasForgeAI Dev Mode overlay
- [ ] Overlay layout (split into four zones):
  - **Top**: prompt input bar with context selector (World / Assets / Code / ECS)
  - **Left**: agent conversation history with diff previews inline
  - **Center**: active game viewport (unobscured — overlay is transparent/framed)
  - **Right**: tool call log + action history + undo button
- [ ] Context-aware prompt suggestions: overlay shows relevant prompts based on current editor panel
- [ ] "Ask about this" right-click: right-click any asset, node, entity, or panel → "Ask AtlasForgeAI" pre-fills context
- [ ] Live code preview: generated code shown in a split editor pane before apply
- [ ] Hot-reload integration: after file write, trigger hot-reload automatically (with user consent)
- [ ] Dev Mode persistence: window layout, conversation, and pending diffs survive engine restarts

---

### D6 — Multi-Language Build Runners

- [ ] `AtlasForgeAI/runners/cpp_runner.py` — invoke cmake/make/msbuild, parse errors, return structured result
- [ ] `AtlasForgeAI/runners/python_runner.py` — run Python scripts, capture stdout/stderr, timeout
- [ ] `AtlasForgeAI/runners/lua_runner.py` — run Lua scripts via luajit or lua5.4
- [ ] `AtlasForgeAI/runners/glsl_runner.py` — compile GLSL via glslangValidator, parse errors
- [ ] Runner error parser: extract file/line/message from compiler output for each language
- [ ] Error-fix loop: on build failure, agent automatically reads the error, diffs a fix, and prompts for approval
- [ ] Compiler feedback integration: build errors surfaced inline in AI conversation as clickable links

---

### D7 — Media Generation Pipelines

> Offline, open-source only. No cloud dependencies.

**Texture Generation**
- [ ] `AtlasForgeAI/media/texture_pipeline.py` — Stable Diffusion interface via local API (ComfyUI or AUTOMATIC1111)
- [ ] `AtlasForgeAI/media/texture_upscaler.py` — ESRGAN-based upscaling to power-of-two resolution
- [ ] `AtlasForgeAI/media/normal_map_gen.py` — generate normal map from albedo (NormalMap-Online algorithm)
- [ ] `AtlasForgeAI/media/texture_validator.py` — check format, size, power-of-two, mip count
- [ ] Texture output → asset registry: generated textures auto-registered as `.atlasb` assets

**3D Mesh Generation**
- [ ] `AtlasForgeAI/media/blender_bridge.py` — headless Blender integration via `blender --python`
- [ ] `AtlasForgeAI/media/mesh_generator.py` — generate simple mesh variants (procedural ship hulls, props) via Blender Python API
- [ ] Mesh output → asset pipeline: generated `.glb`/`.obj` cooked into `.atlasb` binary format

**Audio Generation**
- [ ] `AtlasForgeAI/media/tts_pipeline.py` — text-to-speech via Coqui TTS (offline, no cloud)
- [ ] `AtlasForgeAI/media/sfx_generator.py` — SFX generation via AudioCraft/MusicGen (offline)
- [ ] `AtlasForgeAI/media/audio_validator.py` — check sample rate, bit depth, channel count
- [ ] Audio output → SoundGraph integration: generated clips available as SoundGraph source nodes

---

### D8 — PCG Learning & AI-Driven PCG

- [ ] **Style profiler**: analyze manually authored WorldGraph outputs and extract parameter statistics
- [ ] **Similarity search**: given a reference scene, find WorldGraph configurations that produce similar output
- [ ] **AI node suggestion**: in WorldGraph panel, AtlasForgeAI suggests next nodes based on current graph topology
- [ ] **Parameter tuning**: "make terrain more mountainous" → agent identifies and tweaks relevant noise parameters
- [ ] **Biome description to graph**: "arctic plateau with volcanic ridges" → AtlasForgeAI generates a WorldGraph DSL
- [ ] **Placement style learning**: observe manual prop placements → infer scatter density, clearance rules, surface affinity
- [ ] **Feedback loop**: player-area traversal data (from replay) informs density adjustments in next PCG pass

---

### D9 — AtlasForgeAI Safety & Quality

- [ ] **Approval gate hard enforcement**: no file is ever modified without explicit user `[Apply]` click
- [ ] **Sandboxed execution**: build runners and Python tools run in subprocess with timeout and resource limits
- [ ] **Allowlist-based filesystem access**: agent may only access paths under project root and workspace
- [ ] **No secrets in context**: API keys, passwords, and env vars are scrubbed from context before sending to LLM
- [ ] **Output validation**: generated assets are schema-validated before apply; invalid output rejected
- [ ] **Determinism contract**: AI-generated assets are hashed and logged; replays never depend on AI presence
- [ ] **Audit log**: every tool call, approval, and applied action written to `workspace/ai_audit.log`
- [ ] **Rollback**: `atlas ai undo` reverts the last N applied AI actions using git-style patch reversal

---

## Phase E — Cross-System Integration & Refinement

> **Goal**: All four pillars (Dev, GUI, PCG, AI) working together as a seamless whole. The developer experience is fast, predictable, and delightful.

### E1 — AI + GUI Authoring

- [ ] AtlasForgeAI can generate complete layout DSL files from natural language description
- [ ] AI diff preview uses the DSL Editor panel for side-by-side comparison
- [ ] "Explain this panel layout" — AI describes the current DSL structure in plain English
- [ ] "Add a search bar to the Asset Browser" — AI proposes DSL patch, user applies
- [ ] Widget autocomplete powered by local knowledge base (knows all registered widget types and their properties)
- [ ] Theme token suggestions: AI recommends appropriate semantic tokens for new widgets

---

### E2 — AI + PCG Authoring

- [ ] WorldGraph panel: AI context menu on any node — "Explain", "Suggest alternatives", "Tune parameters"
- [ ] "Generate a desert canyon biome" → AtlasForgeAI produces a complete WorldGraph JSON
- [ ] Seed explorer powered by AI: "find 5 seeds that produce interesting mountain formations" → agent runs seed sweeps
- [ ] PCG regression guard: if a WorldGraph edit changes output beyond a threshold, AI flags it as a regression candidate
- [ ] Biome description panel: plain-English biome descriptions auto-linked to WorldGraph parameter sets

---

### E3 — Full Offline Dev Workflow

- [ ] **Zero-cloud development**: entire build, test, AI, and asset generation pipeline runs with no internet
- [ ] **Model package**: `./setup.sh --ai` bundles all required models into `workspace/models/` (DeepSeek Coder + Stable Diffusion + Coqui TTS)
- [ ] **Offline knowledge base auto-build**: `./setup.sh` indexes all docs and headers; no external search needed
- [ ] **Air-gapped CI**: determinism gate, contract scan, and golden replay tests all run without network access
- [ ] `atlas offline-check` — verify all dev dependencies are available offline, report any missing items

---

### E4 — Live Collaboration Hooks

- [ ] ToolingLayer authority model: in multiplayer dev session, only the host can apply PCG or AI changes
- [ ] Live cursor sharing in Graph Editor: see where remote collaborators are editing
- [ ] Conflict detection: if two devs edit the same WorldGraph node concurrently, merge conflict panel activates
- [ ] AI session sharing: dev A prompts AI; dev B sees the proposed diff and can approve or reject
- [ ] EditorEventBus broadcast: all ToolingLayer tool actions broadcast to connected peers in dev session

---

### E5 — Performance & Scalability

- [ ] GUI render budget: frame budget enforced per panel (< 0.5ms per panel at 60fps target)
- [ ] PCG async pipeline: all WorldGraph evaluation off main thread; no frame stalls during streaming
- [ ] AI context streaming: LLM responses piped to UI incrementally; no blocking waits
- [ ] Build parallelism audit: ensure all CMake targets build in parallel on N cores; no unnecessary serialization
- [ ] Memory budget tracking: each subsystem declares and reports allocation; CI fails if budget exceeded

---

### E6 — Final Hardening

- [ ] Full end-to-end test: open editor → author WorldGraph → run AI suggestion → apply PCG → hot-reload → replay — all automated
- [ ] Certified build: hash ladder verification of engine + PCG + AI module versions bundled into release manifest
- [ ] ABI lock: GUI widget enum, event structs, and command bus signatures frozen and documented for plugin compatibility
- [ ] Plugin SDK export: `find_package(AtlasEngine)` provides GUI, PCG, and AI headers for third-party tool development
- [ ] Developer onboarding benchmark: new developer from zero to running editor with AI assistant in < 15 minutes

---

## Phase Sequencing Summary

```
NOW
│
├── A1  Spaghetti cleanup (ongoing)
├── A2  Build consolidation
├── A3  Test infrastructure
├── A4  Developer tooling
│
├── B1–B4  Widget expansion + layout + themes     ← parallel with C
├── C1–C4  PCG node library + interiors + placement  ← parallel with B
│
├── D1  Offline LLM integration
├── D2  Agent core loop
├── D3  Tool system
├── D4  Code generation pipeline
├── D5  Dev Mode overlay
├── D6  Multi-language runners
├── D7  Media generation pipelines          ← can overlap with D4–D5
├── D8  PCG + AI coupling
│
├── E1–E3  AI+GUI, AI+PCG, offline workflow
├── E4  Collaboration hooks
└── E5–E6  Performance + final hardening
│
GAME FEATURES BEGIN HERE
```

---

## Milestones

| Milestone | Criteria | Target |
|-----------|----------|--------|
| **M1: Clean Foundation** | Phase A complete. All 164 systems use template bases. `GameSession` decomposed. Build < 3 min. | After Phase A |
| **M2: Full GUI Toolkit** | Phase B complete. All planned widgets exist. Theme editor live. DSL round-trip clean. | After Phase B |
| **M3: PCG Studio** | Phase C complete. WorldGraph debugger live. Interior PCG working. Placement learner active. | After Phase C |
| **M4: AtlasForgeAI Online** | Phase D complete. Offline LLM running. Agent loop active. Tool system sandboxed. Dev Mode overlay visible. | After Phase D |
| **M5: Integrated Dev Platform** | Phase E complete. Full offline workflow. AI + GUI + PCG all interconnected. Certified build passing. | After Phase E |
| **Game Features** | All five milestones met. No more infra debt. Begin adding vertical gameplay. | After M5 |

---

## What This Roadmap Intentionally Excludes

The following will be addressed **after** all five milestones are met:
- Ship combat mechanics
- Economy and trading systems
- FPS boarding gameplay
- Fleet command orders
- NPC AI behavior (faction, patrol, aggression)
- Mission generation and quest systems
- Player progression and legend system
- Multiplayer matchmaking
- Any other gameplay feature from `GAME_DESIGN_VISION.md`

> The engine, tools, and AI systems must be production-solid before game features are built on top of them. Building game systems on shaky infrastructure creates double the work.

---

*Last updated: March 2026*
*Maintained by: Nova-Forge: Expeditions core team*
