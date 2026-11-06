#!/usr/bin/env python3
"""Turn a status report into a 20-second spoken digest.

    python3 examples/digest.py report.md
    some-command | python3 examples/digest.py
"""
import os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
raw = open(sys.argv[1]).read() if len(sys.argv) > 1 else sys.stdin.read()

# keep the human parts: headings, bullets, first sentences of paragraphs
lines = [l.strip(" -*#\t") for l in raw.splitlines() if l.strip()]
picked, words = [], 0
for l in lines:
    l = re.sub(r"\s+", " ", l)
    l = l.split(". ")[0]
    if len(l) < 12:
        continue
    picked.append(l if l.endswith(".") else l + ".")
    words += len(l.split())
    if words > 45:
        break

text = "Quick status. " + " ".join(picked[:4])
print(text)
subprocess.run([os.path.join(ROOT, "vox"), "say", text], check=False)
