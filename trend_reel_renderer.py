from __future__ import annotations

import subprocess
import tempfile
from collections import deque
from datetime import date
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from trend_collector import TrendKeyword

BASE_DIR = Path(__file__).resolve().parent
FONT_PATH = BASE_DIR / "fonts" / "Pretendard-Bold.otf"
FOX_DIR = BASE_DIR / "assets" / "fox"

W, H = 1080, 1920
FPS = 30

# Colors — 모던 다크 테마
BG = (15, 15, 20)
BG2 = (22, 22, 30)
WHITE = (255, 255, 255)
DIM = (120, 120, 135)
CORAL = (255, 90, 60)
RANK_COLORS = {
    3: (100, 170, 255),   # 블루
    2: (170, 130, 255),   # 퍼플
    1: (255, 210, 70),    # 골드
}
PROGRESS_BG = (40, 40, 50)
PROGRESS_FG = CORAL


def _font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_PATH), size)


def _text_w(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont) -> int:
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0]


def _text_h(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont) -> int:
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[3] - bbox[1]


def _wrap_center(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_w: int) -> list[str]:
    words = text.split()
    if not words:
        return [text]
    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        trial = f"{current} {word}"
        if _text_w(draw, trial, font) <= max_w:
            current = trial
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def _lerp(a: int, b: int, t: float) -> int:
    return int(a + (b - a) * t)


def _lerp_color(c1: tuple, c2: tuple, t: float) -> tuple:
    return tuple(_lerp(a, b, t) for a, b in zip(c1, c2))


def _ease_out(t: float) -> float:
    return 1 - (1 - t) ** 3


def _ease_in(t: float) -> float:
    return t ** 3


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


def _load_fox(pose: str = "pointing.png", target_w: int = 300) -> Image.Image | None:
    fox_path = FOX_DIR / pose
    if not fox_path.exists():
        fox_path = FOX_DIR / "judging.png"
    if not fox_path.exists():
        return None
    fox = Image.open(fox_path).convert("RGBA")
    fox = _remove_checker_bg(fox)
    bbox = fox.getbbox()
    if bbox:
        fox = fox.crop(bbox)
    orig_w, orig_h = fox.size
    fox_h = int(orig_h * target_w / orig_w)
    return fox.resize((target_w, fox_h), Image.Resampling.LANCZOS)


def _gradient_bg() -> Image.Image:
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        color = _lerp_color(BG, BG2, t)
        draw.line([(0, y), (W, y)], fill=color)
    return img


def _page_visibility(frame: int, page_start: int, page_end: int) -> float:
    """페이지 진입/퇴장 visibility (0~1). fade in 0.4s, fade out 0.4s."""
    fade_frames = int(0.4 * FPS)
    if frame < page_start or frame >= page_end:
        return 0.0
    elapsed = frame - page_start
    remaining = page_end - frame
    if elapsed < fade_frames:
        return _ease_out(elapsed / fade_frames)
    if remaining < fade_frames:
        return _ease_in(remaining / fade_frames)
    return 1.0


def render_trend_reel(keywords: list[TrendKeyword], output_path: Path) -> None:
    """TOP 3 트렌드 키워드를 한 페이지씩 보여주는 릴스."""
    if len(keywords) < 3:
        return

    top3 = sorted(keywords[:3], key=lambda x: x.traffic_num)  # 낮은순 (3위부터)

    bg = _gradient_bg()
    fox = _load_fox()
    today = date.today().strftime("%Y.%m.%d")
    total_frames = int(15.0 * FPS)

    # 타임라인 (프레임): 인트로 → 3위 → 2위 → 1위 → 아웃트로
    pages = [
        ("intro", 0, int(2.5 * FPS)),
        ("rank", int(2.5 * FPS), int(6.0 * FPS)),       # 3위
        ("rank", int(6.0 * FPS), int(9.5 * FPS)),       # 2위
        ("rank", int(9.5 * FPS), int(13.0 * FPS)),      # 1위
        ("outro", int(13.0 * FPS), total_frames),
    ]

    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)

        for fi in range(total_frames):
            progress = fi / total_frames
            canvas = bg.copy()
            draw = ImageDraw.Draw(canvas)

            # 프로그레스 바
            bar_y = H - 6
            draw.rectangle([(0, bar_y), (W, H)], fill=PROGRESS_BG)
            draw.rectangle([(0, bar_y), (int(W * progress), H)], fill=PROGRESS_FG)

            # 인트로 페이지
            vis = _page_visibility(fi, pages[0][1], pages[0][2])
            if vis > 0:
                _draw_intro(draw, vis, today)

            # 키워드 페이지 (3위, 2위, 1위)
            for idx in range(3):
                page = pages[1 + idx]
                vis = _page_visibility(fi, page[1], page[2])
                if vis > 0:
                    rank = 3 - idx  # 3, 2, 1
                    _draw_keyword_page(draw, top3[idx], rank, vis)

            # 아웃트로 페이지
            vis = _page_visibility(fi, pages[4][1], pages[4][2])
            if vis > 0:
                _draw_outro(canvas, draw, fox, vis)

            canvas.save(tmp_dir / f"f_{fi:05d}.png", format="PNG")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-framerate", str(FPS),
                "-i", str(tmp_dir / "f_%05d.png"),
                "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
                "-c:v", "libx264",
                "-preset", "fast",
                "-pix_fmt", "yuv420p",
                "-c:a", "aac",
                "-shortest",
                "-t", "15",
                str(output_path),
            ],
            check=True,
            capture_output=True,
        )


def _draw_intro(draw: ImageDraw.ImageDraw, vis: float, today: str) -> None:
    """인트로: 중앙에 날짜 + 타이틀."""
    date_font = _font(30)
    label_font = _font(36)
    title_font = _font(80)

    label = "오늘의 관심 키워드"
    title = "TOP 3"

    date_color = _lerp_color(BG, CORAL, vis)
    label_color = _lerp_color(BG, DIM, vis)
    title_color = _lerp_color(BG, WHITE, vis)

    # 중앙 정렬
    dw = _text_w(draw, today, date_font)
    lw = _text_w(draw, label, label_font)
    tw = _text_w(draw, title, title_font)

    offset_y = int(30 * (1 - vis))
    cy = H // 2 - 100

    draw.text(((W - dw) // 2, cy - 100 + offset_y), today, font=date_font, fill=date_color)
    draw.text(((W - lw) // 2, cy - 40 + offset_y), label, font=label_font, fill=label_color)
    draw.text(((W - tw) // 2, cy + 30 + offset_y), title, font=title_font, fill=title_color)

    # 장식선
    line_w = int(120 * vis)
    if line_w > 0:
        lx = (W - line_w) // 2
        draw.rectangle([(lx, cy + 140), (lx + line_w, cy + 144)], fill=CORAL)

    # 출처
    src_font = _font(24)
    src = "Google Trends"
    sw = _text_w(draw, src, src_font)
    src_color = _lerp_color(BG, (60, 60, 70), vis)
    draw.text(((W - sw) // 2, cy + 180), src, font=src_font, fill=src_color)


def _draw_keyword_page(
    draw: ImageDraw.ImageDraw,
    kw: TrendKeyword,
    rank: int,
    vis: float,
) -> None:
    """키워드 한 개를 화면 중앙에 크게 표시."""
    rank_color = RANK_COLORS[rank]
    max_text_w = W - 160

    # 순위 라벨 (상단)
    rank_label_font = _font(32)
    rank_label = f"{rank}위"
    rl_w = _text_w(draw, rank_label, rank_label_font)
    rl_color = _lerp_color(BG, rank_color, vis)

    cy = H // 2 - 100  # 수직 중심
    offset_y = int(40 * (1 - vis))

    draw.text(((W - rl_w) // 2, cy - 160 + offset_y), rank_label, font=rank_label_font, fill=rl_color)

    # 큰 순위 번호
    num_font = _font(180)
    num_text = str(rank)
    nw = _text_w(draw, num_text, num_font)
    num_color = _lerp_color(BG, rank_color, vis)
    draw.text(((W - nw) // 2, cy - 120 + offset_y), num_text, font=num_font, fill=num_color)

    # 키워드 (중앙, 큰 폰트)
    kw_font = _font(62)
    kw_lines = _wrap_center(draw, kw.keyword, kw_font, max_text_w)
    kw_color = _lerp_color(BG, WHITE, vis)

    ky = cy + 120 + offset_y
    for line in kw_lines:
        lw = _text_w(draw, line, kw_font)
        draw.text(((W - lw) // 2, ky), line, font=kw_font, fill=kw_color)
        ky += _text_h(draw, line, kw_font) + 16

    # 검색수 배지
    traffic_font = _font(34)
    traffic_text = f"{kw.traffic} 검색"
    ttw = _text_w(draw, traffic_text, traffic_font)

    badge_y = ky + 30
    badge_pad_x, badge_pad_y = 24, 12
    badge_x = (W - ttw - badge_pad_x * 2) // 2
    badge_th = _text_h(draw, traffic_text, traffic_font)

    # 배지 배경 (불투명하게)
    badge_alpha = int(160 * vis)
    if badge_alpha > 0:
        draw.rounded_rectangle(
            [(badge_x, badge_y), (badge_x + ttw + badge_pad_x * 2, badge_y + badge_th + badge_pad_y * 2)],
            radius=20,
            fill=(*rank_color[:3], badge_alpha),
        )
    # 배지 텍스트 (흰색)
    text_color = _lerp_color(BG, WHITE, vis)
    draw.text((badge_x + badge_pad_x, badge_y + badge_pad_y), traffic_text, font=traffic_font, fill=text_color)

    # 설명 (키워드 아래)
    desc_font = _font(28)
    desc_lines = _wrap_center(draw, kw.description, desc_font, max_text_w)
    d_color = _lerp_color(BG, DIM, vis)
    dy = badge_y + 80
    for line in desc_lines[:2]:
        dlw = _text_w(draw, line, desc_font)
        draw.text(((W - dlw) // 2, dy), line, font=desc_font, fill=d_color)
        dy += _text_h(draw, line, desc_font) + 8

    # 상단 액센트 라인
    line_w = int(60 * vis)
    if line_w > 0:
        lx = (W - line_w) // 2
        draw.rectangle([(lx, cy - 200 + offset_y), (lx + line_w, cy - 196 + offset_y)], fill=rank_color)


def _draw_outro(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    fox: Image.Image | None,
    vis: float,
) -> None:
    """아웃트로: 여우 캐릭터 + 워터마크."""
    cy = H // 2

    # 여우 캐릭터 (중앙 위)
    if fox and vis > 0:
        fox_w, fox_h = fox.size
        fx = (W - fox_w) // 2
        fy = cy - fox_h - 20
        offset_y = int(30 * (1 - vis))

        if vis < 1.0:
            fade_fox = fox.copy()
            alpha = fade_fox.split()[3]
            alpha = alpha.point(lambda a: int(a * vis))
            fade_fox.putalpha(alpha)
            canvas.paste(fade_fox, (fx, fy + offset_y), fade_fox)
        else:
            canvas.paste(fox, (fx, fy + offset_y), fox)

    # @여우리
    wm_font = _font(32)
    wm_text = "@여우리"
    ww = _text_w(draw, wm_text, wm_font)
    wm_color = _lerp_color(BG, WHITE, vis)
    draw.text(((W - ww) // 2, cy + 10), wm_text, font=wm_font, fill=wm_color)

    # 출처
    src_font = _font(22)
    src_text = "출처: Google Trends"
    sw = _text_w(draw, src_text, src_font)
    src_color = _lerp_color(BG, (80, 80, 95), vis)
    draw.text(((W - sw) // 2, cy + 60), src_text, font=src_font, fill=src_color)
