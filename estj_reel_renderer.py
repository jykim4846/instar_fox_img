from __future__ import annotations

import platform
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from estj_content import ESTJCard

BASE_DIR = Path(__file__).resolve().parent
FOX_DIR = BASE_DIR / "assets" / "fox"
FONT_PATH = BASE_DIR / "fonts" / "Pretendard-Bold.otf"

W, H = 1080, 1920
FPS = 30

# Colors (기존 ESTJ 카드 스타일 유지)
BG_COLOR = (255, 248, 238)
BADGE_BG = (255, 107, 53)
BADGE_TEXT = (255, 255, 255)
TITLE_COLOR = (26, 20, 14)
BULLET_COLOR = (52, 40, 30)
HASHTAG_COLOR = (160, 130, 100)
ACCENT_LINE = (255, 107, 53)
BULLET_DIM = (180, 170, 158)

# 타임라인 (초)
T_TITLE = 0.0
T_BULLETS = [2.0, 5.0, 8.0, 11.0]
T_FOX = 13.0
T_END = 15.0

FOX_POSES = ["judging.png", "arms_crossed.png", "pointing.png", "annoyed.png"]


def _find_font() -> Path:
    if platform.system() == "Darwin":
        p = Path("/System/Library/Fonts/AppleSDGothicNeo.ttc")
        if p.exists():
            return p
    for candidate in (
        Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"),
        Path("/usr/share/fonts/noto-cjk/NotoSansCJK-Bold.ttc"),
        Path("/usr/share/fonts/opentype/noto/NotoSansCJKkr-Bold.otf"),
    ):
        if candidate.exists():
            return candidate
    return FONT_PATH


_FONT_FILE = _find_font()
_IS_TTC = _FONT_FILE.suffix.lower() == ".ttc"


def _font(size: int) -> ImageFont.FreeTypeFont:
    if _IS_TTC:
        idx = 6 if "AppleSDGothicNeo" in str(_FONT_FILE) else 0
        return ImageFont.truetype(str(_FONT_FILE), size, index=idx)
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


def render_estj_reel(card: ESTJCard, output_path: Path) -> None:
    """ESTJ 카드를 15초 릴스 MP4로 렌더링한다."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        # 키프레임별 상태: (시작초, 보여줄 bullet 수, fox 표시 여부)
        keyframes: list[tuple[float, int, bool]] = [
            (T_TITLE, 0, False),
        ]
        for i, t in enumerate(T_BULLETS):
            keyframes.append((t, i + 1, False))
        keyframes.append((T_FOX, len(card.bullets), True))

        # 각 키프레임 구간별 프레임 생성
        frame_idx = 0
        for kf_i, (start, n_bullets, show_fox) in enumerate(keyframes):
            end = keyframes[kf_i + 1][0] if kf_i + 1 < len(keyframes) else T_END
            n_frames = int((end - start) * FPS)

            frame = _render_frame(card, n_bullets, show_fox)
            frame_path = tmp_dir / f"kf_{kf_i:02d}.png"
            frame.save(frame_path, format="PNG")

            # 동일 프레임을 n_frames개 심볼릭 링크로 생성
            for f in range(n_frames):
                link = tmp_dir / f"frame_{frame_idx:05d}.png"
                link.symlink_to(frame_path)
                frame_idx += 1

        output_path.parent.mkdir(parents=True, exist_ok=True)

        subprocess.run(
            [
                "ffmpeg", "-y",
                "-framerate", str(FPS),
                "-i", str(tmp_dir / "frame_%05d.png"),
                "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
                "-c:v", "libx264",
                "-preset", "fast",
                "-pix_fmt", "yuv420p",
                "-c:a", "aac",
                "-shortest",
                "-t", str(T_END),
                str(output_path),
            ],
            check=True,
            capture_output=True,
        )


def _render_frame(card: ESTJCard, n_bullets: int, show_fox: bool) -> Image.Image:
    """한 프레임을 렌더링한다. n_bullets개만 보이고 나머지는 흐리게."""
    canvas = Image.new("RGB", (W, H), BG_COLOR)
    draw = ImageDraw.Draw(canvas)

    # 상단 장식선
    draw.rectangle([(0, 0), (W, 10)], fill=BADGE_BG)

    # ESTJ 배지
    badge_font = _font(32)
    badge_text = "ESTJ"
    bbox = draw.textbbox((0, 0), badge_text, font=badge_font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    pad_x, pad_y = 28, 12
    bx, by = 80, 100
    draw.rounded_rectangle(
        [(bx, by), (bx + tw + pad_x * 2, by + th + pad_y * 2)],
        radius=22,
        fill=BADGE_BG,
    )
    draw.text((bx + pad_x, by + pad_y), badge_text, font=badge_font, fill=BADGE_TEXT)

    # 제목
    title_font = _font(62)
    max_w = W - 160
    title_lines = _wrap(draw, card.title, title_font, max_w)
    ty = 200
    for line in title_lines:
        draw.text((80, ty), line, font=title_font, fill=TITLE_COLOR)
        ty += 78

    # 강조선
    line_y = ty + 28
    draw.rectangle([(80, line_y), (220, line_y + 5)], fill=ACCENT_LINE)

    # 불릿
    bullet_font = _font(38)
    bullet_max_w = W - 160
    by_start = line_y + 50
    by_cur = by_start
    spacing = 24

    for i, bullet in enumerate(card.bullets):
        color = BULLET_COLOR if i < n_bullets else BULLET_DIM
        text = f"• {bullet}"
        lines = _wrap(draw, text, bullet_font, bullet_max_w)
        for line in lines:
            draw.text((80, by_cur), line, font=bullet_font, fill=color)
            lh = draw.textbbox((0, 0), line, font=bullet_font)[3] - draw.textbbox((0, 0), line, font=bullet_font)[1]
            by_cur += lh + 10
        by_cur += spacing

    # 여우 캐릭터
    if show_fox:
        fox_path = FOX_DIR / "judging.png"
        if fox_path.exists():
            fox = Image.open(fox_path).convert("RGBA")
            bbox = fox.getbbox()
            if bbox:
                fox = fox.crop(bbox)
            fox_w = 340
            orig_w, orig_h = fox.size
            fox_h = int(orig_h * fox_w / orig_w)
            fox = fox.resize((fox_w, fox_h), Image.Resampling.LANCZOS)
            fx = W - fox_w - 60
            fy = H - fox_h - 180
            canvas.paste(fox, (fx, fy), fox)

    # 해시태그 (하단)
    ht_font = _font(26)
    draw.text((80, H - 100), card.hashtags[:60] + "...", font=ht_font, fill=HASHTAG_COLOR)

    # 하단 여우리 워터마크
    wm_font = _font(22)
    draw.text((W - 200, H - 60), "@여우리", font=wm_font, fill=HASHTAG_COLOR)

    return canvas
