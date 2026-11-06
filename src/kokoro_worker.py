#!/usr/bin/env python3
"""Warm Kokoro worker: JSON lines in, {"ok":true,...} out. Run with tools/venv/bin/python."""
import json, os, sys, time, wave

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("LD_LIBRARY_PATH", os.path.join(ROOT, "tools", "piper"))
os.environ.setdefault("ESPEAK_DATA_PATH", os.path.join(ROOT, "tools", "piper", "espeak-ng-data"))

from kokoro_onnx import Kokoro  # noqa: E402

_k = {}


def synth(text, voice, path):
    if "k" not in _k:
        _k["k"] = Kokoro(os.path.join(ROOT, "models", "kokoro-v1.0.onnx"),
                         os.path.join(ROOT, "models", "voices-v1.0.bin"))
    t = time.perf_counter()
    samples, sr = _k["k"].create(text, voice=voice, speed=1.0, lang="en-us")
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes((np.clip(samples, -1, 1) * 32767).astype("<i2").tobytes())
    return time.perf_counter() - t, len(samples) / sr


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        req = json.loads(line)
        try:
            el, dur = synth(req["text"], req.get("voice", "af_heart"), req["out"])
            print(json.dumps({"ok": True, "synth_s": round(el, 2), "audio_s": round(dur, 2)}), flush=True)
        except Exception as e:  # keep the worker alive
            print(json.dumps({"ok": False, "error": f"{type(e).__name__}: {e}"}), flush=True)


if __name__ == "__main__":
    main()
