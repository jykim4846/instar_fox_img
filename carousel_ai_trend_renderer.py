from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


BASE_DIR = Path(__file__).resolve().parent
FONT_PATH = BASE_DIR / "fonts" / "Pretendard-Bold.otf"
OUTPUT_DIR = BASE_DIR / "output" / "ai_trend_carousel"
CANVAS_SIZE = 1080


@dataclass(frozen=True)
class CarouselSlide:
    eyebrow: str
    title: str
    body: list[str]
    footer: str = ""
    inverted: bool = False


SAMPLE_SLIDES = [
    CarouselSlide(
        eyebrow="AI TREND",
        title="AI 안 쓰는 사람이\n더 이상 신중한 사람이\n아닐 수 있다",
        body=["이미 다들 조용히 쓰고 있다."],
    ),
    CarouselSlide(
        eyebrow="QUESTION",
        title="질문이 바뀌었다",
        body=[
            "예전엔",
            "\"AI 써도 괜찮나?\"가 질문이었다.",
            "지금은",
            "\"AI 안 쓰고도 괜찮나?\"가 질문이 됐다.",
        ],
    ),
    CarouselSlide(
        eyebrow="SIGNAL",
        title="AI는 이제\n검색창처럼 쓰인다",
        body=[
            "뉴스 요약도, 쇼핑 비교도, 업무 초안도",
            "먼저 AI에게 물어보는 흐름으로 바뀌고 있다.",
        ],
    ),
    CarouselSlide(
        eyebrow="POINT",
        title="진짜 차이는\nAI를 쓰느냐가 아니다",
        body=[
            "같은 30분 안에",
            "누가 더 많이 시도하고",
            "누가 더 빨리 걸러내느냐다.",
        ],
    ),
    CarouselSlide(
        eyebrow="WARNING",
        title="생각까지 맡기면\n그때부터 위험하다",
        body=[
            "AI는 답을 주는 도구가 아니라",
            "생각의 재료를 압축해주는 도구다.",
            "판단까지 넘기면 기준이 사라진다.",
        ],
        inverted=True,
    ),
    CarouselSlide(
        eyebrow="SAVE THIS",
        title="AI를 잘 쓰는 질문",
        body=[
            "이 주장에 빠진 반례는 뭐야?",
            "더 짧고 세게 말하면?",
            "카드뉴스 5장으로 나누면?",
            "내가 놓친 리스크는 뭐야?",
        ],
    ),
    CarouselSlide(
        eyebrow="TODAY'S RULE",
        title="AI에게 맡길 것과\n내가 판단할 것을\n먼저 나눠라",
        body=[
            "AI는 치트키가 아니다.",
            "반복 작업을 줄이고 판단할 시간을 남기는 방식이다.",
        ],
        footer="저장해두고 다음 작업 전에 다시 보기",
    ),
]


def render_carousel(output_dir: Path = OUTPUT_DIR) -> list[Path]:
    return render_slides(SAMPLE_SLIDES, output_dir)


def render_slides(slides: list[CarouselSlide], output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for index, slide in enumerate(slides, start=1):
        image = _render_slide(slide, index, len(slides))
        path = output_dir / f"slide_{index:02d}.png"
        image.save(path, format="PNG")
        paths.append(path)
    return paths


def _render_slide(slide: CarouselSlide, index: int, total: int) -> Image.Image:
    if slide.inverted:
        bg = (42, 36, 32, 255)
        fg = (255, 248, 240, 255)
        muted = (226, 202, 171, 255)
        accent = (255, 210, 104, 255)
        panel = (62, 54, 48, 255)
    else:
        bg = (247, 243, 234, 255)
        fg = (40, 34, 30, 255)
        muted = (113, 94, 76, 255)
        accent = (215, 86, 56, 255)
        panel = (255, 251, 245, 255)

    image = Image.new("RGBA", (CANVAS_SIZE, CANVAS_SIZE), bg)
    draw = ImageDraw.Draw(image)

    draw.rounded_rectangle((54, 54, 1026, 1026), radius=34, outline=accent, width=5)
    draw.rounded_rectangle((94, 104, 986, 970), radius=28, fill=panel)

    _draw_text(draw, slide.eyebrow, (124, 138), 30, accent)
    _draw_text(draw, f"{index}/{total}", (900, 138), 26, muted)

    title_font = _fit_font(draw, slide.title, 820, 390, 76, min_size=44)
    title_y = 238
    draw.multiline_text((124, title_y), slide.title, font=title_font, fill=fg, spacing=14)

    body_y = 610 if slide.title.count("\n") >= 2 else 560
    body_font = _font(34)
    cursor_y = body_y
    for line in slide.body:
        wrapped = _wrap(draw, line, body_font, 820)
        draw.multiline_text((124, cursor_y), wrapped, font=body_font, fill=muted, spacing=10)
        bbox = draw.multiline_textbbox((124, cursor_y), wrapped, font=body_font, spacing=10)
        cursor_y = bbox[3] + 28

    if slide.footer:
        draw.rounded_rectangle((124, 858, 956, 920), radius=22, fill=accent)
        _draw_center(draw, slide.footer, (124, 858, 956, 920), 28, (255, 248, 240, 255))

    return image.convert("RGB")


def _fit_font(
    draw: ImageDraw.ImageDraw,
    text: str,
    max_w: int,
    max_h: int,
    start_size: int,
    *,
    min_size: int,
):
    for size in range(start_size, min_size - 1, -2):
        font = _font(size)
        bbox = draw.multiline_textbbox((0, 0), text, font=font, spacing=14)
        if bbox[2] - bbox[0] <= max_w and bbox[3] - bbox[1] <= max_h:
            return font
    return _font(min_size)


def _wrap(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_w: int) -> str:
    words = text.split()
    if not words:
        return text
    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        trial = f"{current} {word}"
        bbox = draw.textbbox((0, 0), trial, font=font)
        if bbox[2] - bbox[0] <= max_w:
            current = trial
            continue
        lines.append(current)
        current = word
    lines.append(current)
    return "\n".join(lines)


def _draw_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    xy: tuple[int, int],
    size: int,
    fill: tuple[int, int, int, int],
) -> None:
    draw.text(xy, text, font=_font(size), fill=fill)


def _draw_center(
    draw: ImageDraw.ImageDraw,
    text: str,
    box: tuple[int, int, int, int],
    size: int,
    fill: tuple[int, int, int, int],
) -> None:
    font = _font(size)
    bbox = draw.textbbox((0, 0), text, font=font)
    x1, y1, x2, y2 = box
    x = x1 + ((x2 - x1) - (bbox[2] - bbox[0])) / 2
    y = y1 + ((y2 - y1) - (bbox[3] - bbox[1])) / 2
    draw.text((x, y), text, font=font, fill=fill)


def _font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_PATH), size)


if __name__ == "__main__":
    for rendered_path in render_carousel():
        print(rendered_path)
