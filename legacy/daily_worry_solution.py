from __future__ import annotations

import sys

from render_manual_worry_solution import run


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: python daily_worry_solution.py <manual_worry_solution.json>")
        raise SystemExit(2)
    raise SystemExit(run(sys.argv[1]))
