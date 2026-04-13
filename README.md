# estj_fox 고민 수집 + 수동 답변 렌더 파이프라인

이 레포는 이제 `트렌드 기반 자동 카피 생성`이 아니라 `고민 수집 -> 사람이 답변 작성 -> 2장 카드 렌더` 흐름으로 운영합니다.

현재 프로그램이 담당하는 범위:

- 공개 신호 기반 고민 수집
- 상위 고민을 Notion DB에 `Collected` 상태로 저장
- 사람이 작성한 답변 JSON을 받아 2장 카드 렌더

현재 프로그램이 하지 않는 일:

- OpenAI 기반 자동 카피 생성
- 6컷 웹툰 자동 생성
- Instagram 업로드
- 게시 자동화

## 프로젝트 구조

```text
project/
├── assets/
│   ├── fox/
│   └── backgrounds/
├── fonts/
├── output/
├── daily_worry.py
├── daily_worry_solution.py
├── main.py
├── manual_worry_solution.py
├── notion_writer.py
├── render_manual_worry_solution.py
├── worry_solution_renderer.py
├── notion_worry_db_schema.md
└── requirements.txt
```

## 설치

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## .env 예시

고민 수집 + Notion 저장용:

```env
NOTION_API_KEY=secret_...
NOTION_DATABASE_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TIMEZONE=Asia/Seoul
OUTPUT_DIR=./output
ASSETS_DIR=assets
FOX_ASSETS_DIR=assets/fox
BACKGROUND_ASSETS_DIR=assets/backgrounds
FONTS_DIR=fonts
FONT_PATH=fonts/Pretendard-Bold.otf
IMAGE_SIZE=1080
```

선택:

```env
OPENAI_API_KEY=
OPENAI_MODEL=gpt-5.4
```

`OPENAI_API_KEY`는 현재 기본 운영 경로에서는 필요 없습니다.

## 실행

고민 수집 후 Notion에 저장:

```bash
python main.py
```

수동 답변 JSON을 2장 카드로 렌더:

```bash
python render_manual_worry_solution.py sample_manual_worry_solution.json
```

호환용 별칭:

```bash
python daily_worry_solution.py sample_manual_worry_solution.json
```

## 수동 입력 포맷

예시는 [sample_manual_worry_solution.json](/Users/jongyeonkim/Desktop/instar_fox_img/instar_fox_img/sample_manual_worry_solution.json)에 있습니다.

필수 필드:

- `title`
- `category`
- `worry`
- `source`
- `worry_summary`
- `worry_story`
- `solution_title`
- `solution_body`
- `final_line`
- `fox_pose`
- `background`

## 출력

렌더 결과:

- `output/<title>/worry_slide.png`
- `output/<title>/solution_slide.png`

수집 결과:

- `output/daily_worry/today_worry.json`

## Notion DB

새 DB 구조는 [notion_worry_db_schema.md](/Users/jongyeonkim/Desktop/instar_fox_img/instar_fox_img/notion_worry_db_schema.md)를 기준으로 맞추면 됩니다.

최소 권장 속성:

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

권장 상태값:

- `Status`: `Draft`, `hold`, `Approved`
- `WorkflowStage`: `Collected`, `Answered`, `Rendered`, `Approved`, `Posted`

## 현재 흐름

1. `daily_worry.py`
   - Google Trends RSS
   - Google Suggest
   - 고민형 패턴 필터
   - 민감 키워드 제거
   - 유사 고민 정규화
2. `main.py`
   - 상위 고민을 Notion에 `Collected` 상태로 저장
3. 사람이 Notion 또는 JSON에서 답변 작성
4. `render_manual_worry_solution.py`
   - 고민 카드 1장
   - 솔루션 카드 1장 렌더

## 비고

- `content_generator.py`, `renderer.py` 같은 이전 자동 생성 경로 파일은 아직 레포에 남아 있을 수 있지만, 현재 운영 메인 경로는 아닙니다.
- OpenAI 기반 자동 솔루션 생성은 보조 실험용으로만 남기거나 이후 제거할 수 있습니다.
