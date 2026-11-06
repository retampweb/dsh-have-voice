#!/usr/bin/env bash
# Link this skill into the DSH skill directory.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
DEST="${DSH_SKILLS:-$HOME/.dsh/skills}/voice"
mkdir -p "$(dirname "$DEST")"
ln -sfn "$HERE" "$DEST"
echo "installed: $DEST -> $HERE"
