# Handoff

이 문서는 다른 PC에서 이 레포를 이어받아 작업할 Codex/개발자를 위한 현재 상태 요약입니다.

## 현재 목표

`estj_fox` 인스타 캐릭터 계정용 파이프라인을 운영 중입니다.

현재 프로그램이 담당하는 범위:

- 한국 트렌드 키워드 수집
- 캐릭터 콘텐츠용 주제 필터링
- OpenAI로 3컷 캐러셀 문구 생성
- 로컬 PNG 에셋 기반 1080x1080 이미지 3장 렌더링
- Notion DB에 `Draft` 상태로 저장
- Notion 페이지 본문에 렌더된 이미지 3장 첨부

현재 프로그램이 하지 않는 일:

- Instagram 업로드
- Canva 사용
- 이미지 생성 AI
- 게시 자동화

## 최근 상태

최신 원격 기준 브랜치:

- `main`

최근 중요 커밋:

- `1f3a46b` `Sharpen trend selection and copy generation quality`
- `679d5ce` `Tolerate missing optional Notion properties during draft writes`
- `5e38c9f` `Finish image handling inside the local estj_fox pipeline`
- `dcd422f` `Strip baked checkerboard backgrounds from fox assets at render time`

## 현재 동작 확인된 것

- 로컬 렌더링 성공
- 여우 PNG 체크보드 배경 자동 제거 성공
- 배경 PNG 적용 성공
- Notion Draft 행 생성 성공
- Notion 페이지 본문에 `Rendered Slides` 아래 이미지 3장 첨부 성공
- GitHub Actions에서 `output/` artifact 업로드 성공

## 현재 남아 있는 운영 이슈

### 1. Notion DB 컬럼 불완전

현재 실제 DB 스키마에는 아래 속성이 없습니다.

- `TemplateType`
- `PreviewImage1`
- `PreviewImage2`
- `PreviewImage3`
- `Source`
- `CreatedAt`

그래서 현재 코드는:

- 있으면 저장
- 없으면 건너뛰고 Draft 생성 계속

즉, 페이지 본문 이미지는 붙지만 테이블 컬럼에는 일부 값이 안 보일 수 있습니다.

권장:

Notion DB에 위 컬럼을 추가해서 스키마를 코드와 맞추는 것이 좋습니다.

### 2. 콘텐츠 품질

이전 결과는 너무 generic 하거나 트렌드 연결이 약했습니다.
이를 개선하기 위해 아래를 반영했습니다.

- 의료/사전식 키워드 필터 강화
- Suggest 시드를 생활형/트렌드형으로 교체
- 프롬프트에서 `왜 지금 뜨는지 보이는 생활 장면` 강제
- 위로형/교훈형/사전형 문구 validation 강화

하지만 품질은 여전히 추가 튜닝 대상입니다.

우선 확인 포인트:

- `선정 주제 샘플` 로그
- 생성된 `Title`, `Cut2`, `Cut3`

좋은 결과 기준:

- 키워드가 요즘 왜 보이는지 즉시 감이 와야 함
- 설명문이 아니라 찌르는 한마디여야 함
- 자기계발 명언처럼 보이면 실패

### 3. Notion 미리보기 컬럼 vs 본문 이미지

현재 실제 검수 UX는 페이지 본문 이미지 첨부가 핵심입니다.

DB 테이블에서 곧바로 보고 싶다면:

- `PreviewImage1`
- `PreviewImage2`
- `PreviewImage3`

를 추가한 뒤, 코드가 그 컬럼을 다시 채우도록 두면 됩니다.

## 주요 파일 역할

- [main.py](/Users/jongyeon.kim/Desktop/instar_fox_img/main.py:1)
  전체 파이프라인 진입점

- [trend_collector.py](/Users/jongyeon.kim/Desktop/instar_fox_img/trend_collector.py:1)
  pytrends / Google Trends RSS / Google Suggest fallback

- [topic_filter.py](/Users/jongyeon.kim/Desktop/instar_fox_img/topic_filter.py:1)
  민감 이슈 제거, 생활형/트렌드형 주제 선별

- [content_generator.py](/Users/jongyeon.kim/Desktop/instar_fox_img/content_generator.py:1)
  OpenAI Responses API, structured JSON 생성

- [asset_mapper.py](/Users/jongyeon.kim/Desktop/instar_fox_img/asset_mapper.py:1)
  카테고리별 에셋 fallback 규칙

- [renderer.py](/Users/jongyeon.kim/Desktop/instar_fox_img/renderer.py:1)
  Pillow 렌더링, 체크보드 배경 제거, 폰트/레이아웃 처리

- [notion_writer.py](/Users/jongyeon.kim/Desktop/instar_fox_img/notion_writer.py:1)
  Notion 페이지 생성, 부분 속성 fallback, 본문 이미지 첨부

- [scorer.py](/Users/jongyeon.kim/Desktop/instar_fox_img/scorer.py:1)
  AIScore 계산

## 실제 확인된 Notion 상태

최근 생성된 페이지 예시:

- `습관성 유산처럼 끊기는 관리`

이 페이지는:

- DB 행 생성됨
- 본문에 `Rendered Slides` 아래 이미지 3장 붙어 있음

즉, 이미지 첨부 로직은 현재 동작하고 있습니다.

## 에셋 상태

여우 에셋 폴더:

- `assets/fox/`

배경 에셋 폴더:

- `assets/backgrounds/`

폰트:

- `fonts/Pretendard-Bold.otf`

주의:

- 여우 PNG 원본 일부는 체크보드 배경이 baked-in 되어 있었음
- 렌더 단계에서 edge-connected light pixels 를 투명화하는 전처리 추가됨
- 만약 이후 다른 색 배경 matte PNG가 들어오면 `renderer.py` 의 `_looks_like_checker_bg` 조정 필요

## 실행 방법

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python main.py
```

GitHub Actions:

- `.github/workflows/daily_generate.yml`
- 매일 `UTC 00:00` / 한국 시간 `09:00`

## 집 PC에서 바로 이어서 할 일 추천 순서

1. 레포 pull
2. `.env` 확인
3. `python main.py` 로 로컬 1회 실행
4. Notion 새 Draft 확인
5. 생성된 문구 품질 평가
6. 필요하면 `topic_filter.py`, `content_generator.py`, `scorer.py` 추가 튜닝

## 가장 유력한 다음 작업

### 우선순위 1

Notion DB 스키마를 코드 기대치에 맞추기:

- `TemplateType`
- `PreviewImage1`
- `PreviewImage2`
- `PreviewImage3`
- `Source`
- `CreatedAt`

### 우선순위 2

문구 품질 추가 개선:

- `습관`, `루틴`, `앱`, `구독` 같은 broad keyword가 너무 generic 하면 더 좁혀야 함
- 결과가 평범하면 프롬프트에 더 강한 금지 규칙 추가
- `cut2` 에 트렌드 상황이 드러나지 않으면 실패 처리하는 validation 추가 가능

### 우선순위 3

검수 UX 개선:

- 페이지 커버에 첫 슬라이드 반영
- 본문 이미지 위에 요약 블록 추가
- `PreviewText` 를 다시 채우는 컬럼 복원

## TODO

- Approved 상태와 연동한 게시 파이프라인 연결
- 성과 데이터 기반 주제 점수 개선
- 배경/에셋 다양화
- 이미지 업로드 후 public URL 저장

