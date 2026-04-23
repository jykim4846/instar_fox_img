from __future__ import annotations

from collections import deque
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from estj_content import ESTJCard

BASE_DIR = Path(__file__).resolve().parent
FOX_DIR = BASE_DIR / "assets" / "fox"
FONT_PATH = BASE_DIR / "fonts" / "Pretendard-Bold.otf"

CANVAS_W = 1080
CANVAS_H = 1080

# Colors
BG_COLOR = (255, 248, 238, 255)          # 따뜻한 크림
BADGE_BG = (255, 107, 53, 255)           # 코랄 오렌지 (ESTJ 배지)
BADGE_TEXT = (255, 255, 255, 255)        # 흰색
TITLE_COLOR = (26, 20, 14, 255)          # 거의 검정
BULLET_COLOR = (52, 40, 30, 255)         # 다크 브라운
HASHTAG_COLOR = (160, 130, 100, 255)     # 뮤트 브라운
CARD_BG = (255, 252, 244, 245)           # 카드 배경 (살짝 투명)
CARD_OUTLINE = (220, 200, 175, 255)      # 카드 테두리
ACCENT_LINE = (255, 107, 53, 255)        # 강조선

FOX_POSES = ["judging.png", "arms_crossed.png", "pointing.png", "annoyed.png"]


def render_estj_card(card: ESTJCard, output_path: Path, fox_pose: str = "judging.png") -> None:
    canvas = Image.new("RGBA", (CANVAS_W, CANVAS_H), BG_COLOR)
    draw = ImageDraw.Draw(canvas)

    # 상단 장식선
    draw.rectangle([(0, 0), (CANVAS_W, 8)], fill=BADGE_BG)

    # ESTJ 배지
    _draw_badge(draw, "ESTJ", (80, 52))

    # 제목
    title_bottom = _draw_title(draw, card.title)

    # 구분선
    line_y = title_bottom + 24
    draw.rectangle([(80, line_y), (200, line_y + 4)], fill=ACCENT_LINE)

    # 불릿 포인트
    bullet_top = line_y + 32
    bullet_bottom = _draw_bullets(draw, card.bullets, bullet_top)

    # 여우리 캐릭터
    fox_path = FOX_DIR / fox_pose
    if not fox_path.exists():
        fox_path = FOX_DIR / "judging.png"
    if fox_path.exists():
        _draw_fox(canvas, fox_path, bullet_bottom)

    # 해시태그
    _draw_hashtags(draw, card.hashtags)

    canvas.save(output_path, format="PNG")


def _draw_badge(draw: ImageDraw.ImageDraw, text: str, pos: tuple[int, int]) -> None:
    font = _font(26)
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    pad_x, pad_y = 24, 10
    x, y = pos
    draw.rounded_rectangle(
        [(x, y), (x + tw + pad_x * 2, y + th + pad_y * 2)],
        radius=20,
        fill=BADGE_BG,
    )
    draw.text((x + pad_x, y + pad_y), text, font=font, fill=BADGE_TEXT)


def _draw_title(draw: ImageDraw.ImageDraw, title: str) -> int:
    font = _font(58)
    max_w = CANVAS_W - 160
    lines = _wrap(draw, title, font, max_w)
    y = 148
    line_h = 72
    for line in lines:
        draw.text((80, y), line, font=font, fill=TITLE_COLOR)
        y += line_h
    return y


def _draw_bullets(draw: ImageDraw.ImageDraw, bullets: list[str], top_y: int) -> int:
    font = _font(34)
    max_w = CANVAS_W - 200  # 여우 공간 확보
    spacing = 18
    y = top_y
    for bullet in bullets:
        text = f"• {bullet}"
        lines = _wrap(draw, text, font, max_w)
        for line in lines:
            draw.text((80, y), line, font=font, fill=BULLET_COLOR)
            bbox = draw.textbbox((0, 0), line, font=font)
            y += (bbox[3] - bbox[1]) + 8
        y += spacing
    return y


def _draw_fox(canvas: Image.Image, fox_path: Path, content_bottom: int) -> None:
    fox = Image.open(fox_path).convert("RGBA")
    fox = _remove_checker_bg(fox)
    bbox = fox.getbbox()
    if bbox:
        fox = fox.crop(bbox)

    fox_w = 260
    orig_w, orig_h = fox.size
    fox_h = min(int(orig_h * fox_w / orig_w), 320)
    fox = fox.resize((fox_w, fox_h), Image.Resampling.LANCZOS)

    fx = CANVAS_W - fox_w - 40
    # 콘텐츠 아래와 하단 사이 중간에 배치
    available = CANVAS_H - 80 - content_bottom
    fy = content_bottom + max(0, (available - fox_h) // 2)
    fy = min(fy, CANVAS_H - fox_h - 80)

    canvas.alpha_composite(fox, dest=(fx, fy))


def _draw_hashtags(draw: ImageDraw.ImageDraw, hashtags: str) -> None:
    font = _font(24)
    draw.text((80, CANVAS_H - 56), hashtags, font=font, fill=HASHTAG_COLOR)


def _wrap(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_w: int) -> list[str]:
    words = text.split()
    if not words:
        return [text]
    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        trial = f"{current} {word}"
        bbox = draw.textbbox((0, 0), trial, font=font)
        if (bbox[2] - bbox[0]) <= max_w:
            current = trial
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def _font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_PATH), size)


def _remove_checker_bg(image: Image.Image) -> Image.Image:
    cleaned = image.copy()
    pixels = cleaned.load()
    width, height = cleaned.size
    queue: deque[tuple[int, int]] = deque()
    visited: set[tuple[int, int]] = set()
    for x in range(width):
        queue.append((x, 0))
        queue.append((x, height - 1))
    for y in range(height):
        queue.append((0, y))
        queue.append((width - 1, y))
    while queue:
        x, y = queue.popleft()
        if (x, y) in visited:
            continue
        visited.add((x, y))
        r, g, b, a = pixels[x, y]
        if a == 0 or not (max(r, g, b) >= 228 and (max(r, g, b) - min(r, g, b)) <= 18):
            continue
        pixels[x, y] = (r, g, b, 0)
        for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if 0 <= nx < width and 0 <= ny < height:
                queue.append((nx, ny))
    return cleaned
