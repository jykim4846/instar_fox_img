from __future__ import annotations

import logging
import urllib.parse
from pathlib import Path

import time
import requests
from PIL import Image
import io

logger = logging.getLogger(__name__)

ENDPOINT = "https://image.pollinations.ai/prompt/{prompt}"

BACKGROUND_PROMPTS: dict[str, str] = {
    "dating": "cozy cafe interior, studio ghibli style, warm afternoon light, lush plants, soft watercolor, no people",
    "work": "sunlit studio desk by window, studio ghibli style, scattered papers, warm glow, soft watercolor, no people",
    "selfcare": "cozy attic room, studio ghibli style, soft blankets, golden hour light, dust motes, no people",
    "spending": "whimsical market street, studio ghibli style, colorful lanterns, warm evening light, no people",
    "trend": "magical hilltop view, studio ghibli style, blue sky, fluffy clouds, wide landscape, no people",
    "lifestyle": "morning kitchen, studio ghibli style, sunlight through curtains, warm tones, plants, no people",
    "default": "peaceful countryside, studio ghibli style, soft watercolor, warm natural light, no people",
}


def generate_background(
    category: str,
    save_path: Path,
    width: int = 1080,
    height: int = 1080,
    seed: int | None = None,
    timeout: int = 60,
) -> Path | None:
    prompt = BACKGROUND_PROMPTS.get(category, BACKGROUND_PROMPTS["default"])
    params = {
        "width": width,
        "height": height,
        "nologo": "true",
        "model": "flux",
    }
    if seed is not None:
        params["seed"] = seed

    encoded = urllib.parse.quote(prompt)
    url = ENDPOINT.format(prompt=encoded) + "?" + urllib.parse.urlencode(params)

    try:
        logger.info("Pollinations 배경 생성 시작 | category=%s", category)
        for attempt in range(3):
            response = requests.get(url, timeout=timeout)
            if response.status_code == 429:
                wait = 10 * (attempt + 1)
                logger.warning("Rate limit, %d초 후 재시도 (%d/3)", wait, attempt + 1)
                time.sleep(wait)
                continue
            break
        response.raise_for_status()

        save_path.parent.mkdir(parents=True, exist_ok=True)
        img = Image.open(io.BytesIO(response.content)).convert("RGB")
        if img.size != (width, height):
            img = img.resize((width, height), Image.LANCZOS)
        img.save(save_path, "PNG")
        logger.info("배경 저장 완료 | path=%s size=%s", save_path, img.size)
        return save_path

    except requests.RequestException as e:
        logger.warning("Pollinations 배경 생성 실패 | category=%s | error=%s", category, e)
        return None
