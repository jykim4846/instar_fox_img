from __future__ import annotations

import platform
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from trend_collector import TrendKeyword

BASE_DIR = Path(__file__).resolve().parent
FONT_PATH = BASE_DIR / "fonts" / "Pretendard-Bold.otf"

W, H = 1080, 1920
FPS = 30

# Colors
BG_DARK = (18, 15, 12)
BG_DARK2 = (28, 24, 20)
GOLD = (255, 215, 80)
CORAL = (255, 107, 53)
WHITE = (255, 252, 245)
DIM_WHITE = (140, 130, 118)
RANK_COLORS = {
    3: (120, 180, 255),   # 3위: 블루
    2: (180, 140, 255),   # 2위: 퍼플
    1: (255, 215, 80),    # 1위: 골드
}
TRAFFIC_BG = (255, 255, 255, 30)
BAR_BG = (50, 45, 40)
BAR_FG = CORAL


def _find_font() -> tuple[Path, int]:
    if platform.system() == "Darwin":
        p = Path("/System/Library/Fonts/AppleSDGothicNeo.ttc")
        if p.exists():
            return p, 6
    for c in (
        Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"),
        Path("/usr/share/fonts/noto-cjk/NotoSansCJK-Bold.ttc"),
    ):
        if c.exists():
            return c, 0
    for c in (Path("/usr/share/fonts/opentype/noto/NotoSansCJKkr-Bold.otf"),):
        if c.exists():
            return c, 0
    return FONT_PATH, 0


_FONT_FILE, _FONT_INDEX = _find_font()


def _font(size: int) -> ImageFont.FreeTypeFont:
    if _FONT_FILE.suffix.lower() == ".ttc":
        return ImageFont.truetype(str(_FONT_FILE), size, index=_FONT_INDEX)
    return ImageFont.truetype(str(_FONT_FILE), size)


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
    img = Image.new("RGB", (W, H), BG_DARK)
    draw = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        color = _lerp_color(BG_DARK, BG_DARK2, t)
        draw.line([(0, y), (W, y)], fill=color)
    return img


def render_trend_reel(keywords: list[TrendKeyword], output_path: Path) -> None:
    """TOP 3 트렌드 키워드를 카운트다운 릴스로 렌더링한다."""
    if len(keywords) < 3:
        return

    # 검색수 기준 정렬 (높은순), 상위 3개
    top3 = sorted(keywords[:3], key=lambda x: x.traffic_num)  # 낮은순 (3위부터 표시)

    bg = _gradient_bg()
    total_frames = int(15.0 * FPS)
    anim_dur = int(0.5 * FPS)

    # 타임라인: (프레임, 이벤트)
    events = {
        "intro": (0, int(0.6 * FPS)),
        "rank3": (int(2.0 * FPS), anim_dur),
        "rank2": (int(6.0 * FPS), anim_dur),
        "rank1": (int(10.0 * FPS), anim_dur),
        "outro": (int(14.0 * FPS), anim_dur),
    }

    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)

        for fi in range(total_frames):
            intro_p = _anim_p(fi, *events["intro"])
            r3_p = _anim_p(fi, *events["rank3"])
            r2_p = _anim_p(fi, *events["rank2"])
            r1_p = _anim_p(fi, *events["rank1"])
            outro_p = _anim_p(fi, *events["outro"])
            progress = fi / total_frames

            frame = _render_frame(
                bg, top3, intro_p, [r3_p, r2_p, r1_p], outro_p, progress,
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


def _anim_p(current: int, start: int, duration: int) -> float:
    if current < start:
        return 0.0
    if current >= start + duration:
        return 1.0
    return _ease_out((current - start) / duration)


def _render_frame(
    bg: Image.Image,
    top3: list[TrendKeyword],
    intro_p: float,
    rank_ps: list[float],
    outro_p: float,
    progress: float,
) -> Image.Image:
    canvas = bg.copy()
    draw = ImageDraw.Draw(canvas)

    # 상단 코랄 라인
    draw.rectangle([(0, 0), (W, 6)], fill=CORAL)

    # 프로그레스 바
    bar_y = H - 8
    draw.rectangle([(0, bar_y), (W, H)], fill=BAR_BG)
    draw.rectangle([(0, bar_y), (int(W * progress), H)], fill=BAR_FG)

    # 인트로 헤더
    if intro_p > 0:
        label_font = _font(28)
        title_font = _font(56)

        label_color = _lerp_color(BG_DARK, DIM_WHITE, intro_p)
        draw.text((80, 100), "오늘의 관심 키워드", font=label_font, fill=label_color)

        title_color = _lerp_color(BG_DARK, WHITE, intro_p)
        offset_y = int(20 * (1 - intro_p))
        draw.text((80, 140 + offset_y), "TOP 3", font=title_font, fill=title_color)

        # 구분선
        line_w = int(160 * intro_p)
        if line_w > 0:
            draw.rectangle([(80, 220), (80 + line_w, 224)], fill=CORAL)

    # 각 순위 렌더링
    ranks = [3, 2, 1]
    y_positions = [380, 740, 1100]

    for i, (rank, y_base, rp) in enumerate(zip(ranks, y_positions, rank_ps)):
        if rp <= 0:
            continue

        kw = top3[i]
        rank_color = RANK_COLORS[rank]

        # 순위 번호
        rank_font = _font(120)
        num_text = str(rank)
        num_color = _lerp_color(BG_DARK, rank_color, rp)
        offset_x = int(60 * (1 - rp))
        draw.text((80 + offset_x, y_base - 20), num_text, font=rank_font, fill=num_color)

        # 키워드
        kw_font = _font(48)
        kw_lines = _wrap(draw, kw.keyword, kw_font, W - 280)
        kw_color = _lerp_color(BG_DARK, WHITE, rp)
        ky = y_base + 10
        for line in kw_lines:
            draw.text((230 + offset_x, ky), line, font=kw_font, fill=kw_color)
            lh = draw.textbbox((0, 0), line, font=kw_font)[3] - draw.textbbox((0, 0), line, font=kw_font)[1]
            ky += lh + 8

        # 검색수 배지
        traffic_font = _font(32)
        traffic_text = f"🔍 {kw.traffic} 검색"
        t_color = _lerp_color(BG_DARK, rank_color, rp)
        draw.text((230 + offset_x, ky + 12), traffic_text, font=traffic_font, fill=t_color)

        # 설명
        desc_font = _font(26)
        desc_lines = _wrap(draw, kw.description, desc_font, W - 280)
        d_color = _lerp_color(BG_DARK, DIM_WHITE, rp)
        dy = ky + 60
        for line in desc_lines[:2]:
            draw.text((230 + offset_x, dy), line, font=desc_font, fill=d_color)
            lh = draw.textbbox((0, 0), line, font=desc_font)[3] - draw.textbbox((0, 0), line, font=desc_font)[1]
            dy += lh + 6

        # 구분선
        if i < 2:
            sep_y = y_base + 300
            sep_w = int((W - 160) * rp)
            draw.rectangle([(80, sep_y), (80 + sep_w, sep_y + 1)], fill=(60, 55, 50))

    # 아웃트로
    if outro_p > 0:
        wm_font = _font(24)
        wm_color = _lerp_color(BG_DARK, DIM_WHITE, outro_p)
        draw.text((W - 200, H - 60), "@여우리", font=wm_font, fill=wm_color)

        src_font = _font(20)
        src_color = _lerp_color(BG_DARK, (80, 75, 68), outro_p)
        draw.text((80, H - 60), "출처: Google Trends", font=src_font, fill=src_color)

    return canvas
