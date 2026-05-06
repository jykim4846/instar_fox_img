#!/bin/zsh
set -euo pipefail

ROOT="/Users/jongyeon.kim/Desktop/instar_fox_img"
cd "$ROOT"

exec "$ROOT/.venv/bin/python" "$ROOT/run_local_daily_content.py" --post
