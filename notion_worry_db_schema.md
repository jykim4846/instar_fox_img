# Notion Worry DB Schema

`고민 수집 → 사람 답변 → 2장 렌더 → 검수 → 게시` 워크플로우 기준.

## 속성

### 필수 (코드가 쓰거나 읽는 속성)

| 속성명 | 타입 | 누가 쓰나 | 용도 |
| --- | --- | --- | --- |
| `Title` | Title | `notion_writer.py` write / `render_answered_notion_pages.py` read | 카드 제목 (고민 원문 80자 컷) |
| `Worry` | Rich text | write / read | 대표 고민 문장 |
| `Category` | Select | write / read | `dating`, `work`, `selfcare`, `spending`, `trend`, `lifestyle` |
| `Source` | Rich text | write / read | 수집 출처 요약 (상위 3개 signal) |
| `WorrySummary` | Rich text | write / read | 왜 이 고민이 뽑혔는지 한 줄 |
| `WriterAnswer` | Rich text | read only | 사람이 직접 쓰는 답변 초안. **첫 줄 = 솔루션 제목, 마지막 줄 = 결론, 중간 줄 = 본문** |
| `Status` | Status | write | Notion 네이티브 상태. 수집 시 `Draft` 로 생성 |
| `WorkflowStage` | Select | write / read / update | 파이프라인 단계 (아래 상태 전이 참고) |
| `CreatedAt` | Date | write | 수집 시각 (KST) |
| `PostDate` | Date | write | 게시 예정일 (KST) |

### 권장 (수동 기록용, 코드가 읽지 않음)

| 속성명 | 타입 | 용도 |
| --- | --- | --- |
| `SolutionTitle` | Rich text | `WriterAnswer` 첫 줄 사본 |
| `SolutionBody` | Rich text | `WriterAnswer` 본문 사본 |
| `FinalLine` | Rich text | `WriterAnswer` 마지막 줄 사본 |
| `RenderedWorryImage` | Files & media 또는 Rich text | 렌더된 worry 카드 |
| `RenderedSolutionImage` | Files & media 또는 Rich text | 렌더된 solution 카드 |

참고: 렌더 결과는 자동으로 페이지 본문에 이미지 블록으로 첨부된다 (`render_answered_notion_pages._append_rendered_images`).

## 상태 값

### `Status` (Notion 네이티브)

| 값 | 의미 |
| --- | --- |
| `Draft` | 수집 직후 기본값 (`notion_writer.write_collected_worry`) |
| `hold` | 보류 (수동) |
| `Approved` | 검수 완료 (수동) |

### `WorkflowStage` (Select)

| 값 | 자동 전환 트리거 |
| --- | --- |
| `Collected` | 수집 저장 시 기본 (`notion_writer`) |
| `Answered` | `WriterAnswer` 가 채워진 `Collected` 페이지를 `mark_answered_notion_pages.py` 또는 `render_answered_notion_pages.py` 가 전환 |
| `Rendered` | 2장 카드 렌더 성공 후 (`render_answered_notion_pages.py`) |
| `Approved` | 수동 검수 후 |
| `Posted` | 수동 또는 추후 게시 스크립트 |

## 최소 시작 스키마

필수 속성 10개만 있으면 수집·렌더 파이프라인이 돌아간다. 누락된 속성이 있으면 `NotionWriter` 가 경고 로그를 남기고 해당 속성 없이 저장을 재시도한다 (`notion_writer._extract_missing_properties`).

## 실행 순서

```
main.py              → Collected 상태로 저장
(Notion 에서 WriterAnswer 작성)
render_answered_notion_pages.py  → Answered → Rendered 로 전이, 2장 카드 생성
(검수자가 수동으로 Status=Approved)
```

참고: `pipeline.py`는 릴스 생성과 Instagram 게시까지 포함한 구 운영 경로이며, 현재 Notion 기반 고민 카드 운영 흐름에는 포함하지 않는다.
