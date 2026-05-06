from __future__ import annotations

import argparse
import os
import sys

from dotenv import load_dotenv

from daily_content_pipeline import REQUIRED_POST_ENV, run


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the daily ESTJ reel + carousel pipeline locally.",
    )
    parser.add_argument(
        "--post",
        action="store_true",
        help="Publish to Instagram. Without this flag, the local run renders only.",
    )
    return parser.parse_args()


def _missing_post_env() -> list[str]:
    return [key for key in REQUIRED_POST_ENV if not os.getenv(key, "").strip()]


def main() -> int:
    args = _parse_args()
    load_dotenv()

    if not args.post:
        return run(dry_run=True)

    missing = _missing_post_env()
    if missing:
        print("Missing required posting env vars:", ", ".join(missing), file=sys.stderr)
        print("Add them to .env or export them in your shell before using --post.", file=sys.stderr)
        return 2

    if not os.getenv("OPENAI_API_KEY", "").strip():
        print("OPENAI_API_KEY is not set; copy generation will use fallback templates.", file=sys.stderr)

    return run(dry_run=False)


if __name__ == "__main__":
    sys.exit(main())
