from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class ESTJCard:
    title: str
    bullets: list[str]
    hashtags: str


LIBRARY: list[ESTJCard] = [
    # ── 일상 밈 ──────────────────────────────────
    ESTJCard(
        title="ESTJ가 배민 주문할 때",
        bullets=[
            "메뉴 고르는 데 30초, 리뷰 읽는 데 10분",
            "배달비 0원 필터 먼저 켬",
            "쿠폰 적용 안 했으면 주문 취소하고 다시 함",
            "도착 예정 시간 1분 지나면 배달 추적 시작",
        ],
        hashtags="#ESTJ #MBTI #배달의민족 #배민 #ESTJ일상",
    ),
    ESTJCard(
        title="ESTJ의 넷플릭스 고르기",
        bullets=[
            "고르는 시간 > 보는 시간",
            "평점 낮으면 아무리 추천해도 안 봄",
            "시리즈 1화에서 결정. 재미없으면 바로 손절",
            "결국 봤던 거 또 봄",
        ],
        hashtags="#ESTJ #MBTI #넷플릭스 #넷플추천 #ESTJ취향",
    ),
    ESTJCard(
        title="ESTJ의 카카오톡",
        bullets=[
            "읽고 2분 안에 답장 아니면 까먹음",
            "단톡방 999+ 알림은 정신건강에 해로움",
            "이모티콘 구매 이력: ㅋㅋ 세트 1개",
            "'네' '넵' 'ㅇㅇ' 이 세 개로 대화 가능",
        ],
        hashtags="#ESTJ #MBTI #카톡 #카카오톡 #ESTJ연락",
    ),
    ESTJCard(
        title="ESTJ가 카페 갈 때",
        bullets=[
            "메뉴판 5초 보고 아아 주문",
            "콘센트 자리 먼저 확보",
            "옆 테이블 통화 소리에 속으로 항의문 작성 중",
            "2시간 후 할 일 다 끝내고 뿌듯하게 퇴장",
        ],
        hashtags="#ESTJ #MBTI #카페 #아아 #ESTJ일상",
    ),
    ESTJCard(
        title="ESTJ의 유튜브 시청",
        bullets=[
            "2배속이 기본 세팅",
            "인트로 스킵, 광고 스킵, 본론 어디?",
            "정보 영상만 저장하고 안 봄",
            "'10분 요약' 영상을 또 2배속으로 봄",
        ],
        hashtags="#ESTJ #MBTI #유튜브 #ESTJ특징 #효율",
    ),
    ESTJCard(
        title="ESTJ의 장보기",
        bullets=[
            "장볼 목록 메모장에 미리 작성",
            "동선 짜서 한 바퀴에 끝냄",
            "1+1이면 필요 없어도 일단 계산기 켬",
            "계산대 줄 서면서 다음 일정 체크",
        ],
        hashtags="#ESTJ #MBTI #장보기 #마트 #ESTJ일상",
    ),
    ESTJCard(
        title="ESTJ가 청소할 때",
        bullets=[
            "한번 시작하면 대청소로 번짐",
            "정리하다 못 보던 먼지 발견하면 분노 청소",
            "가족한테 '이거 왜 여기 있어?' 심문 시작",
            "끝나면 사진 찍고 싶을 정도로 뿌듯",
        ],
        hashtags="#ESTJ #MBTI #청소 #대청소 #ESTJ일상",
    ),
    ESTJCard(
        title="ESTJ가 다이어트할 때",
        bullets=[
            "엑셀로 식단표 짬",
            "3일째 완벽 실행. 4일째 치킨 시킴",
            "치킨 먹고 자괴감에 운동 2배로 함",
            "결국 루틴 돌아오면 다시 완벽해짐",
        ],
        hashtags="#ESTJ #MBTI #다이어트 #식단 #ESTJ공감",
    ),
    ESTJCard(
        title="ESTJ가 운전할 때",
        bullets=[
            "네비 찍기 전에 이미 길 알고 있음",
            "앞차 깜빡이 안 켜면 혈압 상승",
            "조수석 사람한테 네비 역할 부여",
            "목적지 10분 전 도착이 국룰",
        ],
        hashtags="#ESTJ #MBTI #운전 #드라이브 #ESTJ일상",
    ),
    ESTJCard(
        title="ESTJ가 이사할 때",
        bullets=[
            "2주 전부터 짐 분류 스프레드시트 작성",
            "박스에 라벨 안 붙이면 불안함",
            "이사 당일 업체보다 본인이 더 지휘함",
            "입주 첫날 와이파이 설치가 1순위",
        ],
        hashtags="#ESTJ #MBTI #이사 #ESTJ특징 #계획형인간",
    ),
    # ── 관계 & 소통 ──────────────────────────────
    ESTJCard(
        title="ESTJ한테 절대 하면 안 되는 말",
        bullets=[
            "'대충 해' — 이 세 글자가 제일 힘듦",
            "'나중에 할게' — 나중이 언제인데?",
            "'몰라 알아서 해' — 기준을 달라는 거임",
            "'그냥 느낌이 그래' — 근거를 달라는 거임",
        ],
        hashtags="#ESTJ #MBTI #MBTI공감 #ESTJ특징 #빡침",
    ),
    ESTJCard(
        title="ESTJ가 진짜 화났을 때",
        bullets=[
            "말이 갑자기 존댓말로 바뀜",
            "'아 네 알겠습니다' = 최후통첩",
            "조용해지면 이미 정리 끝난 거임",
            "다음 날 아무 일 없던 것처럼 행동하는데 기억은 평생 함",
        ],
        hashtags="#ESTJ #MBTI #화날때 #ESTJ분노 #MBTI공감",
    ),
    ESTJCard(
        title="ESTJ의 애정 표현법",
        bullets=[
            "'밥 먹었어?' = 사랑한다는 뜻",
            "상대 일정 외우고 있음 (본인도 모르게)",
            "선물은 실용적인 것만. 감성 선물은 어색",
            "말로 안 하고 행동으로 보여주는데 티가 안 남",
        ],
        hashtags="#ESTJ #MBTI #애정표현 #ESTJ연애 #MBTI연애",
    ),
    ESTJCard(
        title="ESTJ와 친해지는 법",
        bullets=[
            "약속 시간 딱 맞춰 오면 호감도 +50",
            "쓸데없는 눈치 말고 할 말 하면 됨",
            "한번 믿으면 끝까지 편 들어줌",
            "근데 신뢰 깨지면 복구 불가",
        ],
        hashtags="#ESTJ #MBTI #친구 #ESTJ관계 #MBTI관계",
    ),
    ESTJCard(
        title="ESTJ가 좋아하는 사람 생기면",
        bullets=[
            "갑자기 상대 취향 리서치 시작",
            "데이트 코스를 3개 짜놓고 고민함",
            "고백 타이밍도 전략적으로 계산",
            "근데 막상 앞에 서면 어버버함",
        ],
        hashtags="#ESTJ #MBTI #짝사랑 #ESTJ연애 #설렘",
    ),
    ESTJCard(
        title="ESTJ가 소개팅 나가면",
        bullets=[
            "30분 전에 도착해서 자리 세팅",
            "대화 주제 3개 미리 준비해옴",
            "상대 말에 리액션보다 분석이 먼저",
            "끝나고 5분 안에 결론 남: '됨' or '안됨'",
        ],
        hashtags="#ESTJ #MBTI #소개팅 #ESTJ연애 #MBTI연애",
    ),
    # ── 직장 & 학교 ──────────────────────────────
    ESTJCard(
        title="ESTJ의 팀플 실화",
        bullets=[
            "첫 미팅에서 혼자 역할 분배 다 함",
            "공유 문서 만들고 마감일 박아둠",
            "'다 했어요~' 하면 직접 열어서 확인함",
            "결국 본인이 60% 이상 함",
        ],
        hashtags="#ESTJ #MBTI #팀플 #조별과제 #대학생",
    ),
    ESTJCard(
        title="ESTJ가 팀장일 때",
        bullets=[
            "월요일 아침에 주간 목표 공유하는 타입",
            "보고는 두괄식만 받음. 서론 길면 '결론이?'",
            "잘하면 칭찬 확실, 못하면 피드백도 확실",
            "퇴근 시간 되면 '빨리 가세요' 하는 팀장",
        ],
        hashtags="#ESTJ #MBTI #직장인 #팀장 #리더십",
    ),
    ESTJCard(
        title="ESTJ의 회의 자세",
        bullets=[
            "아젠다 없는 회의 = 시간 낭비 = 고통",
            "'그래서 결론이 뭔데요' 참는 게 일임",
            "회의록은 실시간으로 정리 중",
            "30분 넘어가면 눈빛이 달라짐",
        ],
        hashtags="#ESTJ #MBTI #회의 #직장인 #회사생활",
    ),
    ESTJCard(
        title="ESTJ 신입사원 시절",
        bullets=[
            "출근 첫날 회사 조직도 외워옴",
            "메모 습관 때문에 펜 소비가 빠름",
            "어리바리한 척하면서 이미 구조 파악 끝",
            "3개월 차에 '원래 있던 사람 같다' 소리 들음",
        ],
        hashtags="#ESTJ #MBTI #신입 #직장인 #회사생활",
    ),
    ESTJCard(
        title="ESTJ의 시험 기간",
        bullets=[
            "시험 2주 전부터 과목별 시간표 짬",
            "형광펜 색깔별로 의미가 다름",
            "계획대로 안 되면 계획을 수정하지 포기는 없음",
            "끝나면 자기가 짠 플래너 보며 감동받음",
        ],
        hashtags="#ESTJ #MBTI #시험기간 #공부 #대학생",
    ),
    # ── 여행 & 취미 ──────────────────────────────
    ESTJCard(
        title="ESTJ의 여행 준비",
        bullets=[
            "2주 전: 항공-숙소-맛집-동선 완성",
            "패킹리스트 체크하면서 줄 그음",
            "'자유 일정'이라 쓰고 12시~14시 카페 이미 예약",
            "여행 끝나면 가계부 정리가 마무리 의식",
        ],
        hashtags="#ESTJ #MBTI #여행 #여행준비 #ESTJ여행",
    ),
    ESTJCard(
        title="ESTJ가 등산할 때",
        bullets=[
            "코스 난이도, 소요 시간, 날씨 미리 확인",
            "정상까지 예상 시간보다 빨리 도착해야 만족",
            "중간에 쉬자는 사람한테 '조금만 더' 3회 반복",
            "정상 인증샷은 국룰",
        ],
        hashtags="#ESTJ #MBTI #등산 #주말 #ESTJ취미",
    ),
    ESTJCard(
        title="ESTJ의 운동 루틴",
        bullets=[
            "월수금 상체, 화목 하체 — 엑셀에 기록 중",
            "하루 빠지면 죄책감이 이틀 감",
            "운동 안 한 날은 잠이 안 옴",
            "헬스장 정기권 하루도 안 빠지고 출석하는 유일한 사람",
        ],
        hashtags="#ESTJ #MBTI #운동 #헬스 #갓생",
    ),
    ESTJCard(
        title="ESTJ가 게임하면",
        bullets=[
            "공략 먼저 읽고 시작함",
            "파티원 역할 분배 본인이 함",
            "효율 안 나오는 플레이 보면 답답함",
            "지면 패인 분석 회의 시작",
        ],
        hashtags="#ESTJ #MBTI #게임 #ESTJ취미 #MBTI공감",
    ),
    ESTJCard(
        title="ESTJ의 독서 스타일",
        bullets=[
            "자기계발서 먼저 집음",
            "밑줄 + 포스트잇 + 독서 노트 풀세트",
            "소설은 결말 궁금하면 뒤부터 봄",
            "한 달 독서 목표 세우고 진도율 체크",
        ],
        hashtags="#ESTJ #MBTI #독서 #책추천 #자기계발",
    ),
    # ── 계절 & 이벤트 ────────────────────────────
    ESTJCard(
        title="ESTJ의 월요일 아침",
        bullets=[
            "일요일 밤에 이미 한 주 계획 세움",
            "알람 울리기 전에 일어남",
            "출근길에 오늘 할 일 머릿속 리허설",
            "월요병? 할 일 많으면 오히려 좋음",
        ],
        hashtags="#ESTJ #MBTI #월요일 #출근 #직장인",
    ),
    ESTJCard(
        title="ESTJ의 금요일 저녁",
        bullets=[
            "퇴근 전에 다음 주 월요일 할 일 정리해둠",
            "약속 있으면 퇴근 30분 전부터 마무리 모드",
            "약속 없으면 밀린 집안일이 기다림",
            "주말 계획 없는 금요일은 오히려 불안",
        ],
        hashtags="#ESTJ #MBTI #금요일 #불금 #ESTJ일상",
    ),
    ESTJCard(
        title="ESTJ의 새해 목표",
        bullets=[
            "'올해는 여유롭게' → 1월 3일에 포기",
            "목표를 노션에 OKR로 정리해버림",
            "주간 회고까지 세팅해놓고 실행함",
            "12월에 달성률 계산하는 게 진짜 목표",
        ],
        hashtags="#ESTJ #MBTI #새해목표 #갓생 #OKR",
    ),
    ESTJCard(
        title="ESTJ의 생일",
        bullets=[
            "본인 생일은 별로 신경 안 씀",
            "근데 남이 까먹으면 서운함",
            "생일 선물은 현금이나 기프티콘이 최고",
            "생일에도 할 일은 해야 함",
        ],
        hashtags="#ESTJ #MBTI #생일 #ESTJ일상 #MBTI공감",
    ),
    ESTJCard(
        title="비 오는 날의 ESTJ",
        bullets=[
            "전날 일기예보 보고 우산 이미 가방에 넣어둠",
            "우산 안 가져온 사람 보면 '왜 안 챙겨?' 한마디",
            "비 때문에 계획 틀어지면 플랜B 즉시 가동",
            "비 오는 건 상관없는데 습기 때문에 빨래가 걱정",
        ],
        hashtags="#ESTJ #MBTI #비오는날 #ESTJ특징 #MBTI일상",
    ),
    # ── 성격 & 마인드 ────────────────────────────
    ESTJCard(
        title="ESTJ의 사과법",
        bullets=[
            "잘못 인정하면 바로 사과함. 질질 안 끔",
            "'미안해 근데~'로 시작하면 그건 사과가 아님",
            "사과 후 같은 실수 반복? 그건 상대가 더 싫어함",
            "사과받을 때도 명확한 이유를 듣고 싶음",
        ],
        hashtags="#ESTJ #MBTI #사과 #ESTJ특징 #관계",
    ),
    ESTJCard(
        title="ESTJ가 스트레스 받으면",
        bullets=[
            "갑자기 대청소 시작",
            "아니면 운동을 2배로 함",
            "말 줄어들고 할 일에 더 몰두함",
            "풀리면 '아 그거 별거 아니었어' 하고 넘어감",
        ],
        hashtags="#ESTJ #MBTI #스트레스 #ESTJ힐링 #MBTI공감",
    ),
    ESTJCard(
        title="ESTJ의 계획이 틀어졌을 때",
        bullets=[
            "속으로 '왜???' 3번 외침",
            "겉으론 괜찮은 척하면서 이미 플랜B 짜는 중",
            "즉흥 제안하면 5초간 멈칫 후 수용 가능 여부 판단",
            "결국 플랜B가 원래 계획보다 나은 경우 많음",
        ],
        hashtags="#ESTJ #MBTI #계획 #ESTJ특징 #즉흥",
    ),
    ESTJCard(
        title="ESTJ의 고집 사용법",
        bullets=[
            "데이터 있으면 끝까지 밀고 감",
            "데이터 없으면 의외로 금방 접음",
            "'느낌이 그래서'는 근거 아님",
            "설득하고 싶으면 감정 말고 팩트를 들고 와",
        ],
        hashtags="#ESTJ #MBTI #고집 #설득 #ESTJ특징",
    ),
    ESTJCard(
        title="ESTJ가 감동받으면",
        bullets=[
            "표정은 덤덤한데 귀가 빨개짐",
            "그 자리에서 말 못 하고 나중에 '그때 고마웠어'",
            "감동은 반드시 행동으로 돌려줌",
            "한번 마음에 새기면 10년 뒤에도 기억함",
        ],
        hashtags="#ESTJ #MBTI #감동 #ESTJ감성 #MBTI공감",
    ),
    ESTJCard(
        title="ESTJ가 외로울 때",
        bullets=[
            "외롭다고 말 안 함. 그냥 바빠짐",
            "갑자기 연락 안 하던 사람한테 '밥 먹자' 함",
            "혼자 있는 건 괜찮은데 쓸모없이 혼자인 건 싫음",
            "결국 할 일 만들어서 채움",
        ],
        hashtags="#ESTJ #MBTI #외로움 #ESTJ감성 #혼자",
    ),
    # ── 음식 & 소비 ──────────────────────────────
    ESTJCard(
        title="ESTJ가 맛집 갈 때",
        bullets=[
            "별점 4.0 이하는 검색에서 제외",
            "메뉴 사진 + 리뷰 + 블로그 3개 이상 확인",
            "웨이팅 있으면 시간 대비 효율 계산 시작",
            "기대 이하면 블로그 신뢰도 재평가",
        ],
        hashtags="#ESTJ #MBTI #맛집 #맛집탐방 #ESTJ일상",
    ),
    ESTJCard(
        title="ESTJ의 쇼핑 패턴",
        bullets=[
            "장바구니에 담아두고 3일 뒤에도 사고 싶으면 구매",
            "충동구매 후 영수증 보며 자기 반성문",
            "할인율 계산은 암산으로 즉시",
            "세일 기간 미리 캘린더에 등록",
        ],
        hashtags="#ESTJ #MBTI #쇼핑 #소비 #ESTJ특징",
    ),
    ESTJCard(
        title="ESTJ가 요리하면",
        bullets=[
            "레시피 정확히 따름. 계량스푼 필수",
            "냉장고 정리 상태가 곧 멘탈 상태",
            "설거지는 요리하면서 동시에 함",
            "맛있으면 레시피 즐겨찾기 + 다음 식단에 반영",
        ],
        hashtags="#ESTJ #MBTI #요리 #자취 #ESTJ일상",
    ),
    # ── MBTI 비교 ────────────────────────────────
    ESTJCard(
        title="ESTJ vs INFP: 약속 잡기",
        bullets=[
            "ESTJ: '토요일 2시 강남역 3번 출구'",
            "INFP: '주말에 어디 좋은 데 가자~'",
            "ESTJ: '어디? 몇 시? 뭐 먹을 건데?'",
            "INFP: '...그냥 만나서 정하면 안 돼?'",
        ],
        hashtags="#ESTJ #INFP #MBTI궁합 #MBTI비교 #찐공감",
    ),
    ESTJCard(
        title="ESTJ vs ENFP: 여행 계획",
        bullets=[
            "ESTJ: 10페이지짜리 여행 플래너 공유",
            "ENFP: '와 좋다! 근데 여기도 가보자!'",
            "ESTJ: '동선 다 짠 건데...'",
            "ENFP가 찾은 숨은 맛집이 하이라이트 됨",
        ],
        hashtags="#ESTJ #ENFP #MBTI궁합 #여행 #MBTI비교",
    ),
    ESTJCard(
        title="ESTJ vs INTP: 회의할 때",
        bullets=[
            "ESTJ: '결론부터 말해주세요'",
            "INTP: '가능성을 다 검토해야 하는데...'",
            "ESTJ가 실행력을 INTP가 깊이를 채움",
            "싸우면 무섭지만 시너지 나면 최강 조합",
        ],
        hashtags="#ESTJ #INTP #MBTI궁합 #회의 #MBTI비교",
    ),
    ESTJCard(
        title="ESTJ vs ISFP: 데이트",
        bullets=[
            "ESTJ: '오늘 코스 짰어. 1시 브런치, 3시 전시, 5시 카페'",
            "ISFP: '나 그냥 같이 걷고 싶었는데...'",
            "ESTJ 당황하지만 결국 ISFP 페이스에 맞춤",
            "의외로 둘 다 만족하는 하루",
        ],
        hashtags="#ESTJ #ISFP #MBTI궁합 #데이트 #MBTI비교",
    ),
    ESTJCard(
        title="ESTJ vs ENTJ: 리더 대결",
        bullets=[
            "ENTJ: '큰 그림은 내가 그릴게'",
            "ESTJ: '실행 계획은 내가 짤게'",
            "둘 다 지휘하고 싶어서 초반에 충돌",
            "역할 나누면 역대급 프로젝트 완성",
        ],
        hashtags="#ESTJ #ENTJ #MBTI궁합 #리더십 #MBTI비교",
    ),
    # ── 공감 & 짤감 ──────────────────────────────
    ESTJCard(
        title="ESTJ가 '괜찮아'라고 하면",
        bullets=[
            "진짜 괜찮을 확률 20%",
            "'괜찮아 근데' 뒤에 본심이 있음",
            "표정은 괜찮은데 행동이 달라짐",
            "물어봐주면 솔직해지는 타입",
        ],
        hashtags="#ESTJ #MBTI #괜찮아 #ESTJ공감 #본심",
    ),
    ESTJCard(
        title="ESTJ 특: 이런 거 잘함",
        bullets=[
            "총무, 간사, 회장 맡으면 찐으로 잘함",
            "여행 일정, 회식 예약, 경조사 관리",
            "누가 시킨 것도 아닌데 알아서 정리",
            "감사 인사 받으면 '당연한 건데' 하고 넘어감",
        ],
        hashtags="#ESTJ #MBTI #총무 #ESTJ장점 #믿고맡기는",
    ),
    ESTJCard(
        title="ESTJ의 TMI",
        bullets=[
            "핸드폰 배터리 30% 이하면 불안함",
            "알람은 5분 간격 3개",
            "지갑 속 카드 순서가 정해져 있음",
            "냉장고 속 음료수 라벨 방향 통일",
        ],
        hashtags="#ESTJ #MBTI #TMI #ESTJ일상 #MBTI공감",
    ),
    ESTJCard(
        title="ESTJ 어렸을 때",
        bullets=[
            "방학 숙제 7월에 끝냄",
            "반장 or 부반장 한 번은 해봄",
            "친구들 모임에서 자연스럽게 정산 담당",
            "어른들한테 '야무지다' 소리 자주 들음",
        ],
        hashtags="#ESTJ #MBTI #어린시절 #방학숙제 #야무진",
    ),
    ESTJCard(
        title="ESTJ가 피곤할 때",
        bullets=[
            "말이 평소의 반으로 줄어듦",
            "'괜찮아 그냥 좀 피곤해' = 진짜 한계",
            "피곤해도 할 일은 끝내고 눕는 타입",
            "자고 나면 공장 초기화 완료",
        ],
        hashtags="#ESTJ #MBTI #피곤 #ESTJ공감 #리셋",
    ),
    ESTJCard(
        title="ESTJ가 고마울 때",
        bullets=[
            "입으론 '아 뭘~' 하면서 다음에 밥 사줌",
            "고마운 사람한테 은근히 잘해줌",
            "말로 표현 못 하고 행동으로 갚는 스타일",
            "받은 만큼 돌려주는 게 인생 원칙",
        ],
        hashtags="#ESTJ #MBTI #고마움 #ESTJ감성 #MBTI공감",
    ),
    ESTJCard(
        title="ESTJ의 수면 패턴",
        bullets=[
            "내일 할 일 정리 안 되면 잠이 안 옴",
            "알람 전에 눈 떠지는 신기한 체질",
            "주말이라고 늦잠 못 자. 몸이 거부함",
            "잠들기 전 내일 옷까지 정해둠",
        ],
        hashtags="#ESTJ #MBTI #수면 #아침형인간 #갓생",
    ),
    ESTJCard(
        title="ESTJ가 SNS 하면",
        bullets=[
            "보는 건 매일, 올리는 건 분기 1회",
            "올리면 사진 보정 + 해시태그까지 완벽",
            "남 피드에 좋아요는 누르는데 댓글은 귀찮음",
            "스토리는 여행 때만 씀",
        ],
        hashtags="#ESTJ #MBTI #인스타 #SNS #ESTJ일상",
    ),
    ESTJCard(
        title="ESTJ가 거절할 때",
        bullets=[
            "이유는 명확하게. 돌려 말하면 더 복잡해짐",
            "대안 있으면 같이 제시해줌",
            "거절하고 나서 미안한데 미련은 없음",
            "'다음에는 미리 말해줘' 가 진심 어린 부탁",
        ],
        hashtags="#ESTJ #MBTI #거절 #ESTJ소통 #솔직",
    ),
    ESTJCard(
        title="ESTJ한테 칭찬하는 법",
        bullets=[
            "구체적으로 말해야 진심으로 받아들임",
            "'잘했어'보다 '그 보고서 구조가 깔끔했어'",
            "빈말은 바로 구분하니까 진심일 때만",
            "칭찬받으면 겉은 쿨, 속은 저장 완료",
        ],
        hashtags="#ESTJ #MBTI #칭찬 #ESTJ공감 #소통법",
    ),
]


def get_today() -> ESTJCard:
    idx = date.today().toordinal() % len(LIBRARY)
    return LIBRARY[idx]
