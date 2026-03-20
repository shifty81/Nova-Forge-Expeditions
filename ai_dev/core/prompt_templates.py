"""
NovaForge Dev AI — Language-Aware Prompt Templates (Phase 2)

Provides subsystem-specific prompt templates so the LLM receives
context tailored to the language and domain being worked on.
"""

import logging
from typing import Optional

log = logging.getLogger(__name__)

_TEMPLATES: dict[str, str] = {
    "cpp_server": (
        "You are editing C++ code in the **cpp_server/** subsystem.\n"
        "Conventions:\n"
        "- snake_case filenames, methods, and local variables.\n"
        "- Trailing snake_case_ for member variables.\n"
        "- namespace atlas { namespace systems { ... } }\n"
        "- ECS systems extend SingleComponentSystem<Component>.\n"
        "- All mutating methods return bool (true = success).\n"
        "- Use atlas::Logger — never std::cout / std::cerr.\n"
        "- Include guards: #ifndef NOVAFORGE_SYSTEMS_<NAME>_H\n"
    ),
    "cpp_client": (
        "You are editing C++ code in the **cpp_client/** subsystem.\n"
        "Conventions:\n"
        "- snake_case filenames, methods, and local variables.\n"
        "- Trailing snake_case_ for member variables.\n"
        "- namespace atlas { ... }\n"
        "- OpenGL rendering with GLFW; camera uses -Z forward at yaw=0.\n"
        "- Include guards: #ifndef NOVAFORGE_CLIENT_<NAME>_H\n"
    ),
    "engine": (
        "You are editing C++ code in the **engine/** subsystem (Atlas Engine).\n"
        "Conventions:\n"
        "- PascalCase filenames and methods.\n"
        "- m_camelCase for member variables.\n"
        "- namespace atlas { ... }\n"
        "- Core modules: ECS, rendering (OpenGL), audio, PCG.\n"
    ),
    "editor": (
        "You are editing C++ code in the **editor/** subsystem (Atlas Editor).\n"
        "Conventions:\n"
        "- PascalCase filenames and methods.\n"
        "- m_camelCase for member variables.\n"
        "- namespace atlas { ... }\n"
        "- Editor tools register via EditorCommandBus.\n"
        "- Changes are undoable through UndoableCommandBus.\n"
    ),
    "python": (
        "You are editing Python code in **ai_dev/** or **tools/**.\n"
        "Conventions:\n"
        "- Python 3.8+ compatible.\n"
        "- Use logging module (log = logging.getLogger(__name__)).\n"
        "- Type hints for public API methods.\n"
        "- Classes: PascalCase. Functions/variables: snake_case.\n"
        "- Tests use unittest + unittest.mock.\n"
    ),
    "lua": (
        "You are editing Lua scripts used by the Atlas Engine.\n"
        "Conventions:\n"
        "- Use local variables wherever possible.\n"
        "- Scripts are reloaded at runtime via dofile().\n"
        "- No global state pollution — wrap in local tables.\n"
        "- Use atlas.log() for logging, not print().\n"
    ),
    "glsl": (
        "You are editing GLSL shaders for the Atlas Engine renderer.\n"
        "Conventions:\n"
        "- GLSL 4.50 core profile.\n"
        "- Vertex shaders: .vert extension.\n"
        "- Fragment shaders: .frag extension.\n"
        "- Use uniform buffer objects (UBOs) for camera/model matrices.\n"
        "- Validate with: glslangValidator -V <shader>\n"
    ),
    "csharp": (
        "You are editing C# / .NET code.\n"
        "Conventions:\n"
        "- PascalCase for classes, methods, and properties.\n"
        "- camelCase for local variables and parameters.\n"
        "- _camelCase for private fields.\n"
        "- Build with: dotnet build\n"
        "- Test with: dotnet test\n"
    ),
    "json": (
        "You are editing JSON data files.\n"
        "Conventions:\n"
        "- Use consistent indentation (2 spaces).\n"
        "- Keys in snake_case.\n"
        "- Files are hot-reloadable by the game server.\n"
    ),
    "blender": (
        "You are editing Blender Python scripts for the PCG pipeline.\n"
        "Conventions:\n"
        "- Target Blender 5.0+ API.\n"
        "- Use bmesh for procedural geometry.\n"
        "- Export as .glb or .fbx.\n"
        "- Run headless: blender --background --python <script>\n"
    ),
    "cmake": (
        "You are editing CMakeLists.txt build configuration.\n"
        "Conventions:\n"
        "- Minimum CMake 3.22.\n"
        "- Server sources listed in CORE_SOURCES.\n"
        "- Use -DBUILD_TESTS=ON -DUSE_STEAM_SDK=OFF for dev builds.\n"
    ),
}

_EXT_TO_SUBSYSTEM: dict[str, str] = {
    ".cpp": "cpp_server",
    ".h": "cpp_server",
    ".hpp": "cpp_server",
    ".py": "python",
    ".lua": "lua",
    ".vert": "glsl",
    ".frag": "glsl",
    ".glsl": "glsl",
    ".cs": "csharp",
    ".json": "json",
    ".cmake": "cmake",
}

_PATH_PREFIX_TO_SUBSYSTEM: list[tuple[str, str]] = [
    ("cpp_server/", "cpp_server"),
    ("cpp_client/", "cpp_client"),
    ("engine/", "engine"),
    ("editor/", "editor"),
    ("ai_dev/", "python"),
    ("tools/Blender", "blender"),
]


class PromptTemplates:
    """
    Selects and returns the best prompt preamble for a given subsystem,
    file path, or file extension.
    """

    def for_subsystem(self, subsystem: str) -> str:
        return _TEMPLATES.get(subsystem, "")

    def for_file(self, rel_path: str) -> str:
        subsystem = self.detect_subsystem(rel_path)
        return self.for_subsystem(subsystem)

    def detect_subsystem(self, rel_path: str) -> str:
        for prefix, subsystem in _PATH_PREFIX_TO_SUBSYSTEM:
            if rel_path.startswith(prefix):
                return subsystem
        dot = rel_path.rfind(".")
        if dot >= 0:
            ext = rel_path[dot:].lower()
            return _EXT_TO_SUBSYSTEM.get(ext, "")
        return ""

    def available_subsystems(self) -> list[str]:
        return sorted(_TEMPLATES.keys())

    def enrich_prompt(self, prompt: str, rel_path: Optional[str] = None,
                      subsystem: Optional[str] = None) -> str:
        if subsystem:
            preamble = self.for_subsystem(subsystem)
        elif rel_path:
            preamble = self.for_file(rel_path)
        else:
            preamble = ""

        if preamble:
            return f"{preamble}\n---\n\n{prompt}"
        return prompt
