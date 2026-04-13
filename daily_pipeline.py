from __future__ import annotations

import sys

import main as collect_main
import render_answered_notion_pages as render_main


def run() -> int:
    collect_code = collect_main.run()
    render_code = render_main.run()

    if collect_code == 0 or render_code == 0:
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(run())
