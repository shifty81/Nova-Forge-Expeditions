"""
NovaForge Dev AI — IPC Bridge (Phase 2)
Socket-based IPC client for communicating with the Atlas Engine process.
"""
import json
import logging
import socket
from typing import Optional, Tuple

log = logging.getLogger(__name__)

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 19850
DEFAULT_TIMEOUT = 5


class IPCBridge:
    def __init__(self, host=DEFAULT_HOST, port=DEFAULT_PORT, timeout=DEFAULT_TIMEOUT):
        self.host = host
        self.port = port
        self.timeout = timeout

    def ping(self) -> Tuple[bool, str]:
        return self._send({"type": "ping"})

    def is_engine_running(self) -> bool:
        ok, _ = self.ping()
        return ok

    def reload_lua(self, rel_path: str) -> Tuple[bool, str]:
        return self._send({"type": "reload", "asset": "lua", "path": rel_path})

    def reload_glsl(self, rel_path: str) -> Tuple[bool, str]:
        return self._send({"type": "reload", "asset": "glsl", "path": rel_path})

    def reload_json(self, rel_path: str) -> Tuple[bool, str]:
        return self._send({"type": "reload", "asset": "json", "path": rel_path})

    def reload_ui(self, rel_path: str) -> Tuple[bool, str]:
        return self._send({"type": "reload", "asset": "ui", "path": rel_path})

    def reload(self, asset_type: str, rel_path: str) -> Tuple[bool, str]:
        dispatch = {"lua": self.reload_lua, "glsl": self.reload_glsl,
                    "json": self.reload_json, "ui": self.reload_ui}
        handler = dispatch.get(asset_type)
        if handler is None:
            return False, f"Unknown asset type: {asset_type}"
        return handler(rel_path)

    def _send(self, message: dict) -> Tuple[bool, str]:
        payload = json.dumps(message) + "\n"
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(self.timeout)
                sock.connect((self.host, self.port))
                sock.sendall(payload.encode("utf-8"))
                data = b""
                while True:
                    chunk = sock.recv(4096)
                    if not chunk:
                        break
                    data += chunk
                    if b"\n" in data:
                        break
                if not data:
                    return True, "ok (no reply)"
                reply = json.loads(data.decode("utf-8").strip())
                status = reply.get("status", "ok")
                if status == "ok":
                    return True, reply.get("message", "ok")
                else:
                    err = reply.get("message", "unknown error")
                    log.warning(f"Engine IPC error: {err}")
                    return False, err
        except ConnectionRefusedError:
            msg = (f"Engine IPC not reachable at {self.host}:{self.port}. "
                   "Is the engine running with IPC enabled?")
            log.debug(msg)
            return False, msg
        except socket.timeout:
            msg = f"Engine IPC timed out after {self.timeout}s"
            log.warning(msg)
            return False, msg
        except json.JSONDecodeError as e:
            return False, f"Invalid JSON reply from engine: {e}"
        except OSError as e:
            return False, f"IPC socket error: {e}"
