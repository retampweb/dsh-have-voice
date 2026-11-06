#!/usr/bin/env python3
"""MCP server: one tool, `narrate`. Forwards the line to the local voxd.

The words come from the model, so nothing here is templated — the daemon only speaks
what it is given. stdio JSON-RPC, no dependencies.

    {"command": "python3", "args": ["mcp/server.py"]}
"""
import json, os, sys, urllib.error, urllib.request

PORT = int(os.environ.get("VOX_PORT", "8765"))
SERVER = {"name": "dsh-have-voice", "version": "0.2.0"}
PROTOCOL = "2024-11-05"

TOOLS = [{
    "name": "narrate",
    "description": (
        "Speak one short update out loud while the human is looking elsewhere. Write it the way "
        "you would say it to a colleague: what you just did, how it went, what comes next. "
        "One or two sentences, no markdown, no lists, no code. Vary the wording; do not read the "
        "task list or repeat yourself. Use it at milestones (a batch of work finished, tests came "
        "back, something failed, you are blocked), not after every step."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "What to say. Plain spoken English, 1-2 sentences."},
            "voice": {"type": "string", "description": "Optional voice: af_heart (default), bf_emma, af_bella."},
        },
        "required": ["text"],
    },
}, {
    "name": "voice_status",
    "description": "Check whether the local voice daemon is up and which voice it uses.",
    "inputSchema": {"type": "object", "properties": {}},
}]


def post(path, payload):
    req = urllib.request.Request(f"http://127.0.0.1:{PORT}{path}",
                                 data=json.dumps(payload).encode(),
                                 headers={"content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())


def get(path):
    with urllib.request.urlopen(f"http://127.0.0.1:{PORT}{path}", timeout=3) as r:
        return json.loads(r.read())


def call_tool(name, args):
    if name == "narrate":
        text = (args.get("text") or "").strip()
        if not text:
            return {"content": [{"type": "text", "text": "empty text"}], "isError": True}
        try:
            res = post("/say", {"text": text, "voice": args.get("voice", "af_heart")})
        except (urllib.error.URLError, ConnectionError) as e:
            return {"content": [{"type": "text", "text": f"voice daemon is down ({e}); run `vox serve`"}],
                    "isError": True}
        return {"content": [{"type": "text", "text": json.dumps(res)}]}
    if name == "voice_status":
        try:
            return {"content": [{"type": "text", "text": json.dumps(get("/health"))}]}
        except Exception as e:
            return {"content": [{"type": "text", "text": f"daemon down: {e}"}], "isError": True}
    return {"content": [{"type": "text", "text": f"unknown tool {name}"}], "isError": True}


def handle(msg):
    method = msg.get("method")
    mid = msg.get("id")
    if method == "initialize":
        return {"jsonrpc": "2.0", "id": mid, "result": {
            "protocolVersion": PROTOCOL, "capabilities": {"tools": {}}, "serverInfo": SERVER}}
    if method in ("notifications/initialized", "notifications/cancelled"):
        return None
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": mid, "result": {"tools": TOOLS}}
    if method == "tools/call":
        params = msg.get("params") or {}
        return {"jsonrpc": "2.0", "id": mid, "result": call_tool(params.get("name"), params.get("arguments") or {})}
    if method == "ping":
        return {"jsonrpc": "2.0", "id": mid, "result": {}}
    if mid is None:
        return None
    return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32601, "message": f"unknown method {method}"}}


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        reply = handle(msg)
        if reply is not None:
            sys.stdout.write(json.dumps(reply) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
