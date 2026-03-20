"""Tests for ai_dev/tools/ipc_bridge.py"""
import json, socket, threading, unittest
from unittest.mock import patch
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tools.ipc_bridge import IPCBridge, DEFAULT_HOST, DEFAULT_PORT


class TestIPCBridgeInit(unittest.TestCase):
    def test_default_init(self):
        b = IPCBridge()
        self.assertEqual(b.host, DEFAULT_HOST)
        self.assertEqual(b.port, DEFAULT_PORT)

    def test_custom_init(self):
        b = IPCBridge(host="192.168.1.1", port=9999, timeout=10)
        self.assertEqual(b.port, 9999)


class TestIPCBridgeConnection(unittest.TestCase):
    def test_ping_connection_refused(self):
        bridge = IPCBridge(port=19899)
        ok, msg = bridge.ping()
        self.assertFalse(ok)
        self.assertIn("not reachable", msg)

    def test_is_engine_running_false(self):
        self.assertFalse(IPCBridge(port=19899).is_engine_running())

    def test_unknown_asset_type(self):
        bridge = IPCBridge(port=19899)
        ok, msg = bridge.reload("unknown_type", "file.xyz")
        self.assertFalse(ok)
        self.assertIn("Unknown asset type", msg)

    def test_reload_dispatches_lua(self):
        bridge = IPCBridge(port=19899)
        with patch.object(bridge, "reload_lua", return_value=(True, "ok")) as mock:
            ok, _ = bridge.reload("lua", "test.lua")
            mock.assert_called_once_with("test.lua")
            self.assertTrue(ok)


class _MockEngine:
    def __init__(self, port, response=None):
        self.port = port
        self.response = response or {"status": "ok"}
        self.received = []
        self._server = None
        self._thread = None

    def start(self):
        self._server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server.bind(("127.0.0.1", self.port))
        self._server.listen(1)
        self._server.settimeout(5)
        self._thread = threading.Thread(target=self._accept, daemon=True)
        self._thread.start()

    def _accept(self):
        try:
            conn, _ = self._server.accept()
            data = conn.recv(4096)
            self.received.append(json.loads(data.decode("utf-8").strip()))
            conn.sendall((json.dumps(self.response) + "\n").encode("utf-8"))
            conn.close()
        except Exception:
            pass

    def stop(self):
        if self._server: self._server.close()
        if self._thread: self._thread.join(timeout=2)


class TestIPCBridgeWithMockServer(unittest.TestCase):
    def test_ping_success(self):
        s = _MockEngine(port=19861)
        s.start()
        try:
            b = IPCBridge(port=19861)
            ok, msg = b.ping()
            self.assertTrue(ok)
            self.assertEqual(s.received[0]["type"], "ping")
        finally:
            s.stop()

    def test_reload_lua_success(self):
        s = _MockEngine(port=19862)
        s.start()
        try:
            b = IPCBridge(port=19862)
            ok, _ = b.reload_lua("scripts/equip.lua")
            self.assertTrue(ok)
            r = s.received[0]
            self.assertEqual(r["type"], "reload")
            self.assertEqual(r["asset"], "lua")
        finally:
            s.stop()

    def test_engine_error_response(self):
        s = _MockEngine(port=19863, response={"status": "error", "message": "compile failed"})
        s.start()
        try:
            b = IPCBridge(port=19863)
            ok, msg = b.reload_glsl("shaders/bad.frag")
            self.assertFalse(ok)
            self.assertIn("compile failed", msg)
        finally:
            s.stop()


if __name__ == "__main__": unittest.main()
