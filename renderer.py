from __future__ import annotations

import re
import textwrap
from collections import deque
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageColor, ImageDraw, ImageFont

from asset_mapper import ResolvedVisuals
from config import Settings
from content_generator import GeneratedContent


@dataclass(frozen=True)
class RenderResult:
    safe_title: str
    output_dir: Path
    slide1_path: Path
    slide2_path: Path
    slide3_path: Path
    slide1_ref: str
    slide2_ref: str
    slide3_ref: str


class CarouselRenderer:
    def __init__(self, settings: Settings, logger) -> None:
        self.settings = settings
        self.logger = logger

    def render(self, content: GeneratedContent, visuals: ResolvedVisuals) -> RenderResult | None:
        safe_title = _safe_slug(content.title)
        output_dir = self.settings.output_dir / safe_title
        output_dir.mkdir(parents=True, exist_ok=True)

        slide_specs = [
            ("slide1.png", content.cut1, visuals.cut1),
            ("slide2.png", content.cut2, visuals.cut2),
            ("slide3.png", content.cut3, visuals.cut3),
        ]

        paths: list[Path] = []
        for filename, body, fox_path in slide_specs:
            output_path = output_dir / filename
            try:
                self._render_single_slide(
                    title=content.title,
                    body=body,
                    fox_path=fox_path,
                    background_path=visuals.background,
                    output_path=output_path,
                )
                self.logger.info("렌더링 성공 | %s", output_path)
                paths.append(output_path)
            except Exception as error:  # noqa: BLE001
                self.logger.error("렌더링 실패 | %s | %s", output_path, error)
                return None

        return RenderResult(
            safe_title=safe_title,
            output_dir=output_dir,
            slide1_path=paths[0],
            slide2_path=paths[1],
            slide3_path=paths[2],
            slide1_ref=_to_output_ref(paths[0], self.settings),
            slide2_ref=_to_output_ref(paths[1], self.settings),
            slide3_ref=_to_output_ref(paths[2], self.settings),
        )

    def _render_single_slide(
        self,
        title: str,
        body: str,
        fox_path: Path,
        background_path: Path | None,
        output_path: Path,
    ) -> None:
        size = self.settings.image_size
        canvas = Image.new(
            "RGBA",
            (size, size),
            ImageColor.getrgb(self.settings.default_background_color),
        )
        if background_path and background_path.exists():
            background = Image.open(background_path).convert("RGBA").resize((size, size))
            canvas.alpha_composite(background)

        draw = ImageDraw.Draw(canvas)
        badge_font = self._load_font(30)
        title_font = self._load_font(42)
        body_font = self._fit_font(draw, body, 560, 84, 40)

        self._draw_panel_frame(draw, size)
        self._draw_speed_lines(draw, size)
        self._draw_badge(draw, size, badge_font)
        self._draw_title(draw, title, size, title_font)
        self._draw_ground_shadow(draw, size)
        self._draw_fox(canvas, fox_path, size)
        self._draw_body(draw, body, size, body_font)
        canvas.save(output_path, format="PNG")

    def _draw_panel_frame(self, draw, size: int) -> None:
        frame = (28, 28, size - 28, size - 28)
        draw.rounded_rectangle(frame, radius=42, outline="#231815", width=10)
        inner = (48, 48, size - 48, size - 48)
        draw.rounded_rectangle(inner, radius=34, outline="#FFF8F0", width=6)

    def _draw_speed_lines(self, draw, size: int) -> None:
        line_color = "#EAD8D8"
        top_y = 120
        for offset in range(0, 7):
            left_x = 80 + offset * 55
            draw.line((left_x, top_y, left_x + 60, top_y - 32), fill=line_color, width=6)
            right_x = size - 80 - offset * 55
            draw.line((right_x, top_y, right_x - 60, top_y - 32), fill=line_color, width=6)

    def _draw_badge(self, draw, size: int, font) -> None:
        text = "여우리 컷"
        bbox = draw.textbbox((0, 0), text, font=font)
        width = bbox[2] - bbox[0] + 52
        height = bbox[3] - bbox[1] + 26
        x = 74
        y = 66
        draw.rounded_rectangle((x, y, x + width, y + height), radius=20, fill="#221814")
        draw.text((x + width / 2, y + height / 2), text, font=font, fill="#FFF7EF", anchor="mm")

    def _draw_title(self, draw, title: str, size: int, font) -> None:
        wrapped = _wrap_text(title, 14)
        draw.multiline_text(
            (size / 2, 154),
            wrapped,
            font=font,
            fill="#2B1D19",
            anchor="ma",
            align="center",
            spacing=8,
        )

    def _draw_body(self, draw, body: str, size: int, font) -> None:
        body_box = (108, 218, 972, 490)
        draw.rounded_rectangle(body_box, radius=56, fill="#FFFDF8", outline="#231815", width=8)
        tail = [(460, 490), (520, 490), (500, 560)]
        draw.polygon(tail, fill="#FFFDF8", outline="#231815")
        wrap_width = max(6, int(540 / max(getattr(font, "size", 24), 24) * 1.75))
        wrapped = _wrap_text(body, wrap_width)
        draw.multiline_text(
            (size / 2, 346),
            wrapped,
            font=font,
            fill="#2B1D19",
            anchor="mm",
            align="center",
            spacing=12,
        )

    def _draw_ground_shadow(self, draw, size: int) -> None:
        draw.ellipse((280, 770, 800, 930), fill="#E6B0C3")

    def _draw_fox(self, canvas: Image.Image, fox_path: Path, size: int) -> None:
        fox = _remove_checkerboard_background(Image.open(fox_path).convert("RGBA"))
        fox.thumbnail((760, 760))
        x = (size - fox.width) // 2
        y = size - fox.height - 38
        canvas.alpha_composite(fox, dest=(x, y))

    def _fit_font(self, draw, text: str, max_width: int, start_size: int, min_size: int):
        for size in range(start_size, min_size - 1, -4):
            font = self._load_font(size)
            wrap_width = max(6, int(max_width / max(size, 24) * 1.7))
            wrapped = _wrap_text(text, wrap_width)
            bbox = draw.multiline_textbbox((0, 0), wrapped, font=font, spacing=12, align="center")
            width = bbox[2] - bbox[0]
            height = bbox[3] - bbox[1]
            if width <= max_width and height <= 190:
                return font
        return self._load_font(min_size)

    def _load_font(self, size: int):
        try:
            return ImageFont.truetype("fonts/Pretendard-Bold.otf", size=size)
        except OSError:
            pass

        candidates = [
            self.settings.font_path,
            self.settings.fonts_dir / "Pretendard-Bold.otf",
            self.settings.fonts_dir / "Pretendard-Bold.ttf",
            Path("/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc"),
            Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"),
            Path("/System/Library/Fonts/Supplemental/Apple SD Gothic Neo Bold.ttf"),
        ]
        for candidate in candidates:
            if candidate.exists():
                return ImageFont.truetype(str(candidate), size=size)
        self.logger.warning("폰트 파일이 없어 기본 폰트로 대체합니다.")
        return ImageFont.load_default()


def _safe_slug(value: str) -> str:
    cleaned = re.sub(r"[^0-9a-zA-Z가-힣]+", "_", value.strip()).strip("_")
    return cleaned[:60] or "untitled"


def _wrap_text(value: str, width: int) -> str:
    return "\n".join(textwrap.wrap(" ".join(value.split()), width=width, break_long_words=False))


def _to_output_ref(path: Path, settings: Settings) -> str:
    if settings.output_base_url:
        relative = path.relative_to(settings.output_dir).as_posix()
        return f"{settings.output_base_url.rstrip('/')}/{relative}"
    return str(path)


def _remove_checkerboard_background(image: Image.Image) -> Image.Image:
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
        if a == 0 or not _looks_like_checker_bg(r, g, b):
            continue

        pixels[x, y] = (r, g, b, 0)

        if x > 0:
            queue.append((x - 1, y))
        if x < width - 1:
            queue.append((x + 1, y))
        if y > 0:
            queue.append((x, y - 1))
        if y < height - 1:
            queue.append((x, y + 1))

    return cleaned


def _looks_like_checker_bg(r: int, g: int, b: int) -> bool:
    max_channel = max(r, g, b)
    min_channel = min(r, g, b)
    return max_channel >= 230 and (max_channel - min_channel) <= 18
