# legacy

현재 운영 경로에서 빠진 이전 세대 코드 모음. 참고용으로만 보관한다.

## 왜 남겨뒀나

- 이전 시도(자동 카피 생성, 6컷 웹툰, 정적 카드, AI 배경 생성)의 출발점을 잃지 않기 위함
- 수동 답변 + 릴스 중심으로 운영 방식이 바뀌었지만, 일부 로직은 향후 참고용으로 유효함

## 실행 보장 없음

- 여기 있는 파일은 루트의 `topic_filter.py` 등 외부 모듈을 상대 경로 없이 import 한다
- 모듈 간 import 도 원래 루트 기준이다 (예: `from content_generator import ...`)
- 그대로 `python legacy/<file>.py` 로 돌아가지 않는다. 되살리려면 루트로 복사하거나 import path 를 조정해야 한다

## 파일별 메모

### OpenAI 자동 카피 경로 (폐기)
- `content_generator.py` — GPT 기반 고민/솔루션 카피 자동 생성
- `worry_solution_generator.py` — 고민 → 솔루션 카피 자동 생성 폴백
- `scorer.py` — 생성 결과 점수화

### 6컷 웹툰 경로 (폐기)
- `renderer.py` — 6컷 웹툰 이미지 렌더
- `webtoon_composer.py` — 6컷 패널 합성
- `sample_6panel.json` — 6컷 웹툰 샘플 입력

### 자동 비주얼 매핑 (폐기)
- `asset_mapper.py` — 카테고리별 여우 표정/배경 매핑
- `pollinations_generator.py` — Pollinations API Studio Ghibli 스타일 배경 생성

### 정적 카드 경로 (릴스로 대체)
- `estj_card_renderer.py` — ESTJ 정적 카드 이미지
- `trend_card_renderer.py` — 트렌드 정적 카드 이미지

### 기타 미사용
- `daily_issue.py` — 이슈형 신호 수집기 (고민 수집으로 흡수됨)
- `daily_worry_solution.py` — `render_manual_worry_solution.py` 얇은 래퍼 (중복)
- `deduplicator.py` — 14일 윈도우 중복 제거 (현재 파이프라인 미사용)
