#!/usr/bin/env python3
"""voxd — warm Kokoro-82M daemon. POST /say returns in ~100 ms; audio starts ~1-2 s later.

    python3 src/voxd.py --port 8765
    curl -s localhost:8765/say -d '{"text":"Yes. Two lines at most.","voice":"af_heart"}'
"""
import argparse, hashlib, json, os, queue, re, subprocess, sys, threading, time, uuid
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.expanduser(os.environ.get("VOX_CACHE", os.path.join(ROOT, "out", "cache")))
PLAY = os.environ.get("VOX_PLAY", "pw-play")
KOKORO_PY = os.path.join(ROOT, "tools", "venv", "bin", "python")
KOKORO_WORKER = os.path.join(ROOT, "src", "kokoro_worker.py")
VOICES = ("af_heart", "bf_emma", "af_bella", "af_nicole", "af_sarah", "am_michael")
DEFAULT_VOICE = "af_heart"
OPENERS = ["Yes.", "Right.", "Okay.", "Short version.", "Sure."]
CYR = re.compile(r"[А-Яа-яЁё]")
SPLIT = re.compile(r"(?<=[.!?])\s+")
os.makedirs(CACHE, exist_ok=True)


class Player(threading.Thread):
    """Single pw-play consumer: clips go out in order, back to back."""

    def __init__(self):
        super().__init__(daemon=True)
        self.q = queue.Queue()

    def put(self, path):
        self.q.put(path)

    def run(self):
        while True:
            path = self.q.get()
            if path is None:
                return
            subprocess.run([PLAY, path], check=False,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


class Server:
    def __init__(self, play=True):
        self.player = Player()
        self.player.start()
        self.play = play
        self.proc, self.lock = None, threading.Lock()
        threading.Thread(target=self._prewarm, daemon=True).start()

    # ---- Kokoro worker: one long-lived process, model loaded once
    def _worker(self):
        if self.proc is None or self.proc.poll() is not None:
            self.proc = subprocess.Popen([KOKORO_PY, KOKORO_WORKER], stdin=subprocess.PIPE,
                                         stdout=subprocess.PIPE, text=True, bufsize=1)
        return self.proc

    def _synth_blocking(self, text, voice, path):
        with self.lock:
            proc = self._worker()
            proc.stdin.write(json.dumps({"text": text, "voice": voice, "out": path}) + "\n")
            proc.stdin.flush()
            return json.loads(proc.stdout.readline() or "{}")

    def _prewarm(self):
        for text in OPENERS:
            path = self._cache_path(text, DEFAULT_VOICE)
            if not os.path.exists(path):
                self._synth_blocking(text, DEFAULT_VOICE, path)
        print(f"[prewarm] {len(OPENERS)} openers ready", flush=True)

    @staticmethod
    def _cache_path(text, voice):
        key = hashlib.sha1(f"kokoro|{voice}|{text}".encode()).hexdigest()[:20]
        return os.path.join(CACHE, key + ".wav")

    def speak(self, text, voice=DEFAULT_VOICE):
        voice = voice if voice in VOICES else DEFAULT_VOICE
        if CYR.search(text):
            return {"ok": False, "error": "English only: no Russian voice in the bundled pack"}
        sentences = [x.strip() for x in SPLIT.split(text.strip()) if x.strip()]
        job, started = uuid.uuid4().hex[:8], time.perf_counter()

        def run():
            for i, sentence in enumerate(sentences):
                path = self._cache_path(sentence, voice)
                if not os.path.exists(path):
                    resp = self._synth_blocking(sentence, voice, path)
                    if not resp.get("ok"):
                        print(f"[{job}] failed: {resp}", flush=True)
                        return
                if i == 0:
                    print(f"[{job}] first sentence in {time.perf_counter()-started:.2f}s", flush=True)
                if self.play:
                    self.player.put(path)
            print(f"[{job}] {len(sentences)} sentence(s) in {time.perf_counter()-started:.2f}s", flush=True)

        threading.Thread(target=run, daemon=True).start()
        cached = all(os.path.exists(self._cache_path(x, voice)) for x in sentences)
        return {"ok": True, "job": job, "voice": voice, "sentences": len(sentences), "cached": cached}


class Handler(BaseHTTPRequestHandler):
    srv: Server

    def log_message(self, *a):
        pass

    def _json(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/health":
            return self._json(200, {"ok": True, "queue": self.srv.player.q.qsize(), "play": self.srv.play,
                                    "voice": DEFAULT_VOICE, "voices": list(VOICES)})
        return self._json(404, {"ok": False})

    def do_POST(self):
        if self.path != "/say":
            return self._json(404, {"ok": False})
        n = int(self.headers.get("content-length") or 0)
        try:
            req = json.loads(self.rfile.read(n) or b"{}")
        except json.JSONDecodeError:
            return self._json(400, {"ok": False, "error": "bad json"})
        text = (req.get("text") or "").strip()
        if not text:
            return self._json(400, {"ok": False, "error": "text required"})
        return self._json(200, self.srv.speak(text, req.get("voice", DEFAULT_VOICE)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--no-play", action="store_true")
    a = ap.parse_args()
    if not os.path.exists(os.path.join(ROOT, "models", "kokoro-v1.0.onnx")):
        sys.exit("missing models/kokoro-v1.0.onnx + voices-v1.0.bin (see README)")
    srv = Server(play=not a.no_play)
    Handler.srv = srv
    print(f"voxd on http://127.0.0.1:{a.port} (kokoro-82m, {DEFAULT_VOICE})", flush=True)
    ThreadingHTTPServer(("127.0.0.1", a.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
