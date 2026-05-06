#!/bin/zsh
set -euo pipefail

ROOT="/Users/jongyeon.kim/Desktop/instar_fox_img"
cd "$ROOT"

echo "[$(/bin/date '+%Y-%m-%d %H:%M:%S %Z')] local daily content start"
exec "$ROOT/.venv/bin/python" "$ROOT/run_local_daily_content.py" --post
