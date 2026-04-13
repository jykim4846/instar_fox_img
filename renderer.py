from __future__ import annotations

import json
import textwrap
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List

from PIL import Image, ImageDraw, ImageFont

if TYPE_CHECKING:
    from asset_mapper import ResolvedVisuals
    from config import Settings
    from content_generator import CutLine, GeneratedContent

BASE_DIR = Path(__file__).resolve().parent
ASSET_DIR = BASE_DIR / "assets"
FOX_DIR = ASSET_DIR / "fox"
BG_DIR = ASSET_DIR / "backgrounds"
FONT_PATH = BASE_DIR / "fonts" / "Pretendard-Bold.otf"
OUTPUT_DIR = BASE_DIR / "output"

CANVAS_W = 1080
CANVAS_H = 1080
BG_COLOR = (247, 243, 234, 255)
TEXT_COLOR = (34, 34, 34, 255)
PANEL_GAP = 20
OUTER_MARGIN = 30
HEADER_HEIGHT = 0

PANEL_VISUAL_RULES: Dict[str, List[str]] = {
    "dating": [
        "phone_looking.png",
        "judging.png",
        "neutral_front.png",
        "annoyed.png",
        "sitting_blank.png",
        "closeup_face.png",
    ],
    "work": [
        "arms_crossed.png",
        "pointing.png",
        "judging.png",
        "annoyed.png",
        "sitting_blank.png",
        "closeup_face.png",
    ],
    "selfcare": [
        "lying_down.png",
        "sitting_blank.png",
        "neutral_front.png",
        "annoyed.png",
        "lying_down.png",
        "closeup_face.png",
    ],
    "spending": [
        "phone_looking.png",
        "judging.png",
        "neutral_front.png",
        "judging.png",
        "sitting_blank.png",
        "pointing.png",
    ],
    "trend": [
        "neutral_front.png",
        "judging.png",
        "annoyed.png",
        "sitting_blank.png",
        "judging.png",
        "closeup_face.png",
    ],
    "lifestyle": [
        "neutral_front.png",
        "sitting_blank.png",
        "judging.png",
        "annoyed.png",
        "sitting_blank.png",
        "closeup_face.png",
    ],
}

PANEL_BG_RULES: Dict[str, str] = {
    "dating": "chat.png",
    "work": "office.png",
    "selfcare": "home.png",
    "spending": "shopping.png",
    "trend": "blank.png",
    "lifestyle": "home.png",
}


@dataclass
class WebtoonPost:
    title: str
    category: str
    cuts: List[dict[str, str]]


@dataclass(frozen=True)
class RenderResult:
    safe_title: str
    output_dir: Path
    image_path: Path
    image_ref: str


def load_rgba(path: Path) -> Image.Image:
    if not path.exists():
        raise FileNotFoundError(f"파일이 없습니다: {path}")
    return Image.open(path).convert("RGBA")


def get_font(size: int) -> ImageFont.FreeTypeFont:
    if not FONT_PATH.exists():
        raise FileNotFoundError(f"폰트 파일이 없습니다: {FONT_PATH}")
    return ImageFont.truetype(str(FONT_PATH), size)


def load_post(json_path: Path) -> WebtoonPost:
    with json_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if "title" not in data or "category" not in data or "cuts" not in data:
        raise ValueError("title, category, cuts 필수")

    cuts = data["cuts"]
    if not isinstance(cuts, list) or len(cuts) != 6:
        raise ValueError("cuts는 6개 객체 리스트여야 함")

    normalized_cuts: list[dict[str, str]] = []
    for item in cuts:
        if not isinstance(item, dict):
            raise ValueError("cuts 각 항목은 객체여야 함")
        normalized_cuts.append(
            {
                "type": str(item.get("type", "dialogue")).strip() or "dialogue",
                "speaker": _normalize_speaker(str(item.get("speaker", "none")).strip() or "none"),
                "text": str(item.get("text", "")).strip(),
            }
        )

    return WebtoonPost(
        title=data["title"].strip(),
        category=data["category"].strip(),
        cuts=normalized_cuts,
    )


def sanitize_filename(name: str) -> str:
    invalid_chars = '\\/:*?"<>|'
    sanitized = "".join("_" if ch in invalid_chars else ch for ch in name)
    return sanitized.strip().replace(" ", "_")


def wrap_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    box_w: int,
    box_h: int,
) -> tuple[ImageFont.FreeTypeFont, str]:
    for font_size in range(40, 22, -2):
        font = get_font(font_size)
        approx_width = max(6, int(box_w / (font_size * 0.95)))

        lines = []
        for paragraph in text.split("\n"):
            wrapped = textwrap.wrap(paragraph, width=approx_width) or [""]
            lines.extend(wrapped)

        wrapped_text = "\n".join(lines)
        bbox = draw.multiline_textbbox(
            (0, 0),
            wrapped_text,
            font=font,
            spacing=8,
            align="center",
        )
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]

        if text_w <= box_w and text_h <= box_h:
            return font, wrapped_text

    return get_font(22), text


def draw_text_center(
    draw: ImageDraw.ImageDraw,
    text: str,
    box: tuple[int, int, int, int],
    *,
    fill: tuple[int, int, int, int] = TEXT_COLOR,
) -> None:
    left, top, right, bottom = box
    box_w = right - left
    box_h = bottom - top

    font, wrapped_text = wrap_text(draw, text, box_w, box_h)
    bbox = draw.multiline_textbbox((0, 0), wrapped_text, font=font, spacing=8, align="center")
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    x = left + (box_w - text_w) / 2
    y = top + (box_h - text_h) / 2
    draw.multiline_text((x, y), wrapped_text, font=font, fill=fill, spacing=8, align="center")


def get_panel_boxes() -> List[tuple[int, int, int, int]]:
    inner_w = CANVAS_W - OUTER_MARGIN * 2
    inner_h = CANVAS_H - OUTER_MARGIN * 2 - HEADER_HEIGHT

    panel_w = (inner_w - PANEL_GAP) // 2
    panel_h = (inner_h - PANEL_GAP * 2) // 3

    boxes = []
    for row in range(3):
        for col in range(2):
            x1 = OUTER_MARGIN + col * (panel_w + PANEL_GAP)
            y1 = OUTER_MARGIN + HEADER_HEIGHT + row * (panel_h + PANEL_GAP)
            x2 = x1 + panel_w
            y2 = y1 + panel_h
            boxes.append((x1, y1, x2, y2))
    return boxes


def paste_centered(canvas: Image.Image, asset: Image.Image, area: tuple[int, int, int, int]) -> None:
    left, top, right, bottom = area
    area_w = right - left
    area_h = bottom - top

    rendered = _prepare_fox_asset(asset)
    rendered.thumbnail(
        (int(area_w * 0.8), int(area_h * 0.82)),
        Image.Resampling.LANCZOS,
    )
    x = left + (area_w - rendered.width) // 2
    y = top + (area_h - rendered.height) // 2
    canvas.alpha_composite(rendered, (x, y))


def _prepare_fox_asset(asset: Image.Image) -> Image.Image:
    cleaned = _remove_checkerboard_background(asset)
    bbox = cleaned.getbbox()
    if bbox is None:
        return cleaned
    return cleaned.crop(bbox)


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


def _speaker_label(speaker: str) -> str:
    labels = {
        "fox": "여우리",
        "other": "상대",
        "none": "",
    }
    return labels.get(speaker, "")


def _normalize_speaker(speaker: str) -> str:
    if speaker == "me":
        return "fox"
    return speaker


def draw_speech_box(
    draw: ImageDraw.ImageDraw,
    cut: dict[str, str],
    panel_box: tuple[int, int, int, int],
) -> None:
    x1, y1, x2, y2 = panel_box
    panel_w = x2 - x1
    panel_h = y2 - y1
    box = (x1 + 14, y1 + 14, x2 - 14, y1 + int(panel_h * 0.37))
    bubble_fill = (255, 253, 248, 245)
    bubble_outline = (49, 43, 38, 255)
    text_fill = TEXT_COLOR

    cut_type = cut["type"]
    speaker = _normalize_speaker(cut["speaker"])
    speaker_label = _speaker_label(speaker)
    text = cut["text"]

    if cut_type == "fact":
        bubble_fill = (46, 42, 38, 245)
        bubble_outline = (46, 42, 38, 255)
        text_fill = (255, 248, 240, 255)
    elif cut_type == "narration":
        bubble_fill = (242, 234, 221, 235)
        bubble_outline = (183, 166, 147, 255)

    draw.rounded_rectangle(box, radius=26, fill=bubble_fill, outline=bubble_outline, width=3)

    if cut_type == "dialogue":
        tail_y = box[3]
        if speaker == "other":
            tail = [(box[0] + 76, tail_y), (box[0] + 116, tail_y), (box[0] + 92, tail_y + 26)]
        else:
            tail = [(box[2] - 116, tail_y), (box[2] - 76, tail_y), (box[2] - 92, tail_y + 26)]
        draw.polygon(tail, fill=bubble_fill, outline=bubble_outline)

    if speaker_label:
        label_font = get_font(18)
        label_box = (box[0] + 14, box[1] + 10, box[0] + 110, box[1] + 40)
        label_fill = (233, 226, 216, 255) if cut_type != "fact" else (88, 80, 74, 255)
        draw.rounded_rectangle(label_box, radius=12, fill=label_fill)
        draw_text_center(draw, speaker_label, label_box, fill=text_fill)
        text_top = box[1] + 42
    else:
        label_font = None
        text_top = box[1] + 16

    text_box = (box[0] + 16, text_top, box[2] - 16, box[3] - 14)
    draw_text_center(draw, text, text_box, fill=text_fill)


def create_panel_background(panel_size: tuple[int, int], bg_path: Path | None) -> Image.Image:
    pw, ph = panel_size
    panel = Image.new("RGBA", (pw, ph), (255, 255, 255, 220))

    if bg_path and bg_path.exists():
        bg = load_rgba(bg_path).resize((pw, ph), Image.Resampling.LANCZOS)
        panel.alpha_composite(bg)

    overlay = Image.new("RGBA", (pw, ph), (255, 255, 255, 70))
    panel.alpha_composite(overlay)
    return panel


def render_6panel(
    post: WebtoonPost,
    *,
    output_dir: Path | None = None,
    fox_paths: list[Path] | None = None,
    bg_path: Path | None = None,
) -> Path:
    canvas = Image.new("RGBA", (CANVAS_W, CANVAS_H), BG_COLOR)
    draw = ImageDraw.Draw(canvas)

    fallback_assets = PANEL_VISUAL_RULES.get(post.category, PANEL_VISUAL_RULES["lifestyle"])
    fox_paths = fox_paths or [FOX_DIR / name for name in fallback_assets]
    if bg_path is None:
        bg_name = PANEL_BG_RULES.get(post.category, "blank.png")
        bg_path = BG_DIR / bg_name

    boxes = get_panel_boxes()
    for i, box in enumerate(boxes):
        x1, y1, x2, y2 = box
        pw = x2 - x1
        ph = y2 - y1

        panel_bg = create_panel_background((pw, ph), bg_path)
        canvas.alpha_composite(panel_bg, (x1, y1))
        draw.rounded_rectangle(box, radius=28, outline=(220, 210, 200, 255), width=3)

        asset_area = (x1 + 24, y1 + int(ph * 0.40), x2 - 24, y2 - 20)

        asset_path = fox_paths[i]
        show_fox = _normalize_speaker(post.cuts[i]["speaker"]) != "other"
        if show_fox and asset_path.exists():
            paste_centered(canvas, load_rgba(asset_path), asset_area)

        draw_speech_box(draw, post.cuts[i], box)

    final_output_dir = output_dir or (OUTPUT_DIR / sanitize_filename(post.title))
    final_output_dir.mkdir(parents=True, exist_ok=True)
    output_path = final_output_dir / "webtoon_6panel.png"
    canvas.save(output_path)
    return output_path


class CarouselRenderer:
    def __init__(self, settings: Settings, logger) -> None:
        self.settings = settings
        self.logger = logger

    def render(self, content: GeneratedContent, visuals: ResolvedVisuals) -> RenderResult | None:
        safe_title = sanitize_filename(content.title)
        output_dir = self.settings.output_dir / safe_title
        post = WebtoonPost(
            title=content.title,
            category=content.category,
            cuts=[
                {"type": cut.type, "speaker": cut.speaker, "text": cut.text}
                for cut in content.cuts
            ],
        )
        try:
            image_path = render_6panel(
                post,
                output_dir=output_dir,
                fox_paths=visuals.cuts,
                bg_path=visuals.background,
            )
            self.logger.info("렌더링 성공 | %s", image_path)
            return RenderResult(
                safe_title=safe_title,
                output_dir=output_dir,
                image_path=image_path,
                image_ref=_to_output_ref(image_path, self.settings),
            )
        except Exception as error:  # noqa: BLE001
            self.logger.error("렌더링 실패 | title=%s | %s", content.title, error)
            return None


def _to_output_ref(path: Path, settings: Settings) -> str:
    if settings.output_base_url:
        relative = path.relative_to(settings.output_dir).as_posix()
        return f"{settings.output_base_url.rstrip('/')}/{relative}"
    return str(path)


def main() -> None:
    sample_json = BASE_DIR / "sample_6panel.json"
    post = load_post(sample_json)
    output_path = render_6panel(post)
    print(f"생성 완료: {output_path}")


if __name__ == "__main__":
    main()
