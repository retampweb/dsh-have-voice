#!/usr/bin/env python3
"""Reproduces every number in the README. Run: tools/venv/bin/python tests/bench.py

Measures the Kokoro worker directly (load, synthesis speed) and the daemon over HTTP
(roundtrip, cache hit) when it is running.
"""
import json, os, subprocess, sys, time, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORT = int(os.environ.get("VOX_PORT", "8765"))
TEXTS = [
    "Yes. Two lines at most.",
    "Here is a slightly longer line, the kind an agent would actually say out loud to a human.",
    "The build is green, the release is on Thursday, and the only blocker left is mine to fix.",
]


def post(text, voice="af_heart"):
    req = urllib.request.Request(f"http://127.0.0.1:{PORT}/say",
                                 data=json.dumps({"text": text, "voice": voice}).encode(),
                                 headers={"content-type": "application/json"})
    t = time.perf_counter()
    with urllib.request.urlopen(req, timeout=10) as r:
        body = json.loads(r.read())
    return time.perf_counter() - t, body


def daemon_up():
    try:
        urllib.request.urlopen(f"http://127.0.0.1:{PORT}/health", timeout=1).read()
        return True
    except Exception:
        return False


def main():
    rows = []
    t0 = time.perf_counter()
    proc = subprocess.Popen([sys.executable, os.path.join(ROOT, "src", "kokoro_worker.py")],
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)
    out = os.path.join(ROOT, "out", "bench.wav")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    proc.stdin.write(json.dumps({"text": "warm up", "voice": "af_heart", "out": out}) + "\n")
    proc.stdin.flush()
    proc.stdout.readline()
    load = time.perf_counter() - t0

    for text in TEXTS:
        proc.stdin.write(json.dumps({"text": text, "voice": "af_heart", "out": out}) + "\n")
        proc.stdin.flush()
        res = json.loads(proc.stdout.readline())
        rows.append((res["audio_s"], res["synth_s"], res["audio_s"] / res["synth_s"]))
    proc.stdin.close()
    proc.wait()

    print(f"model load + first sample: {load:.2f}s")
    print()
    print("| audio, s | synth, s | speed |")
    print("|---:|---:|---:|")
    for dur, el, rtf in rows:
        print(f"| {dur:.2f} | {el:.2f} | {rtf:.2f}x |")
    print(f"\nmedian speed: {sorted(r for _, _, r in rows)[len(rows)//2]:.2f}x real time")

    if daemon_up():
        cold_text = "This line has never been spoken before, so it goes all the way through the model."
        warm_text = TEXTS[0]
        t_cold, _ = post(cold_text)
        t_warm, body = post(warm_text)
        print(f"\ndaemon roundtrip, new text: {t_cold*1000:.0f} ms")
        print(f"daemon roundtrip, cached text: {t_warm*1000:.0f} ms (cached={body.get('cached')})")
    else:
        print("\ndaemon not running; HTTP numbers skipped")


if __name__ == "__main__":
    main()
