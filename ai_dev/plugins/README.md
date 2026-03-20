# NovaForge Dev AI — Plugin Directory

Drop plugin packages here to extend the Dev AI with new tools.

## Plugin Structure

Each plugin is a folder containing:
```
my_plugin/
├── plugin.json       — manifest
├── __init__.py       — tool registration
└── <tool modules>    — one .py per tool
```

## Manifest Format

```json
{
    "name": "my_plugin",
    "version": "1.0.0",
    "description": "What this plugin does",
    "author": "Your name",
    "tools": ["tool_generate_texture", "tool_run_linter"],
    "requires": []
}
```

## Tool Module Format

Each tool module must expose:
```python
TOOL_NAME = "generate_texture"
TOOL_DESCRIPTION = "Generate a tileable texture using Stable Diffusion offline"

def run(args: dict, repo_root) -> str:
    prompt = args.get("prompt", "rocky surface")
    # ... generate texture ...
    return "Generated: assets/textures/generated/rocky.png"
```

## Planned Built-in Plugins (Phase 6+)

| Plugin | Tools | Phase |
|--------|-------|-------|
| `stable_diffusion` | `generate_texture`, `generate_ui_icon`, `generate_skybox` | 6 |
| `audiocraft` | `generate_sfx`, `generate_music`, `generate_ambient` | 6 |
| `bark_tts` | `generate_voiceover`, `generate_npc_voice` | 6 |
| `code_intelligence` | `find_symbol`, `find_references`, `rename_symbol` | 3 |
| `git_tools` | `stage_files`, `commit_changes`, `create_branch` | 7 |
| `packaging` | `build_release`, `create_installer`, `create_zip` | 7 |
