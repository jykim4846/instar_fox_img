#!/usr/bin/env python3
"""인스타툰 패널 생성기"""
from __future__ import annotations

import io
import time
import urllib.parse
from dataclasses import dataclass
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = Path(__file__).resolve().parent
CHAR_DIR = BASE_DIR / "output" / "character"
OUTPUT_DIR = BASE_DIR / "output" / "webtoon"
FONT_PATH = BASE_DIR / "fonts" / "Pretendard-Bold.otf"

CANVAS_W, CANVAS_H = 1080, 1080


@dataclass
class Panel:
    expression: str   # smug / shocked / angry / proud / thinking
    dialogue: str     # 말풍선 텍스트 (\n으로 줄바꿈)
    bg_prompt: str    # Pollinations 배경 프롬프트
    caption: str = "" # 상단 캡션 바


EPISODE_1: list[Panel] = [
    Panel(
        expression="smug",
        dialogue="9시 정각.\n시작하죠.",
        bg_prompt="modern office meeting room, empty chairs around table, morning sunlight, clean minimal, studio ghibli anime illustration style, soft warm colors, no people",
        caption="오전 9:00  /  회의실",
    ),
    Panel(
        expression="thinking",
        dialogue="...\n다들 어디 있지?",
        bg_prompt="modern office meeting room, empty chairs, wall clock showing 9:03, studio ghibli anime illustration style, soft warm colors, no people",
        caption="9:03 AM — 아무도 없다",
    ),
    Panel(
        expression="shocked",
        dialogue="지금... 몇 시예요?",
        bg_prompt="office meeting room, open door, bright hallway behind, studio ghibli illustration style, soft colors, no people",
        caption="팀원들이 헐레벌떡 입장",
    ),
    Panel(
        expression="angry",
        dialogue="지각은 팀 전체의\n시간을 훔치는 겁니다.",
        bg_prompt="office meeting room, whiteboard with writing, professional setting, studio ghibli illustration style, warm tones, no people",
        caption="",
    ),
    Panel(
        expression="proud",
        dialogue="회의록 배포 완료 ✓\n수고하셨습니다.",
        bg_prompt="office desk with papers neatly stacked, laptop open, after meeting atmosphere, studio ghibli illustration style, cozy warm light, no people",
        caption="회의 종료",
    ),
]


def remove_white_bg(img: Image.Image, threshold: int = 238) -> Image.Image:
    img = img.convert("RGBA")
    data = img.getdata()
    new_data = [
        (r, g, b, 0) if (r > threshold and g > threshold and b > threshold) else (r, g, b, a)
        for r, g, b, a in data
    ]
    img.putdata(new_data)
    return img


def fetch_background(prompt: str, save_path: Path) -> Image.Image:
    if save_path.exists():
        print("  배경 캐시 사용")
        return Image.open(save_path).convert("RGB")

    encoded = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width=1080&height=1080&nologo=true&model=flux&seed=100"
    print("  배경 생성 중...")
    r = requests.get(url, timeout=90)
    r.raise_for_status()
    img = Image.open(io.BytesIO(r.content)).convert("RGB").resize((CANVAS_W, CANVAS_H), Image.LANCZOS)
    img.save(save_path)
    time.sleep(5)
    return img


def draw_speech_bubble(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont,
    cx: int,
    cy: int,
    padding: int = 32,
) -> None:
    lines = text.split("\n")
    line_h = font.size + 12
    text_w = int(max(draw.textlength(l, font=font) for l in lines))
    text_h = len(lines) * line_h

    bx1, by1 = cx - text_w // 2 - padding, cy - text_h // 2 - padding
    bx2, by2 = cx + text_w // 2 + padding, cy + text_h // 2 + padding

    # 버블 본체
    draw.rounded_rectangle([bx1, by1, bx2, by2], radius=22, fill=(255, 255, 255, 235), outline=(40, 34, 30), width=3)

    # 꼬리 (아래 방향)
    draw.polygon(
        [(cx - 14, by2), (cx + 14, by2), (cx, by2 + 28)],
        fill=(255, 255, 255, 235),
    )
    draw.line([(cx - 14, by2), (cx, by2 + 28)], fill=(40, 34, 30), width=3)
    draw.line([(cx + 14, by2), (cx, by2 + 28)], fill=(40, 34, 30), width=3)

    # 텍스트
    y = by1 + padding
    for line in lines:
        lw = int(draw.textlength(line, font=font))
        draw.text((cx - lw // 2, y), line, font=font, fill=(30, 24, 20))
        y += line_h


def compose_panel(panel: Panel, idx: int, bg_cache_dir: Path) -> Image.Image:
    # 1. 배경
    bg = fetch_background(panel.bg_prompt, bg_cache_dir / f"bg_{idx}.png")
    canvas = bg.copy().convert("RGBA")
    canvas = Image.alpha_composite(canvas, Image.new("RGBA", canvas.size, (0, 0, 0, 55)))

    # 2. 캐릭터
    char_path = CHAR_DIR / f"estj_main_{panel.expression}.png"
    if not char_path.exists():
        char_path = CHAR_DIR / "estj_main.png"
    char = remove_white_bg(Image.open(char_path))
    char_h = 500
    char_w = int(char.width * (char_h / char.height))
    char = char.resize((char_w, char_h), Image.LANCZOS)
    canvas.paste(char, ((CANVAS_W - char_w) // 2, CANVAS_H - char_h - 50), char)

    draw = ImageDraw.Draw(canvas)
    font_lg = ImageFont.truetype(str(FONT_PATH), 40)
    font_sm = ImageFont.truetype(str(FONT_PATH), 28)

    # 3. 말풍선
    if panel.dialogue:
        draw_speech_bubble(draw, panel.dialogue, font_lg, CANVAS_W // 2, 210)

    # 4. 캡션 바
    if panel.caption:
        draw.rectangle([0, 0, CANVAS_W, 54], fill=(25, 20, 16, 210))
        cw = int(draw.textlength(panel.caption, font=font_sm))
        draw.text(((CANVAS_W - cw) // 2, 13), panel.caption, font=font_sm, fill=(255, 245, 215))

    # 5. 패널 번호
    draw.text((28, CANVAS_H - 46), f"{idx + 1} / {5}", font=font_sm, fill=(255, 255, 255, 160))

    return canvas.convert("RGB")


def make_episode(episode: list[Panel], name: str = "episode_01") -> list[Path]:
    out_dir = OUTPUT_DIR / name
    bg_cache = out_dir / "bg_cache"
    out_dir.mkdir(parents=True, exist_ok=True)
    bg_cache.mkdir(exist_ok=True)

    paths = []
    for i, panel in enumerate(episode):
        print(f"\n[{i + 1}/{len(episode)}] {panel.expression} 패널...")
        img = compose_panel(panel, i, bg_cache)
        p = out_dir / f"panel_{i + 1:02d}.png"
        img.save(p)
        print(f"  저장: {p.name}")
        paths.append(p)

    print(f"\n✓ 완료! {len(paths)}장 → {out_dir}")
    return paths


if __name__ == "__main__":
    make_episode(EPISODE_1, "ep01_지각")
