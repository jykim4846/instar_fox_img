# estj_fox 콘텐츠 생성 + 렌더링 파이프라인

한국 트렌드 키워드를 수집하고, 인스타 캐릭터 콘텐츠로 쓸 수 있는 주제만 골라 3컷 캐러셀 문구를 생성합니다. 이후 미리 준비된 여우 PNG 에셋과 배경 PNG를 조합해 1080x1080 PNG 3장을 렌더링하고, 결과를 Notion DB에 `Draft` 상태로 저장합니다.

이 프로그램은 다음까지만 담당합니다.

- 트렌드 수집
- 문구 생성
- PNG 렌더링
- Notion 저장

이 프로그램은 하지 않습니다.

- Canva 사용
- 이미지 생성 AI 호출
- Instagram 업로드
- 게시 자동화

## 프로젝트 구조

```text
project/
├── assets/
│   ├── fox/
│   │   ├── annoyed.png
│   │   ├── arms_crossed.png
│   │   ├── base_reference.png
│   │   ├── closeup_face.png
│   │   ├── judging.png
│   │   ├── lying_down.png
│   │   ├── neutral_front.png
│   │   ├── phone_looking.png
│   │   ├── pointing.png
│   │   └── sitting_blank.png
│   └── backgrounds/
├── fonts/
├── output/
├── asset_mapper.py
├── config.py
├── content_generator.py
├── deduplicator.py
├── logger.py
├── main.py
├── notion_db_template.csv
├── notion_writer.py
├── renderer.py
├── requirements.txt
├── scorer.py
├── topic_filter.py
└── trend_collector.py
```

## 설치 방법

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## .env 예시

```env
OPENAI_API_KEY=sk-...
NOTION_API_KEY=secret_...
NOTION_DATABASE_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_MODEL=gpt-5.4
MAX_TOPICS_PER_RUN=5
LOCALE=ko-KR
TIMEZONE=Asia/Seoul
OUTPUT_BASE_URL=
OUTPUT_DIR=./output
ASSETS_DIR=assets
FOX_ASSETS_DIR=assets/fox
BACKGROUND_ASSETS_DIR=assets/backgrounds
FONTS_DIR=fonts
FONT_PATH=fonts/Pretendard-Bold.otf
IMAGE_SIZE=1080
```

## 실행 방법

```bash
python main.py
```

## GitHub Actions

- `.github/workflows/daily_generate.yml`
- 매일 `UTC 00:00`, 한국 시간 `09:00`
- 수동 실행 지원
- 생성 이미지들은 `output/` 아래에 저장되고 workflow artifact 로 업로드됩니다.

필수 Secrets:

- `OPENAI_API_KEY`
- `NOTION_API_KEY`
- `NOTION_DATABASE_ID`

선택 Secrets:

- `OPENAI_MODEL`
- `MAX_TOPICS_PER_RUN`
- `LOCALE`
- `TIMEZONE`
- `OUTPUT_BASE_URL`

## Notion DB 속성 예시

| 속성명 | 타입 | 예시 |
| --- | --- | --- |
| `Title` | Title | `필요한 거냐` |
| `Topic` | Rich text | `무지출 챌린지` |
| `Category` | Select | `spending` |
| `TemplateType` | Select | `carousel_3` |
| `Cut1` | Rich text | `시작은 쉬움` |
| `Cut2` | Rich text | `결제는 더 쉬움` |
| `Cut3` | Rich text | `유지가 어렵지` |
| `Caption` | Rich text | `유행은 빨리 오고 카드값은 늦게 온다.` |
| `Hashtags` | Rich text | `#절약 #소비 #챌린지` |
| `Status` | Status | `Draft`, `Approved` |
| `AIScore` | Number | `87` |
| `Recommended` | Checkbox | `true` |
| `PreviewImage1` | Rich text | `./output/example/slide1.png` |
| `PreviewImage2` | Rich text | `./output/example/slide2.png` |
| `PreviewImage3` | Rich text | `./output/example/slide3.png` |
| `Source` | Rich text | `Google Trends RSS` |
| `CreatedAt` | Date | `2026-04-13T09:00:00+09:00` |
| `PostDate` | Date | `2026-04-13` |

중요:

- 새 콘텐츠는 항상 `Draft`
- 사람이 `Approved` 로 바꾼 것만 기존 게시 프로그램이 처리
- `PreviewImage1~3` 는 URL 또는 로컬 경로 문자열 저장

## 동작 흐름

1. `trend_collector.py`
   - pytrends
   - Google Trends RSS
   - Google Suggest fallback
2. `topic_filter.py`
   - 민감 주제 제거
   - 자기관리, 소비, 직장, 연애, 습관, 밈, 앱/서비스 문화 우선
3. `deduplicator.py`
   - 최근 14일간 생성된 `Title`, `Topic` 중복/유사 중복 제거
4. `content_generator.py`
   - OpenAI Responses API로 JSON 생성
   - `visuals` 필드까지 포함
5. `asset_mapper.py`
   - OpenAI visuals 우선
   - 없거나 파일이 없으면 category fallback
6. `renderer.py`
   - Pillow로 1080x1080 이미지 3장 렌더
7. `scorer.py`
   - AIScore 계산
   - 추천 후보 정렬
8. `notion_writer.py`
   - Notion DB에 `Draft` 상태 저장
   - 렌더된 3장을 Notion 페이지 본문에도 첨부

## 렌더링 규칙

- 기본 배경색: `#F7F3EA`
- 텍스트: 상단 중앙
- 캐릭터: 중앙 하단
- 여우 PNG 비율 유지
- 폰트: `fonts/Pretendard-Bold.otf` 우선
- 폰트가 없으면 기본 폰트 fallback
- 배경 PNG가 없으면 단색 배경으로 fallback

## sample JSON 예시

```json
{
  "title": "필요한 거냐",
  "topic": "무지출 챌린지",
  "category": "spending",
  "template_type": "carousel_3",
  "cut1": "시작은 쉬움",
  "cut2": "결제는 더 쉬움",
  "cut3": "유지가 어렵지",
  "caption": "유행은 빨리 오고 카드값은 늦게 온다.",
  "hashtags": ["#절약", "#소비", "#챌린지"],
  "visuals": {
    "background": "shopping.png",
    "cut1": "phone_looking.png",
    "cut2": "judging.png",
    "cut3": "pointing.png"
  }
}
```

## 예외 처리

- 트렌드 수집 실패 시 fallback 재시도
- OpenAI JSON 파싱 실패 시 재시도
- visuals 파일 누락 시 category fallback
- 배경 누락 시 단색 배경 fallback
- 폰트 누락 시 기본 폰트 fallback
- Notion 저장 실패 시 다음 후보 계속 처리

## TODO

- Approved 상태와 연동한 게시 파이프라인 연결
- 성과 데이터 기반 주제 점수 개선
- 배경/에셋 다양화
- 이미지 업로드 후 public URL 저장
