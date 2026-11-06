#!/usr/bin/env python3
"""Pure functions: sentence splitting, cache keys, Cyrillic guard."""
import importlib.util, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location("voxd", os.path.join(ROOT, "src", "voxd.py"))
voxd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(voxd)


def main():
    assert voxd.SPLIT.split("One. Two! Three?") == ["One.", "Two!", "Three?"]
    assert [s for s in voxd.SPLIT.split("Single sentence without stop")] == ["Single sentence without stop"]

    a = voxd.Server._cache_path("Tests are green.", "af_heart")
    b = voxd.Server._cache_path("Tests are green.", "af_heart")
    c = voxd.Server._cache_path("Tests are green.", "bf_emma")
    assert a == b and a != c, (a, b, c)
    assert a.endswith(".wav") and a.startswith(voxd.CACHE)

    assert voxd.CYR.search("привет") is not None
    assert voxd.CYR.search("hello") is None

    print("units ok: split, cache keys, script guard")


if __name__ == "__main__":
    main()
