# Handoff

이 문서는 현재 레포의 실제 운영 방향을 빠르게 복구하기 위한 요약입니다.

## 현재 목표

`estj_fox` 계정은 이제 자동 카피 생성보다 `고민 수집 + 사람이 답변 작성 + 2장 카드 렌더` 흐름으로 운영합니다.

현재 프로그램이 담당하는 범위:

- 공개 신호에서 고민 후보 수집
- 상위 고민을 Notion DB에 `Collected` 상태로 저장
- 사람이 작성한 답변 JSON을 2장 이미지로 렌더

현재 프로그램이 하지 않는 일:

- 자동 6컷 웹툰 생성
- OpenAI 기반 메인 카피 생성
- Instagram 업로드
- 게시 자동화

## 현재 기준 메인 파일

- [main.py](/Users/jongyeonkim/Desktop/instar_fox_img/instar_fox_img/main.py)
  고민 수집 후 Notion에 저장

- [daily_worry.py](/Users/jongyeonkim/Desktop/instar_fox_img/instar_fox_img/daily_worry.py)
  Google Trends / Google Suggest 기반 고민 수집기

- [notion_writer.py](/Users/jongyeonkim/Desktop/instar_fox_img/instar_fox_img/notion_writer.py)
  새 Worry DB 구조 기준 `Collected` 저장기

- [manual_worry_solution.py](/Users/jongyeonkim/Desktop/instar_fox_img/instar_fox_img/manual_worry_solution.py)
  사람이 쓰는 수동 답변 JSON 로더

- [render_manual_worry_solution.py](/Users/jongyeonkim/Desktop/instar_fox_img/instar_fox_img/render_manual_worry_solution.py)
  수동 답변 JSON을 2장 카드로 렌더

- [worry_solution_renderer.py](/Users/jongyeonkim/Desktop/instar_fox_img/instar_fox_img/worry_solution_renderer.py)
  고민 카드 / 솔루션 카드 렌더러

- [notion_worry_db_schema.md](/Users/jongyeonkim/Desktop/instar_fox_img/instar_fox_img/notion_worry_db_schema.md)
  새 Notion DB 스키마 문서

## 현재 확인된 것

- 수동 답변 JSON 렌더 성공
- `worry_slide.png`, `solution_slide.png` 2장 출력 성공
- 여우 PNG 체커보드 제거 성공
- `main.py`는 고민 수집 후 Notion `Collected` 저장 흐름으로 교체됨

샘플 출력:

- [worry_slide.png](/Users/jongyeonkim/Desktop/instar_fox_img/instar_fox_img/output/답장은_우선순위다/worry_slide.png)
- [solution_slide.png](/Users/jongyeonkim/Desktop/instar_fox_img/instar_fox_img/output/답장은_우선순위다/solution_slide.png)

## 현재 남아 있는 핵심 이슈

### 1. Notion DB 실물 스키마 변경 필요

코드는 새 Worry DB 구조를 기준으로 바뀌었지만, 실제 워크스페이스 DB는 아직 확인/변경하지 못했습니다.

이유:

- 실제 `NOTION_DATABASE_ID`가 로컬 `.env`에 없어서 현재 세션에서 대상 DB를 특정할 수 없었음

필요한 최소 속성:

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

권장 추가 속성:

- `SolutionTitle`
- `SolutionBody`
- `FinalLine`
- `RenderedWorryImage`
- `RenderedSolutionImage`

현재 실제 DB 기준:

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

### 2. 구형 자동 생성 파일 정리 (완료)

이전 자동 생성 경로 파일은 `legacy/` 로 이동했습니다. 상세 목록과 보관 사유는 [legacy/README.md](legacy/README.md) 참고.

이동 대상:

- OpenAI 자동 카피: `content_generator.py`, `worry_solution_generator.py`, `scorer.py`
- 6컷 웹툰: `renderer.py`, `webtoon_composer.py`, `sample_6panel.json`
- 자동 비주얼: `asset_mapper.py`, `pollinations_generator.py`
- 정적 카드 (릴스로 대체): `estj_card_renderer.py`, `trend_card_renderer.py`
- 기타: `daily_issue.py`, `daily_worry_solution.py`, `deduplicator.py`

`trend_collector.py` 는 현재 `pipeline.py` 에서 트렌드 릴스용으로 **계속 사용 중** 이라 루트에 남겼습니다.

### 3. Notion 기반 수동 작성 UX 미완성

지금은 두 방식이 섞여 있습니다.

- `main.py`로 고민 수집 후 Notion 저장
- `sample_manual_worry_solution.json` 같은 수동 JSON 렌더

다음 단계는 둘 중 하나로 통일하는 것이 좋습니다.

- Notion에서 직접 답변 작성 후 렌더
- 로컬 JSON 작성 후 렌더

## 실행 방법

고민 수집 후 Notion 저장:

```bash
python main.py
```

수동 답변 렌더:

```bash
python render_manual_worry_solution.py sample_manual_worry_solution.json
```

## 추천 다음 작업

1. 실제 Notion DB를 새 스키마로 변경
2. `WriterAnswer` 기반 입력 규칙 확정
3. Notion 페이지에서 답변을 읽어와 자동 렌더하는 스크립트 추가
4. 구형 자동 생성 파일 정리

## 참고

- 현재 `config.py`는 `OPENAI_API_KEY` 없이도 기본 운영 경로가 동작하도록 수정됨
- OpenAI 기반 생성 실험 경로는 별도 유지 가능하지만, 메인 흐름에서는 필수가 아님
