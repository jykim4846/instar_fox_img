from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING
from collections import deque

from PIL import Image, ImageDraw, ImageFont

from manual_worry_solution import ManualWorrySolution

if TYPE_CHECKING:
    from config import Settings

BASE_DIR = Path(__file__).resolve().parent
FOX_DIR = BASE_DIR / "assets" / "fox"
BG_DIR = BASE_DIR / "assets" / "backgrounds"
FONT_PATH = BASE_DIR / "fonts" / "Pretendard-Bold.otf"

CANVAS_W = 1080
CANVAS_H = 1080
BG_COLOR = (247, 243, 234, 255)
TEXT_COLOR = (40, 34, 30, 255)
CARD_FILL = (255, 251, 245, 240)
CARD_OUTLINE = (72, 62, 54, 255)

DEFAULT_BG = {
    "dating": "chat.png",
    "work": "office.png",
    "selfcare": "home.png",
    "spending": "shopping.png",
    "trend": "blank.png",
    "lifestyle": "home.png",
}

DEFAULT_FOX = {
    "dating": "judging.png",
    "work": "arms_crossed.png",
    "selfcare": "sitting_blank.png",
    "spending": "pointing.png",
    "trend": "closeup_face.png",
    "lifestyle": "judging.png",
}


@dataclass(frozen=True)
class WorrySolutionRenderResult:
    safe_title: str
    output_dir: Path
    worry_path: Path
    solution_path: Path


@dataclass(frozen=True)
class RendererVisualSelection:
    background: str
    fox_pose: str


@dataclass(frozen=True)
class RendererContent:
    title: str
    topic: str
    category: str
    template_type: str
    worry_summary: str
    worry_story: list[str]
    estj_rule: str
    solution_title: str
    solution_body: list[str]
    final_line: str
    caption: str
    hashtags: list[str]
    visuals: RendererVisualSelection


class WorrySolutionRenderer:
    def __init__(self, settings: Settings, logger) -> None:
        self.settings = settings
        self.logger = logger

    def render(self, content: "WorrySolutionContent | ManualWorrySolution | RendererContent") -> WorrySolutionRenderResult | None:
        normalized = _normalize_content(content)
        safe_title = _safe_slug(normalized.title)
        output_dir = self.settings.output_dir / safe_title
        output_dir.mkdir(parents=True, exist_ok=True)

        worry_path = output_dir / "worry_slide.png"
        solution_path = output_dir / "solution_slide.png"
        try:
            self._render_worry_slide(normalized, worry_path)
            self._render_solution_slide(normalized, solution_path)
            return WorrySolutionRenderResult(
                safe_title=safe_title,
                output_dir=output_dir,
                worry_path=worry_path,
                solution_path=solution_path,
            )
        except Exception as error:  # noqa: BLE001
            self.logger.error("worry solution 렌더링 실패 | %s | %s", content.title, error)
            return None

    def _render_worry_slide(self, content: RendererContent, output_path: Path) -> None:
        canvas = _base_canvas(content)
        draw = ImageDraw.Draw(canvas)

        _draw_title(draw, content.title, (80, 70, 1000, 170), 58)
        _draw_round_card(draw, (76, 200, 1004, 920))
        _draw_section_label(draw, "오늘의 고민", (120, 238, 340, 292))
        _draw_title(draw, content.worry_summary, (120, 316, 960, 420), 48)
        _draw_multiline_list(draw, content.worry_story, (130, 470, 950, 850), 34, bullet=True)

        canvas.save(output_path, format="PNG")

    def _render_solution_slide(self, content: RendererContent, output_path: Path) -> None:
        canvas = _base_canvas(content)
        draw = ImageDraw.Draw(canvas)

        _draw_title(draw, "여우리 솔루션", (80, 70, 1000, 170), 58)
        _draw_round_card(draw, (70, 200, 1010, 920))
        _draw_section_label(draw, content.solution_title, (110, 238, 520, 296))
        _draw_title(draw, content.estj_rule, (110, 320, 970, 408), 38)
        _draw_multiline_list(draw, content.solution_body, (120, 450, 610, 800), 32, bullet=True)
        _draw_final_line(draw, content.final_line, (120, 820, 970, 900))

        fox_path = FOX_DIR / (content.visuals.fox_pose or DEFAULT_FOX.get(content.category, "judging.png"))
        fox_area = (650, 430, 955, 845)
        if fox_path.exists():
            fox = _prepare_fox_asset(Image.open(fox_path).convert("RGBA"))
            fox.thumbnail((fox_area[2] - fox_area[0], fox_area[3] - fox_area[1]), Image.Resampling.LANCZOS)
            x = fox_area[0] + ((fox_area[2] - fox_area[0]) - fox.width) // 2
            y = fox_area[1] + ((fox_area[3] - fox_area[1]) - fox.height) // 2
            canvas.alpha_composite(fox, dest=(x, y))

        canvas.save(output_path, format="PNG")


def _base_canvas(content: RendererContent) -> Image.Image:
    canvas = Image.new("RGBA", (CANVAS_W, CANVAS_H), BG_COLOR)
    bg_name = content.visuals.background or DEFAULT_BG.get(content.category, "blank.png")
    bg_path = BG_DIR / bg_name
    if bg_path.exists():
        bg = Image.open(bg_path).convert("RGBA").resize((CANVAS_W, CANVAS_H), Image.Resampling.LANCZOS)
        overlay = Image.new("RGBA", (CANVAS_W, CANVAS_H), (255, 250, 244, 160))
        canvas.alpha_composite(bg)
        canvas.alpha_composite(overlay)
    return canvas


def _draw_round_card(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    draw.rounded_rectangle(box, radius=42, fill=CARD_FILL, outline=CARD_OUTLINE, width=4)


def _draw_section_label(
    draw: ImageDraw.ImageDraw,
    text: str,
    box: tuple[int, int, int, int],
) -> None:
    draw.rounded_rectangle(box, radius=20, fill=(238, 229, 217, 255))
    _draw_text_center(draw, text, box, 28)


def _draw_title(
    draw: ImageDraw.ImageDraw,
    text: str,
    box: tuple[int, int, int, int],
    size: int,
) -> None:
    _draw_text_center(draw, text, box, size)


def _draw_multiline_list(
    draw: ImageDraw.ImageDraw,
    lines: list[str],
    box: tuple[int, int, int, int],
    size: int,
    *,
    bullet: bool,
) -> None:
    x1, y1, x2, y2 = box
    font = _get_font(size)
    cursor_y = y1
    spacing = 18
    for line in lines:
        text = f"• {line}" if bullet else line
        wrapped = _wrap_to_width(draw, text, font, x2 - x1)
        bbox = draw.multiline_textbbox((0, 0), wrapped, font=font, spacing=8)
        draw.multiline_text((x1, cursor_y), wrapped, font=font, fill=TEXT_COLOR, spacing=8)
        cursor_y += (bbox[3] - bbox[1]) + spacing
        if cursor_y > y2:
            break


def _draw_final_line(draw: ImageDraw.ImageDraw, text: str, box: tuple[int, int, int, int]) -> None:
    draw.rounded_rectangle(box, radius=24, fill=(56, 49, 44, 255))
    _draw_text_center(draw, text, box, 34, fill=(255, 248, 240, 255))


def _draw_text_center(
    draw: ImageDraw.ImageDraw,
    text: str,
    box: tuple[int, int, int, int],
    size: int,
    *,
    fill: tuple[int, int, int, int] = TEXT_COLOR,
) -> None:
    x1, y1, x2, y2 = box
    font = _fit_font(draw, text, x2 - x1, y2 - y1, size)
    wrapped = _wrap_to_width(draw, text, font, x2 - x1)
    bbox = draw.multiline_textbbox((0, 0), wrapped, font=font, spacing=8, align="center")
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    x = x1 + ((x2 - x1) - w) / 2
    y = y1 + ((y2 - y1) - h) / 2
    draw.multiline_text((x, y), wrapped, font=font, fill=fill, spacing=8, align="center")


def _fit_font(draw: ImageDraw.ImageDraw, text: str, max_w: int, max_h: int, start_size: int):
    for size in range(start_size, 20, -2):
        font = _get_font(size)
        wrapped = _wrap_to_width(draw, text, font, max_w)
        bbox = draw.multiline_textbbox((0, 0), wrapped, font=font, spacing=8, align="center")
        if (bbox[2] - bbox[0]) <= max_w and (bbox[3] - bbox[1]) <= max_h:
            return font
    return _get_font(22)


def _wrap_to_width(draw: ImageDraw.ImageDraw, text: str, font, max_w: int) -> str:
    words = text.split()
    if not words:
        return text
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
    return "\n".join(lines)


def _get_font(size: int):
    return ImageFont.truetype(str(FONT_PATH), size)


def _prepare_fox_asset(asset: Image.Image) -> Image.Image:
    asset = _remove_checkerboard_background(asset)
    bbox = asset.getbbox()
    if bbox:
        asset = asset.crop(bbox)
    return asset


def _safe_slug(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in {"_", "-"} or ("가" <= ch <= "힣") else "_" for ch in value).strip("_")[:60] or "untitled"


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
    return max_channel >= 228 and (max_channel - min_channel) <= 18


def _normalize_content(content: "WorrySolutionContent | ManualWorrySolution | RendererContent") -> RendererContent:
    if isinstance(content, RendererContent):
        return content
    if isinstance(content, ManualWorrySolution):
        return RendererContent(
            title=content.title,
            topic=content.worry,
            category=content.category,
            template_type="worry_solution_2",
            worry_summary=content.worry_summary,
            worry_story=content.worry_story,
            estj_rule=content.solution_title,
            solution_title=content.solution_title,
            solution_body=content.solution_body,
            final_line=content.final_line,
            caption=content.final_line,
            hashtags=[],
            visuals=RendererVisualSelection(
                background=content.background,
                fox_pose=content.fox_pose,
            ),
        )
    return RendererContent(
        title=content.title,
        topic=content.topic,
        category=content.category,
        template_type=content.template_type,
        worry_summary=content.worry_summary,
        worry_story=content.worry_story,
        estj_rule=content.estj_rule,
        solution_title=content.solution_title,
        solution_body=content.solution_body,
        final_line=content.final_line,
        caption=content.caption,
        hashtags=content.hashtags,
        visuals=RendererVisualSelection(
            background=content.visuals.background,
            fox_pose=content.visuals.fox_pose,
        ),
    )
