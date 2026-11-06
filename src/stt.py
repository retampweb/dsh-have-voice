#!/usr/bin/env python3
"""Ears: record from the default PipeWire source, transcribe with Underdog Bark 3.0 (163 MB, English only).

Needs once:
    pip install torch==2.8.0 transformers==5.19.0 constriction numpy soundfile soxr librosa
    hf download ConwayResearch/Underdog-Bark-3.0 --local-dir models/bark-3.0 \
       --include "model.bark" --include "bark_loader.py" --include "mlx/*"

    python3 src/stt.py --seconds 6          # fixed window
    python3 src/stt.py --vad                # stop on ~0.8 s of silence
"""
import argparse, os, subprocess, sys, tempfile, wave

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BARK = os.path.join(ROOT, "models", "bark-3.0")


def record(seconds=6.0, vad=False, sr=16000):
    path = os.path.join(tempfile.mkdtemp(prefix="ear-"), "in.wav")
    cmd = ["pw-record", "--rate", str(sr), "--channels", "1", "--format", "s16", path]
    if not vad:
        subprocess.run(cmd, timeout=seconds + 2, check=False)
        return path
    p = subprocess.Popen(cmd)
    try:
        import time
        time.sleep(0.4)
        while True:
            time.sleep(0.25)
            try:
                with wave.open(path) as w:
                    n = w.getnframes()
                    w.rewind()
                    tail = np.frombuffer(w.readframes(n)[-sr // 4 * 2:], dtype=np.int16)
                if n > sr and np.abs(tail).mean() < 60:  # ~0.8 s quiet after speech
                    break
            except Exception:
                pass
    finally:
        p.terminate()
        p.wait()
    return path


def transcribe(path):
    if not os.path.isdir(BARK):
        sys.exit(f"no model at {BARK}; see docstring")
    sys.path.insert(0, BARK)
    import soundfile as sf
    from bark_loader import load_model, transcribe as bark
    model = load_model(os.path.join(BARK, "model.bark"), device=os.environ.get("BARK_DEVICE", "cpu"))
    wave_, sr = sf.read(path, dtype="float32", always_2d=True)
    return bark(model, wave_.mean(1), sr)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--seconds", type=float, default=6.0)
    ap.add_argument("--vad", action="store_true")
    ap.add_argument("--file")
    a = ap.parse_args()
    wav = a.file or record(a.seconds, a.vad)
    print(transcribe(wav))
