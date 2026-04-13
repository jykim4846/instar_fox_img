from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

from logger import setup_logger
from manual_worry_solution import load_manual_worry_solution
from worry_solution_renderer import WorrySolutionRenderer


@dataclass(frozen=True)
class RenderSettings:
    output_dir: Path = Path("output")


def run(json_path: str) -> int:
    logger = setup_logger(Path("logs") / "manual_worry_render.log")
    solution = load_manual_worry_solution(Path(json_path))
    settings = RenderSettings()
    renderer = WorrySolutionRenderer(settings=settings, logger=logger)
    result = renderer.render(solution)
    if result is None:
        return 1

    print(str(result.worry_path))
    print(str(result.solution_path))
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: python render_manual_worry_solution.py <manual_worry_solution.json>")
        raise SystemExit(2)
    raise SystemExit(run(sys.argv[1]))
