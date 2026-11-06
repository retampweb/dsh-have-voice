#!/usr/bin/env bash
# Fetches Kokoro-82M (fp32, 311 MB) + its voice pack (27 MB).
# fp32 is ~2.4x faster than int8 on CPUs without AVX-512 VNNI (tested on a Xeon E5 v3).
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p models
B=https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.1
[ -f models/kokoro-v1.0.onnx ] || curl -L --retry 3 "$B/kokoro-v1.0.onnx" -o models/kokoro-v1.0.onnx
[ -f models/voices-v1.0.bin ]   || curl -L --retry 3 "$B/voices-v1.0.bin" -o models/voices-v1.0.bin
echo "ok: $(du -shL models | cut -f1)"
if [ ! -d tools/piper ] && ! ldconfig -p 2>/dev/null | grep -q libespeak-ng; then
  echo "espeak-ng data is required by Kokoro's phonemizer: install espeak-ng, or unpack"
  echo "https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_linux_x86_64.tar.gz into tools/piper"
fi
