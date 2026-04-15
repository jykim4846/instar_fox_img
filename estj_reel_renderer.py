from __future__ import annotations

import subprocess
import tempfile
from collections import deque
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from estj_content import ESTJCard

BASE_DIR = Path(__file__).resolve().parent
FOX_DIR = BASE_DIR / "assets" / "fox"
FONT_PATH = BASE_DIR / "fonts" / "Pretendard-Bold.otf"

W, H = 1080, 1920
FPS = 30

# Colors
BG_TOP = (255, 248, 238)
BG_BOTTOM = (255, 238, 220)
BADGE_BG = (255, 107, 53)
BADGE_TEXT = (255, 255, 255)
TITLE_COLOR = (26, 20, 14)
BULLET_COLOR = (52, 40, 30)
BULLET_DIM = (210, 200, 188)
HASHTAG_COLOR = (160, 130, 100)
ACCENT_LINE = (255, 107, 53)
PROGRESS_BG = (235, 225, 210)
PROGRESS_FG = (255, 107, 53)
WATERMARK_COLOR = (180, 165, 145)


def _font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_PATH), size)


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


def _lerp(a: int, b: int, t: float) -> int:
    return int(a + (b - a) * t)


def _lerp_color(c1: tuple, c2: tuple, t: float) -> tuple:
    return tuple(_lerp(a, b, t) for a, b in zip(c1, c2))


def _ease_out(t: float) -> float:
    return 1 - (1 - t) ** 3


def _gradient_bg() -> Image.Image:
    img = Image.new("RGB", (W, H), BG_TOP)
    draw = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        color = _lerp_color(BG_TOP, BG_BOTTOM, t)
        draw.line([(0, y), (W, y)], fill=color)
    return img


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


def _load_fox(pose: str = "judging.png", target_w: int = 380) -> Image.Image | None:
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


def render_estj_reel(card: ESTJCard, output_path: Path) -> None:
    """ESTJ 카드를 15초 릴스 MP4로 렌더링한다."""
    bg = _gradient_bg()
    fox = _load_fox()

    # 타임라인 (프레임 단위)
    # 0.0~1.5s: 배지+제목 슬라이드다운
    # 1.5~3.5s: bullet 1 슬라이드업+페이드인
    # 3.5~5.5s: bullet 2
    # 5.5~7.5s: bullet 3
    # 7.5~9.5s: bullet 4
    # 9.5~12.0s: 여우 슬라이드인
    # 12.0~15.0s: 전체 유지 + 해시태그

    anim_frames = int(0.4 * FPS)  # 애니메이션 지속 프레임 (0.4초)
    total_frames = int(15.0 * FPS)

    events = [
        (0, "title"),
        (int(1.5 * FPS), "bullet_0"),
        (int(3.5 * FPS), "bullet_1"),
        (int(5.5 * FPS), "bullet_2"),
        (int(7.5 * FPS), "bullet_3"),
        (int(9.5 * FPS), "fox"),
        (int(12.0 * FPS), "hashtags"),
    ]

    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)

        for fi in range(total_frames):
            # 현재 상태 결정
            title_progress = _anim_progress(fi, events[0][0], anim_frames)
            bullet_progress = []
            for i in range(4):
                bp = _anim_progress(fi, events[1 + i][0], anim_frames)
                bullet_progress.append(bp)
            fox_progress = _anim_progress(fi, events[5][0], int(0.6 * FPS))
            ht_progress = _anim_progress(fi, events[6][0], anim_frames)
            overall_t = fi / total_frames

            frame = _render_frame(
                bg, card, fox,
                title_p=title_progress,
                bullet_ps=bullet_progress,
                fox_p=fox_progress,
                ht_p=ht_progress,
                progress=overall_t,
            )
            frame.save(tmp_dir / f"f_{fi:05d}.png", format="PNG")

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


def _anim_progress(current_frame: int, start_frame: int, duration: int) -> float:
    if current_frame < start_frame:
        return 0.0
    if current_frame >= start_frame + duration:
        return 1.0
    return _ease_out((current_frame - start_frame) / duration)


def _render_frame(
    bg: Image.Image,
    card: ESTJCard,
    fox: Image.Image | None,
    title_p: float,
    bullet_ps: list[float],
    fox_p: float,
    ht_p: float,
    progress: float,
) -> Image.Image:
    canvas = bg.copy()
    draw = ImageDraw.Draw(canvas)

    # 상단 장식선
    draw.rectangle([(0, 0), (W, 10)], fill=BADGE_BG)

    # 프로그레스 바 (하단)
    bar_y = H - 8
    draw.rectangle([(0, bar_y), (W, H)], fill=PROGRESS_BG)
    draw.rectangle([(0, bar_y), (int(W * progress), H)], fill=PROGRESS_FG)

    # ESTJ 배지 (슬라이드다운)
    if title_p > 0:
        badge_font = _font(32)
        badge_text = "ESTJ"
        bbox = draw.textbbox((0, 0), badge_text, font=badge_font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        pad_x, pad_y = 28, 12
        bx = 80
        by_target = 120
        by = int(by_target - 40 * (1 - title_p))
        alpha = int(255 * title_p)
        draw.rounded_rectangle(
            [(bx, by), (bx + tw + pad_x * 2, by + th + pad_y * 2)],
            radius=22,
            fill=(*BADGE_BG[:3], alpha) if title_p >= 1 else BADGE_BG,
        )
        draw.text((bx + pad_x, by + pad_y), badge_text, font=badge_font, fill=BADGE_TEXT)

        # 제목
        title_font = _font(64)
        max_w = W - 160
        title_lines = _wrap(draw, card.title, title_font, max_w)
        ty_target = 230
        ty = int(ty_target - 30 * (1 - title_p))
        t_color = _lerp_color((255, 248, 238), TITLE_COLOR, title_p)
        for line in title_lines:
            draw.text((80, ty), line, font=title_font, fill=t_color)
            ty += 82

        # 강조선
        line_y = ty + 24
        line_w = int(140 * title_p)
        if line_w > 0:
            draw.rectangle([(80, line_y), (80 + line_w, line_y + 5)], fill=ACCENT_LINE)
        content_top = line_y + 50
    else:
        content_top = 400

    # 불릿
    bullet_font = _font(40)
    bullet_max_w = W - 160
    by_cur = content_top

    for i, bullet in enumerate(card.bullets):
        p = bullet_ps[i] if i < len(bullet_ps) else 0
        text = f"• {bullet}"
        lines = _wrap(draw, text, bullet_font, bullet_max_w)

        if p > 0:
            color = _lerp_color(BULLET_DIM, BULLET_COLOR, p)
            offset_x = int(30 * (1 - p))
            for line in lines:
                draw.text((80 + offset_x, by_cur), line, font=bullet_font, fill=color)
                lh = draw.textbbox((0, 0), line, font=bullet_font)[3] - draw.textbbox((0, 0), line, font=bullet_font)[1]
                by_cur += lh + 12
        else:
            for line in lines:
                lh = draw.textbbox((0, 0), line, font=bullet_font)[3] - draw.textbbox((0, 0), line, font=bullet_font)[1]
                by_cur += lh + 12

        by_cur += 28

    # 여우 캐릭터 (오른쪽에서 슬라이드인)
    if fox and fox_p > 0:
        fox_w, fox_h = fox.size
        fx_target = W - fox_w - 60
        fx = int(fx_target + 200 * (1 - fox_p))
        fy = H - fox_h - 200

        if fox_p < 1.0:
            fade_fox = fox.copy()
            alpha = fade_fox.split()[3]
            alpha = alpha.point(lambda a: int(a * fox_p))
            fade_fox.putalpha(alpha)
            canvas.paste(fade_fox, (fx, fy), fade_fox)
        else:
            canvas.paste(fox, (fx, fy), fox)

    # 해시태그
    if ht_p > 0:
        ht_font = _font(26)
        ht_text = card.hashtags[:55] + "..."
        ht_color = _lerp_color(BG_BOTTOM, HASHTAG_COLOR, ht_p)
        draw.text((80, H - 120), ht_text, font=ht_font, fill=ht_color)

    # 워터마크
    wm_font = _font(22)
    draw.text((W - 200, H - 60), "@여우리", font=wm_font, fill=WATERMARK_COLOR)

    return canvas
