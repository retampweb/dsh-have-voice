#!/usr/bin/env bash
# One-command install: venv, kokoro-onnx, espeak-ng, weights, smoke test.
set -euo pipefail
cd "$(dirname "$0")"
PY="${PYTHON:-python3}"

say() { printf '\033[1m%s\033[0m\n' "$*"; }

command -v "$PY" >/dev/null || { echo "python3 not found"; exit 1; }
"$PY" - <<'PYCHK'
import sys
if sys.version_info < (3, 10):
    sys.exit(f"python >= 3.10 required, found {sys.version.split()[0]}")
PYCHK

if [ ! -x tools/venv/bin/python ] || ! tools/venv/bin/python -c "import kokoro_onnx" 2>/dev/null; then
  say "creating tools/venv"
  mkdir -p tools
  "$PY" -m venv tools/venv
  tools/venv/bin/pip install -q --upgrade pip
  tools/venv/bin/pip install -q kokoro-onnx
fi

say "weights"
./fetch-model.sh

if ! ldconfig -p 2>/dev/null | grep -q libespeak-ng && [ ! -d tools/piper ]; then
  say "espeak-ng not found on the system, unpacking the bundled one"
  curl -sL --retry 3 https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_linux_x86_64.tar.gz \
    | tar xz -C tools
fi

say "smoke test"
tools/venv/bin/python - <<'PYCHK'
import os, sys
sys.path.insert(0, os.path.join("tools", "piper") if os.path.isdir("tools/piper") else ".")
os.environ.setdefault("LD_LIBRARY_PATH", os.path.abspath("tools/piper"))
os.environ.setdefault("ESPEAK_DATA_PATH", os.path.abspath("tools/piper/espeak-ng-data"))
from kokoro_onnx import Kokoro
k = Kokoro("models/kokoro-v1.0.onnx", "models/voices-v1.0.bin")
s, sr = k.create("Ready.", voice="af_heart", speed=1.0, lang="en-us")
print(f"ok: {len(s)/sr:.2f}s of audio at {sr} Hz")
PYCHK

command -v pw-play >/dev/null || echo "note: pw-play not found; set VOX_PLAY=aplay (or afplay on macOS)"
say "installed. next: ./vox serve &  then  ./vox say \"Yes. It works.\""
