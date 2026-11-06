#!/usr/bin/env python3
"""MCP protocol test with a stub daemon: no model, no audio, no network."""
import json, os, socket, subprocess, sys, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class Stub(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, obj):
        body = json.dumps(obj).encode()
        self.send_response(200)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        n = int(self.headers.get("content-length") or 0)
        req = json.loads(self.rfile.read(n) or b"{}")
        self._send({"ok": True, "job": "test", "voice": req.get("voice", "af_heart"), "sentences": 1})

    def do_GET(self):
        self._send({"ok": True, "queue": 0, "play": False, "voice": "af_heart"})


def run(lines, port, daemon_up=True):
    srv = None
    if daemon_up:
        srv = ThreadingHTTPServer(("127.0.0.1", port), Stub)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
    env = dict(os.environ, VOX_PORT=str(port))
    proc = subprocess.run([sys.executable, os.path.join(ROOT, "mcp", "server.py")],
                          input="\n".join(json.dumps(x) for x in lines) + "\n",
                          capture_output=True, text=True, env=env, timeout=30)
    if srv:
        srv.shutdown()
    return [json.loads(l) for l in proc.stdout.splitlines() if l.strip()]


def main():
    port = free_port()
    out = run([
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
         "params": {"name": "narrate", "arguments": {"text": "Tests are green."}}},
        {"jsonrpc": "2.0", "id": 4, "method": "tools/call",
         "params": {"name": "voice_status", "arguments": {}}},
    ], port)

    assert out[0]["result"]["serverInfo"]["name"] == "dsh-have-voice", out[0]
    names = [t["name"] for t in out[1]["result"]["tools"]]
    assert names == ["narrate", "voice_status"], names
    assert json.loads(out[2]["result"]["content"][0]["text"])["ok"] is True, out[2]
    assert "ok" in out[3]["result"]["content"][0]["text"].lower(), out[3]

    down = run([{"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                 "params": {"name": "narrate", "arguments": {"text": "hello"}}}],
               free_port(), daemon_up=False)
    assert down[0]["result"].get("isError") is True, down[0]

    print("protocol ok: initialize, tools/list, narrate, voice_status, daemon-down path")


if __name__ == "__main__":
    main()
