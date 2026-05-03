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

## 자동 카드뉴스 게시

`daily_carousel_pipeline.py`는 매일 최신 트렌드 후보를 수집하고, 규칙 기반 점수 모델로 1위를 고른 뒤 7장 캐러셀을 렌더하고 Instagram에 게시합니다.

선정은 항상 규칙 기반 점수 모델이 맡습니다. 1위가 정해진 뒤에는 `OPENAI_API_KEY`가 있으면 `gpt-5.4-mini`로 훅, 7장 원고, 캡션을 생성합니다. OpenAI 호출이 실패하거나 키가 없으면 기존 템플릿 작성기로 자동 fallback합니다.

점수 기준:

- 트렌드 강도
- 계정 타깃 적합도
- 자극적인 훅으로 바꿀 수 있는 정도
- 하루 지나도 의미가 남는 정도
- 출처 다양성
- 민감 이슈/팩트 리스크/브랜드 불일치 감점

로컬 검증:

```bash
python daily_carousel_pipeline.py --dry-run
```

실제 게시:

```bash
python daily_carousel_pipeline.py
```

GitHub Actions:

- `.github/workflows/post_ai_trend_carousel.yml`
- 매일 12:07 UTC, 21:07 KST 자동 실행
- `workflow_dispatch`로 수동 실행 가능

실행 결과는 `output/daily_carousel/<date>/` 아래에 저장됩니다.

- `ranking.json`: 후보 랭킹과 점수
- `carousel_content.json`: 최종 원고와 캡션
- `slide_01.png` ~ `slide_07.png`: 게시 이미지

## 자동 ESTJ 릴스 게시

`pipeline.py`는 기존처럼 정적 ESTJ 라이브러리에서 날짜별 콘텐츠를 고르는 대신, `daily_trend_ranker.py`의 오늘 1위 트렌드를 ESTJ 관점으로 바꿔 릴스를 만듭니다.

동작 방식:

- `daily_trend_ranker.py`로 오늘의 1위 트렌드 선정
- `OPENAI_API_KEY`가 있으면 `gpt-5.4-mini`가 ESTJ식 제목과 4개 bullet 작성
- OpenAI 호출이 실패하거나 키가 없으면 카테고리별 ESTJ 템플릿으로 fallback
- 트렌드 후보 수집 자체가 실패하면 기존 `estj_content.py` 정적 라이브러리로 fallback
- `estj_reel_renderer.py`가 15초 MP4 렌더
- `instagram_poster.py`가 릴스로 게시

GitHub Actions:

- `.github/workflows/daily_post.yml`
- 매일 11:37 UTC, 20:37 KST 자동 실행
- 이제 트렌드 릴스는 자동 생성/게시하지 않고 ESTJ 릴스 1개만 게시

## 현재 기준

이 레포에서 신뢰해야 하는 기본 운영 명령은 다음 네 개입니다.

```bash
python main.py
python render_answered_notion_pages.py
python daily_pipeline.py
python render_manual_worry_solution.py sample_manual_worry_solution.json
```

릴스 생성이나 Instagram 게시가 필요할 때만 구 경로를 별도로 확인합니다.
