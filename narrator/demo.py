#!/usr/bin/env python3
"""Narration sample: the lines a model would write during a long task, spoken in order.

    tools/venv/bin/python narrator/demo.py

Each line is authored, not templated: what I did, how it went, what comes next.
"""
import json, os, time, urllib.request

PORT = int(os.environ.get("VOX_PORT", "8765"))

LINES = [
    "Tests are green, forty two of forty two. Next I'm taking the API layer.",
    "That type error in the handler was mine, the retry path returned the wrong shape. Fixed it, build is clean.",
    "Deploy is rolling out version two point four. I'll say something when it lands.",
    "It's live. Nothing is on fire, and the last thing left is the changelog.",
]


def say(text):
    req = urllib.request.Request(f"http://127.0.0.1:{PORT}/say",
                                 data=json.dumps({"text": text}).encode(),
                                 headers={"content-type": "application/json"})
    urllib.request.urlopen(req, timeout=5).read()


def main():
    t0 = time.time()
    for line in LINES:
        say(line)
        print(f"{time.time()-t0:5.1f}s  {line}")
        time.sleep(3.0)


if __name__ == "__main__":
    main()
