# estj_fox 콘텐츠 초안 자동 생성기

한국 트렌드 키워드를 수집하고, 인스타 캐릭터 콘텐츠로 쓸 수 있는 주제만 고른 뒤, 3컷 캐러셀 초안을 생성해서 Notion DB에 `Draft` 상태로 저장하는 MVP입니다.

## 구성 파일

- `main.py`: 한 번 실행되는 전체 파이프라인 진입점
- `config.py`: 환경변수 로드와 설정 관리
- `logger.py`: 콘솔 + 파일 로깅
- `trend_collector.py`: 한국 트렌드 키워드 수집
- `topic_filter.py`: 민감 이슈 제외 및 캐릭터용 주제 선별
- `content_generator.py`: OpenAI Responses API로 JSON 생성
- `scorer.py`: 후보 점수 계산과 추천순 정렬용 보조 로직
- `deduplicator.py`: 최근 14일 Notion 주제와 중복 검사
- `notion_writer.py`: Notion DB 저장

## 설치 방법

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## .env 예시

`.env.example` 을 복사해서 `.env` 로 사용합니다.

```env
OPENAI_API_KEY=sk-...
NOTION_API_KEY=secret_...
NOTION_DATABASE_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_MODEL=gpt-5.4
MAX_TOPICS_PER_RUN=5
LOCALE=ko-KR
TIMEZONE=Asia/Seoul
```

## 실행 방법

```bash
python main.py
```

cron 친화적으로 설계되어 있으므로 하루 1회 배치 실행에 바로 붙일 수 있습니다.

예시:

```bash
0 9 * * * cd /path/to/estj_fox && /usr/bin/python3 main.py
```

## GitHub Actions 배포

레포에 포함된 워크플로 파일:

- `.github/workflows/daily_generate.yml`

동작:

- 매일 `UTC 00:00` 에 실행
- 한국 시간 기준 `09:00` 에 해당
- GitHub Actions 화면에서 `Run workflow` 로 수동 실행 가능

필수 GitHub Secrets:

- `OPENAI_API_KEY`
- `NOTION_API_KEY`
- `NOTION_DATABASE_ID`

선택 GitHub Secrets:

- `OPENAI_MODEL`
- `MAX_TOPICS_PER_RUN`
- `LOCALE`
- `TIMEZONE`

권장 기본값:

- `OPENAI_MODEL=gpt-5.4`
- `MAX_TOPICS_PER_RUN=5`
- `LOCALE=ko-KR`
- `TIMEZONE=Asia/Seoul`

설정 방법:

1. GitHub 레포의 `Settings -> Secrets and variables -> Actions` 로 이동
2. 위 값을 `New repository secret` 으로 등록
3. `Actions` 탭에서 `Daily Estj Fox Draft Generation` 워크플로를 수동 실행해 1회 검증

## Notion DB 준비 방법

아래 속성명을 그대로 맞추는 것을 권장합니다.

| 속성명 | 타입 | 예시 |
| --- | --- | --- |
| `Title` | Title | `필요한 거냐` |
| `Topic` | Rich text | `무지출 챌린지` |
| `Category` | Select | `spending` |
| `Cut1` | Rich text | `시작은 쉬움` |
| `Cut2` | Rich text | `결제는 더 쉬움` |
| `Cut3` | Rich text | `유지가 어렵지` |
| `Caption` | Rich text | `유행은 빨리 오고 카드값은 천천히 안 온다.` |
| `Hashtags` | Rich text | `#절약 #소비 #챌린지` |
| `AIScore` | Number | `87` |
| `Recommended` | Checkbox | `true` |
| `Status` | Status | `Draft`, `Approved` |
| `PreviewText` | Rich text | `시작은 쉬움 | 유지가 어렵지` |
| `PostDate` | Date | `2026-04-13` |

중요:

- 이 프로그램은 항상 `Draft` 로만 저장합니다.
- 실제 업로드는 사람이 검수 후 `Approved` 로 바꾼 항목만 기존 파이프라인이 처리하도록 전제합니다.
- 점수가 가장 높은 1건만 `Recommended=true` 로 표시합니다.
- Notion 뷰는 `Recommended` 내림차순, `AIScore` 내림차순, `PostDate` 내림차순으로 정렬해 두는 것을 권장합니다.

## 동작 흐름

1. `trend_collector.py`
   - `pytrends` 를 먼저 시도합니다.
   - 실패하면 Google Trends RSS 를 시도합니다.
   - 그래도 실패하면 Google Suggest 기반 대체 수집을 시도합니다.
2. `topic_filter.py`
   - 정치, 범죄, 재난, 성적/혐오 이슈를 제외합니다.
   - 자기관리, 소비, 직장, 연애, 습관, 유행, 앱/서비스 문화를 우선 채택합니다.
   - 중복 대체를 위해 내부적으로는 후보를 넉넉히 본 뒤 최종 저장은 최대 5건만 진행합니다.
3. `deduplicator.py`
   - 최근 14일간 Notion DB의 `Title`, `Topic` 과 비교해 단순 중복과 유사 중복을 막습니다.
   - Notion 페이지의 생성 시각 기준으로 최근 14일을 계산합니다.
4. `content_generator.py`
   - OpenAI Responses API의 Structured Outputs 방식으로 JSON 스키마를 강제합니다.
   - 실패 시 1회 재시도합니다.
5. `scorer.py`
   - 생성된 후보별로 실용성, 간결함, 카테고리 우선순위를 반영해 `AIScore` 를 계산합니다.
   - 점수 기준으로 후보를 추천순 정렬합니다.
6. `notion_writer.py`
   - 생성 결과를 Notion DB에 새 페이지로 저장합니다.
   - 가장 높은 점수 1건만 `Recommended=true` 로 저장합니다.
   - 저장 실패 시 로그만 남기고 다음 항목을 계속 처리합니다.

## 로그

- 콘솔 로그 출력
- `logs/estj_fox_pipeline.log` 파일 기록

## 예외 처리 범위

- 트렌드 수집 실패 시 대체 소스 재시도
- OpenAI 응답 비어 있음 / JSON 파싱 실패 / 검증 실패 시 재시도
- Notion 저장 실패 시 다음 항목 계속 진행
- 중복 제거 후 결과가 없으면 정상 종료
- 생성 성공 후보가 5개보다 적어도 가능한 개수만 저장

## 확장 TODO

- Canva 템플릿 연결
- 승인 후 Instagram 자동 업로드
- 주제 랭킹 점수화
