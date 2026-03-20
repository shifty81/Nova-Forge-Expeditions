"""
NovaForge Dev AI — Local LLM Interface (Phase 0)

Thin wrapper around the Ollama REST API (and any OpenAI-compatible server,
including LM Studio).  Everything runs locally — no cloud API keys needed.

Environment variables:
    LLM_BASE_URL   Base URL of the inference server (default: http://localhost:11434)
    LLM_MODEL      Model name to use            (default: deepseek-coder)
    LLM_TIMEOUT    Request timeout in seconds   (default: 120)
"""

import os
import json
import logging
from typing import Optional

try:
    import requests
    _REQUESTS_AVAILABLE = True
except ImportError:
    _REQUESTS_AVAILABLE = False

log = logging.getLogger(__name__)

DEFAULT_BASE_URL = "http://localhost:11434"
DEFAULT_MODEL = "deepseek-coder"
DEFAULT_TIMEOUT = 120

_SYSTEM_PROMPT = """You are an expert C++ and Python developer working on the
NovaForge project — a PvE space simulator built with C++17, CMake, and a custom
Atlas Engine (ECS, OpenGL, AtlasUI). You have deep knowledge of the project's
conventions:

- cpp_server/ and cpp_client/ use snake_case filenames, snake_case methods,
  trailing snake_case_ member variables.
- engine/ and editor/ use PascalCase filenames, PascalCase methods,
  m_camelCase member variables.
- All code lives in namespace atlas with sub-namespaces: ecs, systems,
  components, network, pcg, sim.
- Every ECS system follows the SingleComponentSystem<Component> pattern.
- All mutating methods return bool (true=success, false=missing entity).
- Use atlas::Logger, never std::cout in cpp_server/.
- Include guards follow: #ifndef NOVAFORGE_<SUBSYSTEM>_<FILE>_H

When suggesting code changes:
1. Show the exact file path on the first line of every code block.
2. Use the format:  ```cpp path/to/file.cpp
3. Explain what changed and why in plain English before the code.
4. Keep changes minimal and surgical — do not rewrite unrelated code.
5. Always mention which CMakeLists.txt entries need updating, if any.
"""


class LocalLLM:
    """
    Interface to a locally running LLM server (Ollama or LM Studio).

    Supports both the Ollama native API (/api/chat) and the OpenAI-compatible
    API (/v1/chat/completions).  Auto-detects which endpoint to use based on
    the server response.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[int] = None,
    ):
        self.base_url = (base_url or os.environ.get("LLM_BASE_URL", DEFAULT_BASE_URL)).rstrip("/")
        self.model = model or os.environ.get("LLM_MODEL", DEFAULT_MODEL)
        self.timeout = timeout or int(os.environ.get("LLM_TIMEOUT", DEFAULT_TIMEOUT))
        self._use_openai_compat = "1234" in self.base_url  # LM Studio default port

    def query(
        self,
        prompt: str,
        context: str = "",
        history: Optional[list] = None,
    ) -> Optional[str]:
        """Send a prompt to the local LLM and return the response text."""
        if not _REQUESTS_AVAILABLE:
            log.error("'requests' package not installed. Run: pip install requests")
            return None

        messages = self._build_messages(prompt, context, history or [])

        if self._use_openai_compat:
            return self._query_openai(messages)
        else:
            return self._query_ollama(messages)

    def is_available(self) -> bool:
        """Return True if the local LLM server is reachable."""
        if not _REQUESTS_AVAILABLE:
            return False
        try:
            import requests as req
            resp = req.get(f"{self.base_url}/api/tags", timeout=5)
            return resp.status_code == 200
        except Exception:
            try:
                import requests as req
                resp = req.get(f"{self.base_url}/v1/models", timeout=5)
                self._use_openai_compat = True
                return resp.status_code == 200
            except Exception:
                return False

    def list_models(self) -> list:
        """Return a list of available model names on the server."""
        if not _REQUESTS_AVAILABLE:
            return []
        try:
            import requests as req
            if self._use_openai_compat:
                resp = req.get(f"{self.base_url}/v1/models", timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    return [m["id"] for m in data.get("data", [])]
            else:
                resp = req.get(f"{self.base_url}/api/tags", timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    return [m["name"] for m in data.get("models", [])]
        except Exception as e:
            log.warning(f"Could not list models: {e}")
        return []

    @staticmethod
    def _build_messages(prompt: str, context: str, history: list) -> list:
        messages = [{"role": "system", "content": _SYSTEM_PROMPT}]
        for entry in history[-12:]:
            messages.append(entry)
        if context.strip():
            user_content = f"Project context:\n{context}\n\n---\n\n{prompt}"
        else:
            user_content = prompt
        messages.append({"role": "user", "content": user_content})
        return messages

    def _query_ollama(self, messages: list) -> Optional[str]:
        import requests as req
        payload = {"model": self.model, "messages": messages, "stream": False}
        try:
            resp = req.post(f"{self.base_url}/api/chat", json=payload, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
            return data.get("message", {}).get("content", "").strip()
        except req.exceptions.ConnectionError:
            log.error(f"Cannot connect to Ollama at {self.base_url}. Run: ollama serve")
        except req.exceptions.Timeout:
            log.error(f"LLM request timed out after {self.timeout}s.")
        except Exception as e:
            log.error(f"LLM query failed: {e}")
        return None

    def _query_openai(self, messages: list) -> Optional[str]:
        import requests as req
        payload = {"model": self.model, "messages": messages, "temperature": 0.2, "max_tokens": 4096}
        try:
            resp = req.post(f"{self.base_url}/v1/chat/completions", json=payload, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()
        except req.exceptions.ConnectionError:
            log.error(f"Cannot connect to LM Studio at {self.base_url}.")
        except req.exceptions.Timeout:
            log.error(f"LLM request timed out after {self.timeout}s.")
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            log.error(f"Unexpected LLM response format: {e}")
        except Exception as e:
            log.error(f"LLM query failed: {e}")
        return None
