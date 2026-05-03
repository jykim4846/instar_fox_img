# estj_fox 고민 수집 + 답변 카드 렌더 파이프라인

이 레포의 현재 운영 기준은 `고민 수집 -> Notion에서 사람이 답변 작성 -> 2장 카드 렌더`입니다.

과거에 쓰던 릴스 생성, Instagram 게시, OpenAI 자동 카피 생성, 6컷 웹툰 생성 코드는 일부 남아 있지만 현재 메인 운영 경로가 아닙니다.

## 현재 운영 흐름

1. `main.py`
   - Google Trends RSS와 Google Suggest에서 고민 후보를 수집합니다.
   - 민감 키워드와 부적합 후보를 거릅니다.
   - 유사 고민을 정규화하고 상위 후보를 고릅니다.
   - Notion DB에 `WorkflowStage=Collected`, `Status=Draft`로 저장합니다.
2. 사람이 Notion의 `WriterAnswer` 속성에 답변을 작성합니다.
   - 첫 줄: 솔루션 제목
   - 중간 줄: 본문 bullet
   - 마지막 줄: 결론 문장
3. `render_answered_notion_pages.py`
   - `WorkflowStage`가 `Collected` 또는 `Answered`이고 `WriterAnswer`가 채워진 페이지를 찾습니다.
   - 필요하면 `Collected -> Answered`로 전환합니다.
   - `worry_slide.png`, `solution_slide.png` 2장을 렌더합니다.
   - 렌더 결과를 Notion 페이지 본문에 이미지 블록으로 첨부합니다.
   - 성공하면 `WorkflowStage=Rendered`로 전환합니다.

## 실행 명령

설치:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

고민 수집 후 Notion 저장:

```bash
python main.py
```

Notion에서 답변이 작성된 페이지 렌더:

```bash
python render_answered_notion_pages.py
```

수집과 렌더를 한 번에 실행:

```bash
python daily_pipeline.py
```

로컬 JSON 샘플을 바로 렌더:

```bash
python render_manual_worry_solution.py sample_manual_worry_solution.json
```

## 환경변수

필수:

```env
NOTION_API_KEY=secret_...
NOTION_DATABASE_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TIMEZONE=Asia/Seoul
OUTPUT_DIR=./output
```

권장 기본값:

```env
ASSETS_DIR=assets
FOX_ASSETS_DIR=assets/fox
BACKGROUND_ASSETS_DIR=assets/backgrounds
FONTS_DIR=fonts
FONT_PATH=fonts/Pretendard-Bold.otf
IMAGE_SIZE=1080
```

현재 메인 운영 경로에서는 `OPENAI_API_KEY`, Instagram, Cloudinary 환경변수가 필요 없습니다.

## Notion DB

스키마 상세는 [notion_worry_db_schema.md](notion_worry_db_schema.md)를 기준으로 맞춥니다.

필수 속성:

- `Title`
- `Worry`
- `Category`
- `Source`
- `WorrySummary`
- `WriterAnswer`
- `Status`
- `WorkflowStage`
- `CreatedAt`
- `PostDate`

상태값:

- `Status`: `Draft`, `hold`, `Approved`
- `WorkflowStage`: `Collected`, `Answered`, `Rendered`, `Approved`, `Posted`

## 주요 파일

- `main.py`: 고민 수집 후 Notion 저장
- `daily_worry.py`: Google Trends/Suggest 기반 고민 수집기
- `notion_writer.py`: Notion DB에 수집 고민 저장
- `render_answered_notion_pages.py`: Notion 답변 페이지를 2장 카드로 렌더
- `manual_worry_solution.py`: 로컬 JSON 답변 포맷 로더
- `render_manual_worry_solution.py`: 로컬 JSON 답변 렌더
- `worry_solution_renderer.py`: PIL 기반 카드 렌더러
- `mark_answered_notion_pages.py`: `WriterAnswer`가 있는 페이지를 `Answered`로만 전환하는 보조 스크립트
- `daily_pipeline.py`: 수집과 답변 렌더를 이어서 실행하는 보조 스크립트

## 출력

렌더 결과:

- `output/<title>/worry_slide.png`
- `output/<title>/solution_slide.png`

수집 결과를 로컬 JSON으로 저장하는 보조 함수는 `daily_worry.save_worries()`에 남아 있습니다. 현재 `main.py`는 Notion 저장을 기준으로 동작합니다.

## 과거 경로

다음 코드는 현재 메인 운영 경로가 아닙니다.

- `pipeline.py`: ESTJ 릴스, 트렌드 릴스, Instagram 게시까지 포함한 구 운영 파이프라인
- `instagram_poster.py`: Instagram Graph API 게시 보조
- `estj_content.py`, `estj_reel_renderer.py`, `trend_reel_renderer.py`, `trend_collector.py`: 릴스용 구 경로
- `legacy/`: OpenAI 자동 카피, 6컷 웹툰, 구 카드 렌더러 등 보관 코드
- `.github/workflows/daily_post.yml`: 아직 `pipeline.py`를 실행하는 구 GitHub Actions 워크플로우입니다. 현재 운영 방식으로 자동화하려면 별도 수정이 필요합니다.

## 현재 기준

이 레포에서 신뢰해야 하는 기본 운영 명령은 다음 네 개입니다.

```bash
python main.py
python render_answered_notion_pages.py
python daily_pipeline.py
python render_manual_worry_solution.py sample_manual_worry_solution.json
```

릴스 생성이나 Instagram 게시가 필요할 때만 구 경로를 별도로 확인합니다.
