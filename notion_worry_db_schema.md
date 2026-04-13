# Notion Worry DB Schema

새 워크플로우 기준:

- `고민 수집`
- `Collected` 상태로 저장
- 사람이 답글 작성
- 2장 렌더
- 검수 후 게시

권장 속성:

| 속성명 | 타입 | 설명 |
| --- | --- | --- |
| `Title` | Title | 카드 제목 |
| `Worry` | Rich text | 대표 고민 문장 |
| `Category` | Select | `dating`, `work`, `selfcare`, `spending`, `trend`, `lifestyle` |
| `Source` | Rich text | 수집 출처 요약 |
| `WorrySummary` | Rich text | 왜 이 고민이 뽑혔는지 한 줄 요약 |
| `WriterAnswer` | Rich text | 사람이 직접 쓰는 답변 초안 |
| `SolutionTitle` | Rich text | 솔루션 카드 제목 |
| `SolutionBody` | Rich text | 솔루션 본문 |
| `FinalLine` | Rich text | 마지막 결론 문장 |
| `RenderedWorryImage` | Rich text | 고민 카드 이미지 경로 또는 URL |
| `RenderedSolutionImage` | Rich text | 솔루션 카드 이미지 경로 또는 URL |
| `Status` | Status | 기존 Notion 상태. 현재 `Draft`, `hold`, `Approved` 유지 |
| `WorkflowStage` | Select | `Collected`, `Answered`, `Rendered`, `Approved`, `Posted` |
| `CreatedAt` | Date | 생성 시각 |
| `PostDate` | Date | 게시 예정일 |

최소 시작 버전:

| 속성명 | 타입 |
| --- | --- |
| `Title` | Title |
| `Worry` | Rich text |
| `Category` | Select |
| `Source` | Rich text |
| `WorrySummary` | Rich text |
| `WriterAnswer` | Rich text |
| `Status` | Status |
| `WorkflowStage` | Select |
| `CreatedAt` | Date |
| `PostDate` | Date |

운영 상태 추천:

- `Status`
  - `Draft`
  - `hold`
  - `Approved`
- `WorkflowStage`
  - `Collected`
  - `Answered`
  - `Rendered`
  - `Approved`
  - `Posted`
