from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from trend_collector import TrendCollection, TrendItem

import platform

BASE_DIR = Path(__file__).resolve().parent
FONT_PATH = BASE_DIR / "fonts" / "Pretendard-Bold.otf"


def _find_cjk_font() -> Path:
    if platform.system() == "Darwin":
        p = Path("/System/Library/Fonts/AppleSDGothicNeo.ttc")
        if p.exists():
            return p
    # Linux (GitHub Actions: apt install fonts-noto-cjk)
    for candidate in (
        Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"),
        Path("/usr/share/fonts/opentype/noto/NotoSansCJKkr-Bold.otf"),
        Path("/usr/share/fonts/noto-cjk/NotoSansCJK-Bold.ttc"),
    ):
        if candidate.exists():
            return candidate
    return FONT_PATH  # Pretendard fallback


FONT_PATH_CJK = _find_cjk_font()

CANVAS_W = 1080
CANVAS_H = 1080

# Colors
OVERLAY_COLOR = (15, 12, 10, 175)      # 다크 오버레이
HEADER_COLOR = (255, 248, 235, 255)    # 헤더 텍스트 (크림)
NUMBER_COLOR = (255, 107, 53, 255)     # 번호 (코랄 오렌지)
KEYWORD_COLOR = (255, 252, 245, 255)   # 키워드 텍스트 (흰색)
DESC_COLOR = (195, 182, 165, 255)      # 설명 텍스트 (연한 베이지)
DIVIDER_COLOR = (255, 255, 255, 30)    # 구분선
FALLBACK_BG = (28, 24, 20, 255)        # 이미지 없을 때 배경


def render_trend_card(collection: TrendCollection, output_path: Path) -> None:
    canvas = _build_canvas(collection.image_path)
    draw = ImageDraw.Draw(canvas)

    # 헤더
    _draw_header(draw, collection.image_credit)

    # 아이템 리스트
    _draw_items(draw, collection.items)

    canvas.save(output_path, format="PNG")


def _build_canvas(image_path: Path | None) -> Image.Image:
    canvas = Image.new("RGBA", (CANVAS_W, CANVAS_H), FALLBACK_BG)

    if image_path and image_path.exists():
        try:
            bg = Image.open(image_path).convert("RGBA")
            bg = bg.resize((CANVAS_W, CANVAS_H), Image.Resampling.LANCZOS)
            bg = bg.filter(ImageFilter.GaussianBlur(radius=28))
            canvas.alpha_composite(bg)
        except Exception:
            pass

    overlay = Image.new("RGBA", (CANVAS_W, CANVAS_H), OVERLAY_COLOR)
    canvas.alpha_composite(overlay)
    return canvas


def _draw_header(draw: ImageDraw.ImageDraw, credit: str) -> None:
    from datetime import date
    today = date.today().strftime("%Y.%m.%d")

    # 상단 레이블
    label_font = _font(26)
    draw.text((80, 72), "오늘의 트렌드", font=label_font, fill=NUMBER_COLOR)

    # 날짜
    date_font = _font(24)
    date_text = today
    bbox = draw.textbbox((0, 0), date_text, font=date_font)
    draw.text((CANVAS_W - 80 - (bbox[2] - bbox[0]), 74), date_text, font=date_font, fill=DESC_COLOR)

    # 구분선
    draw.line([(80, 120), (CANVAS_W - 80, 120)], fill=DIVIDER_COLOR, width=1)

    # 크레딧 (하단)
    if credit:
        credit_font = _font(20)
        credit_text = f"Photo: {credit} / Unsplash"
        draw.text((80, CANVAS_H - 52), credit_text, font=credit_font, fill=(140, 130, 118, 255))


def _draw_items(draw: ImageDraw.ImageDraw, items: list[TrendItem]) -> None:
    if not items:
        return

    area_top = 148
    area_bottom = CANVAS_H - 80

    number_font = _font(36)
    keyword_font = _font(32)
    desc_font = _font(22)

    circle_r = 22
    left_x = 80
    num_cx = left_x + circle_r
    text_x = left_x + circle_r * 2 + 24
    max_w = CANVAS_W - text_x - 60

    # 각 아이템 높이 사전 계산
    def item_height(item: TrendItem) -> int:
        kw_lines = _wrap(draw, item.keyword, keyword_font, max_w)
        kw_h = sum(draw.textbbox((0, 0), l, font=keyword_font)[3] - draw.textbbox((0, 0), l, font=keyword_font)[1] for l in kw_lines) + 4 * (len(kw_lines) - 1)
        desc_h = draw.textbbox((0, 0), item.description, font=desc_font)[3] - draw.textbbox((0, 0), item.description, font=desc_font)[1]
        return kw_h + desc_h + 12

    heights = [item_height(item) for item in items]
    total_content_h = sum(heights)
    total_area = area_bottom - area_top
    gap = max(16, (total_area - total_content_h) // (len(items) + 1))

    y = area_top + gap
    for i, item in enumerate(items):
        h = heights[i]
        y_center = y + h // 2

        # 번호 원형 배지
        draw.ellipse([(num_cx - circle_r, y_center - circle_r), (num_cx + circle_r, y_center + circle_r)], fill=NUMBER_COLOR)
        num_text = str(i + 1)
        nbbox = draw.textbbox((0, 0), num_text, font=number_font)
        draw.text((num_cx - (nbbox[2] - nbbox[0]) // 2, y_center - (nbbox[3] - nbbox[1]) // 2 - 2), num_text, font=number_font, fill=(255, 255, 255, 255))

        # 키워드 (줄바꿈)
        kw_lines = _wrap(draw, item.keyword, keyword_font, max_w)
        ky = y
        for line in kw_lines:
            draw.text((text_x, ky), line, font=keyword_font, fill=KEYWORD_COLOR)
            lh = draw.textbbox((0, 0), line, font=keyword_font)[3] - draw.textbbox((0, 0), line, font=keyword_font)[1]
            ky += lh + 4

        # 설명
        draw.text((text_x, ky + 4), item.description, font=desc_font, fill=DESC_COLOR)

        # 구분선 (마지막 제외)
        if i < len(items) - 1:
            line_y = y + h + gap // 2
            draw.line([(80, line_y), (CANVAS_W - 80, line_y)], fill=DIVIDER_COLOR, width=1)

        y += h + gap


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


def _font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    # AppleSDGothicNeo: index 6=Bold, 0=Regular — 한자 포함 CJK 완전 지원
    if FONT_PATH_CJK.exists():
        return ImageFont.truetype(str(FONT_PATH_CJK), size, index=6 if bold else 0)
    return ImageFont.truetype(str(FONT_PATH), size)
