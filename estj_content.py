from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class ESTJCard:
    title: str
    bullets: list[str]
    hashtags: str


LIBRARY: list[ESTJCard] = [
    ESTJCard(
        title="ESTJ가 계획이 바뀔 때",
        bullets=[
            "속으로 '왜 갑자기 바뀌어?' 3번 외침",
            "겉으론 괜찮다며 이미 플랜B 짜는 중",
            "미리 말해줬으면 됐잖아 라는 말 참는 중",
            "결국 더 완벽한 플랜으로 돌아옴",
        ],
        hashtags="#ESTJ #MBTI #계획형인간 #ESTJ특징",
    ),
    ESTJCard(
        title="ESTJ의 카톡 답장 스타일",
        bullets=[
            "용건 없는 연락엔 빠른 답장 기대 X",
            "용건 있으면 2분 안에 답장",
            "이모티콘은 ㅎㅎ 정도가 최선",
            "읽고 바로 답 안 하면 기억에서 사라짐",
        ],
        hashtags="#ESTJ #MBTI #ESTJ연락 #MBTI특징",
    ),
    ESTJCard(
        title="ESTJ가 화났을 때",
        bullets=[
            "말이 갑자기 짧아짐",
            "'알겠어요'는 화났다는 신호",
            "이유 모르면 직접 물어보지 않음",
            "시간 지나면 쿨하게 정리됨",
        ],
        hashtags="#ESTJ #MBTI #ESTJ화날때 #MBTI분석",
    ),
    ESTJCard(
        title="ESTJ의 회의 자세",
        bullets=[
            "결론 먼저, 이유 나중에",
            "회의 시간 낭비하면 속이 탐",
            "아젠다 없는 회의는 고통",
            "한 번에 깔끔하게 정리되는 게 최고",
        ],
        hashtags="#ESTJ #MBTI #직장인MBTI #ESTJ직장",
    ),
    ESTJCard(
        title="ESTJ가 팀장일 때",
        bullets=[
            "목표 먼저 공유하고 역할 딱 나눔",
            "의욕 없는 사람한테 에너지 낭비 안 함",
            "잘하면 잘한다고 확실히 말함",
            "책임은 자기가 지려는 스타일",
        ],
        hashtags="#ESTJ #MBTI #ESTJ리더 #리더십MBTI",
    ),
    ESTJCard(
        title="ESTJ가 약속 취소 당했을 때",
        bullets=[
            "이미 시간 다 비워뒀는데... 속으론 한소리 함",
            "미리 연락 안 하면 더 불쾌",
            "겉으론 '그래 괜찮아' 하지만 재스케줄 기다림",
            "다음 약속엔 전날 확인 메시지가 필수가 됨",
        ],
        hashtags="#ESTJ #MBTI #ESTJ약속 #MBTI공감",
    ),
    ESTJCard(
        title="ESTJ가 좋아하는 사람 생겼을 때",
        bullets=[
            "좋아하는 거 표나지 않으려 하지만 챙김이 늘어남",
            "갑자기 상대 일정 체크가 잦아짐",
            "연락 빈도는 유지하되 반응 속도가 빨라짐",
            "확신이 생기면 직접적으로 고백",
        ],
        hashtags="#ESTJ #MBTI #ESTJ연애 #MBTI연애",
    ),
    ESTJCard(
        title="ESTJ의 연애 스타일",
        bullets=[
            "기념일과 약속은 캘린더에 저장",
            "감정 표현은 말보다 행동으로",
            "상대 요청은 최대한 들어주려 함",
            "모호한 관계는 오래 못 버팀",
        ],
        hashtags="#ESTJ #MBTI #ESTJ연애 #MBTI연애스타일",
    ),
    ESTJCard(
        title="ESTJ가 칭찬받을 때",
        bullets=[
            "'당연한 거 한 건데' 라고 생각함",
            "표정은 덤덤하지만 속으로 뿌듯",
            "더 잘해야겠다는 동기부여로 연결됨",
            "빈말인지 진심인지 구분함",
        ],
        hashtags="#ESTJ #MBTI #ESTJ특징 #MBTI공감",
    ),
    ESTJCard(
        title="ESTJ가 비판받을 때",
        bullets=[
            "사실 기반이면 인정하고 바로 수정",
            "감정적이거나 근거 없으면 흘려들음",
            "같은 실수 두 번은 절대 안 함",
            "다음번엔 더 완벽하게 돌아옴",
        ],
        hashtags="#ESTJ #MBTI #ESTJ특징 #MBTI분석",
    ),
    ESTJCard(
        title="ESTJ의 주말 루틴",
        bullets=[
            "오전 중에 할 일 다 끝냄",
            "점심 뭐 먹을지 아침부터 정해놓음",
            "쉬는 것도 일정에 포함됨",
            "갑자기 약속 잡히면 조율이 필요함",
        ],
        hashtags="#ESTJ #MBTI #ESTJ일상 #MBTI일상",
    ),
    ESTJCard(
        title="ESTJ가 쇼핑할 때",
        bullets=[
            "살 것 목록 미리 정해옴",
            "충동구매 거의 없음",
            "리뷰 꼼꼼히 보고 결정",
            "살 거 아니면 구경도 잘 안 함",
        ],
        hashtags="#ESTJ #MBTI #ESTJ소비 #MBTI쇼핑",
    ),
    ESTJCard(
        title="ESTJ가 맛집 갈 때",
        bullets=[
            "대기줄 있는지 미리 파악해옴",
            "메뉴도 집에서 이미 정해옴",
            "음식 나오는 타이밍 체크",
            "후기는 바로 머릿속에 정리됨",
        ],
        hashtags="#ESTJ #MBTI #ESTJ맛집 #MBTI공감",
    ),
    ESTJCard(
        title="ESTJ의 여행 준비",
        bullets=[
            "출발 2주 전부터 준비 시작",
            "숙소, 교통, 식당 모두 예약 완료",
            "여행 일정표 공유는 기본",
            "예상치 못한 변수가 제일 싫음",
        ],
        hashtags="#ESTJ #MBTI #ESTJ여행 #MBTI여행",
    ),
    ESTJCard(
        title="ESTJ가 지각할 때",
        bullets=[
            "10분 전 도착이 기본인데 지각은 이변 상황",
            "미리 '늦을 것 같아' 연락은 필수",
            "지각 이유 설명이 길어짐",
            "다음엔 더 일찍 출발함",
        ],
        hashtags="#ESTJ #MBTI #ESTJ특징 #시간약속",
    ),
    ESTJCard(
        title="ESTJ가 불공평한 상황 맞닥뜨릴 때",
        bullets=[
            "참다가 한 번에 정리하는 스타일",
            "논리적으로 조목조목 따짐",
            "감정적으로 얘기하면 대화 안 됨",
            "기준이 명확해야 납득함",
        ],
        hashtags="#ESTJ #MBTI #ESTJ특징 #MBTI분석",
    ),
    ESTJCard(
        title="ESTJ의 스트레스 해소법",
        bullets=[
            "할 일 목록 다 지우면 일단 해소됨",
            "운동 아니면 청소",
            "혼자 있는 시간이 좀 필요함",
            "말보단 행동으로 풀어냄",
        ],
        hashtags="#ESTJ #MBTI #ESTJ스트레스 #MBTI힐링",
    ),
    ESTJCard(
        title="ESTJ가 새 친구 사귈 때",
        bullets=[
            "첫인상은 약간 딱딱해 보일 수 있음",
            "신뢰 쌓이면 의외로 잘 챙김",
            "관심사 맞으면 빠르게 친해짐",
            "겉보기와 속 다름을 나중에야 알게 됨",
        ],
        hashtags="#ESTJ #MBTI #ESTJ친구 #MBTI관계",
    ),
    ESTJCard(
        title="ESTJ가 이별할 때",
        bullets=[
            "관계 회복 가능성 냉정하게 판단",
            "결정나면 미련 안 두려 함",
            "이유는 명확하게 말함",
            "시간 지나면 정리하고 앞으로 감",
        ],
        hashtags="#ESTJ #MBTI #ESTJ이별 #MBTI연애",
    ),
    ESTJCard(
        title="ESTJ의 운동 스타일",
        bullets=[
            "루틴 정해두고 꾸준히",
            "목표 수치 설정하고 추적함",
            "빠지면 찜찜해서 어떻게든 채움",
            "결석은 불가항력적 사유일 때만",
        ],
        hashtags="#ESTJ #MBTI #ESTJ운동 #갓생MBTI",
    ),
    ESTJCard(
        title="ESTJ가 요리할 때",
        bullets=[
            "레시피 그대로 따름 (즉흥은 없음)",
            "재료 미리 다 손질해둠",
            "설거지는 바로바로",
            "맛있으면 레시피 저장해둠",
        ],
        hashtags="#ESTJ #MBTI #ESTJ일상 #MBTI공감",
    ),
    ESTJCard(
        title="ESTJ가 SNS 할 때",
        bullets=[
            "보는 건 자주, 올리는 건 가끔",
            "올릴 거면 완성도 있게",
            "댓글은 의미 있는 것만",
            "스토리는 거의 안 올림",
        ],
        hashtags="#ESTJ #MBTI #ESTJ특징 #MBTI인스타",
    ),
    ESTJCard(
        title="ESTJ의 돈 관리",
        bullets=[
            "고정 지출 파악 먼저",
            "예산 세우고 그 안에서 씀",
            "충동구매는 하루 지나도 사고 싶으면 구매",
            "후회하는 소비는 거의 없음",
        ],
        hashtags="#ESTJ #MBTI #ESTJ소비 #MBTI재테크",
    ),
    ESTJCard(
        title="ESTJ가 갈등 해결할 때",
        bullets=[
            "감정 다독이기보다 해결책 먼저",
            "팩트 기반으로 정리",
            "흐지부지 넘어가는 건 싫음",
            "해결되면 깔끔하게 마무리",
        ],
        hashtags="#ESTJ #MBTI #ESTJ특징 #갈등MBTI",
    ),
    ESTJCard(
        title="ESTJ가 새해 목표 세울 때",
        bullets=[
            "구체적인 숫자로 설정 (주 3회, 월 X만원)",
            "실현 가능한 것만 씀",
            "앱이나 노트에 기록해둠",
            "중간 점검도 챙김",
        ],
        hashtags="#ESTJ #MBTI #ESTJ목표 #갓생MBTI",
    ),
    ESTJCard(
        title="ESTJ가 후배 대할 때",
        bullets=[
            "명확하게 지시하고 기대치 전달",
            "잘하면 확실하게 인정해줌",
            "실수는 한 번은 넘어감",
            "두 번은 왜 반복되는지 같이 봄",
        ],
        hashtags="#ESTJ #MBTI #ESTJ직장 #직장인MBTI",
    ),
    ESTJCard(
        title="ESTJ가 선배 대할 때",
        bullets=[
            "존중하지만 무조건 따르진 않음",
            "논리가 있으면 의견 말함",
            "불합리한 건 정중하게 짚음",
            "잘 이끌어주면 열심히 따름",
        ],
        hashtags="#ESTJ #MBTI #ESTJ직장 #직장인MBTI",
    ),
    ESTJCard(
        title="ESTJ vs INFP: 갈등 상황",
        bullets=[
            "ESTJ: 문제 원인부터 파악하자",
            "INFP: 왜 그렇게 느꼈는지 들어줘",
            "서로 원하는 게 달라서 생기는 오해",
            "접점은 상대 방식을 존중해줄 때",
        ],
        hashtags="#ESTJ #INFP #MBTI궁합 #MBTI비교",
    ),
    ESTJCard(
        title="ESTJ vs ENFP: 계획 vs 즉흥",
        bullets=[
            "ESTJ: 다음 주말 뭐 할지 정하자",
            "ENFP: 그때 가서 생각하자",
            "같이 여행 가면 매일 협상",
            "그래도 의외로 잘 맞음",
        ],
        hashtags="#ESTJ #ENFP #MBTI궁합 #MBTI비교",
    ),
    ESTJCard(
        title="ESTJ vs ISFP: 업무 스타일",
        bullets=[
            "ESTJ: 마감 일주일 전에 끝냄",
            "ISFP: 마감 전날 밤 시작",
            "같은 팀이면 속 터짐",
            "결과물 퀄리티는 둘 다 좋은 편",
        ],
        hashtags="#ESTJ #ISFP #MBTI궁합 #MBTI비교",
    ),
    ESTJCard(
        title="ESTJ vs INTP: 회의에서",
        bullets=[
            "ESTJ: 결론부터 말해",
            "INTP: 가능성을 모두 검토해야 해",
            "ESTJ가 속도를 냄, INTP가 깊이를 냄",
            "같이 일하면 의외의 시너지",
        ],
        hashtags="#ESTJ #INTP #MBTI궁합 #MBTI비교",
    ),
    ESTJCard(
        title="ESTJ가 틀렸을 때",
        bullets=[
            "팩트로 증명되면 바로 인정함",
            "감정적으로 몰아붙이면 저항함",
            "인정하면 빠르게 수정하고 넘어감",
            "같은 실수 반복은 절대 없음",
        ],
        hashtags="#ESTJ #MBTI #ESTJ특징 #MBTI분석",
    ),
    ESTJCard(
        title="ESTJ가 거절할 때",
        bullets=[
            "이유는 명확하게",
            "미안하지만 돌려 말하진 않음",
            "대안 있으면 같이 제시함",
            "거절하고 나서 미련 없음",
        ],
        hashtags="#ESTJ #MBTI #ESTJ특징 #거절MBTI",
    ),
    ESTJCard(
        title="ESTJ의 리더십 스타일",
        bullets=[
            "목표와 역할 명확하게 배분",
            "과정보단 결과로 평가",
            "팀원 잘 되길 진심으로 바람",
            "약자 보호하는 스타일",
        ],
        hashtags="#ESTJ #MBTI #ESTJ리더 #리더십MBTI",
    ),
    ESTJCard(
        title="ESTJ가 자기계발할 때",
        bullets=[
            "목표 설정 → 계획 수립 → 실행",
            "책이면 완독, 강의면 끝까지",
            "중간에 포기는 거의 없음",
            "성장 체감되면 더 열심히 함",
        ],
        hashtags="#ESTJ #MBTI #갓생MBTI #ESTJ자기계발",
    ),
    ESTJCard(
        title="ESTJ가 피곤할 때",
        bullets=[
            "말이 더 짧아짐",
            "괜찮냐고 물으면 '응 그냥 피곤해'",
            "쉬고 싶은데 할 일은 해야 해서 투덜거림",
            "자고 나면 리셋됨",
        ],
        hashtags="#ESTJ #MBTI #ESTJ공감 #MBTI일상",
    ),
    ESTJCard(
        title="ESTJ가 누군가 챙길 때",
        bullets=[
            "뭐 필요한지 직접 물음",
            "필요한 거 찾아보고 행동으로 보여줌",
            "감정 공감보다 해결 도움",
            "챙기는 거 표 안 내도 계속함",
        ],
        hashtags="#ESTJ #MBTI #ESTJ애정표현 #MBTI공감",
    ),
    ESTJCard(
        title="ESTJ가 실망했을 때",
        bullets=[
            "먼저 인정하고 사과함",
            "이유보다 책임 먼저",
            "어떻게 만회할지 생각함",
            "스스로 기준 더 높임",
        ],
        hashtags="#ESTJ #MBTI #ESTJ특징 #MBTI분석",
    ),
    ESTJCard(
        title="ESTJ의 고집",
        bullets=[
            "근거 있으면 끝까지 밀고 감",
            "근거 없으면 의외로 유연함",
            "'그냥 그게 맞는 것 같아서'는 안 통함",
            "설득하려면 데이터나 사례 들고 와야 함",
        ],
        hashtags="#ESTJ #MBTI #ESTJ고집 #MBTI분석",
    ),
    ESTJCard(
        title="ESTJ가 결정을 내릴 때",
        bullets=[
            "선택지 모두 정리해보고",
            "장단점 비교 후 결정",
            "결정 후엔 미련 없음",
            "남들 의견 듣되 최종은 본인이",
        ],
        hashtags="#ESTJ #MBTI #ESTJ특징 #결정MBTI",
    ),
    ESTJCard(
        title="ESTJ가 감동받을 때",
        bullets=[
            "티 안 내려 하지만 눈빛이 달라짐",
            "나중에 '그때 고마웠어' 라고 말함",
            "감동은 행동으로 돌려줌",
            "한 번 마음에 새기면 오래 기억함",
        ],
        hashtags="#ESTJ #MBTI #ESTJ감정 #MBTI공감",
    ),
    ESTJCard(
        title="ESTJ가 혼자 있을 때",
        bullets=[
            "생각 정리하는 시간으로 씀",
            "할 일 없으면 오히려 불안함",
            "취미든 공부든 뭔가를 함",
            "완전한 충전은 이틀 이상이어야 가능",
        ],
        hashtags="#ESTJ #MBTI #ESTJ혼자 #MBTI힐링",
    ),
    ESTJCard(
        title="ESTJ가 설명할 때",
        bullets=[
            "결론 → 이유 → 예시 순서로",
            "길게 설명 못 하면 답답함",
            "요점 없는 이야기엔 집중 힘듦",
            "명확하게 전달됐는지 확인함",
        ],
        hashtags="#ESTJ #MBTI #ESTJ소통 #MBTI대화",
    ),
    ESTJCard(
        title="ESTJ가 칭찬해줄 때",
        bullets=[
            "빈말 칭찬은 잘 안 함",
            "칭찬하면 진심임",
            "구체적으로 뭘 잘했는지 말함",
            "받는 사람은 가끔 부담스러울 수도",
        ],
        hashtags="#ESTJ #MBTI #ESTJ칭찬 #MBTI공감",
    ),
    ESTJCard(
        title="ESTJ가 팀원일 때",
        bullets=[
            "맡은 거 기한 안에 무조건 완료",
            "불명확한 지시엔 바로 질문",
            "팀 분위기보단 성과 중시",
            "인정받으면 더 열심히 함",
        ],
        hashtags="#ESTJ #MBTI #직장인MBTI #ESTJ직장",
    ),
    ESTJCard(
        title="ESTJ의 완벽주의",
        bullets=[
            "대충 하는 거 못 봄",
            "스스로 기준을 높게 잡음",
            "남에게 강요하진 않지만 내심 아쉬움",
            "완성도에 타협 없음",
        ],
        hashtags="#ESTJ #MBTI #ESTJ완벽주의 #MBTI특징",
    ),
]


def get_today() -> ESTJCard:
    idx = date.today().toordinal() % len(LIBRARY)
    return LIBRARY[idx]
