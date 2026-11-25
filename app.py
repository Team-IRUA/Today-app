# -*- coding: utf-8 -*-
"""
T.O.DAY (티오데이) - 시연용 앱
기업이 T.O를 내는 날, AI가 인재를 키운다.

실행:  streamlit run app.py
"""
import json
import os
import re
from collections import Counter

import pandas as pd
import streamlit as st

HERE = os.path.dirname(os.path.abspath(__file__))
LOGO = os.path.join(HERE, "logo.png")
st.set_page_config(page_title="T.O.DAY", page_icon=LOGO if os.path.exists(LOGO) else "🎓", layout="wide")


# ---------------------------------------------------------------------------
# 메모장으로 고칠 수 있는 파일 읽기
# ---------------------------------------------------------------------------
def read_lines(filename):
    try:
        with open(os.path.join(HERE, filename), encoding="utf-8-sig") as f:
            return [ln.rstrip("\n") for ln in f]
    except OSError:
        return []


def load_list(filename, default):
    items = [ln.strip() for ln in read_lines(filename) if ln.strip() and not ln.strip().startswith("#")]
    return items or default


def load_major_groups(filename):
    """전공목록.txt 의 '# ── ○○계열' 제목을 읽어 전공 → 계열 표를 만든다."""
    groups, current = {}, "융합·기타"
    for ln in read_lines(filename):
        s = ln.strip()
        if not s:
            continue
        if s.startswith("#"):
            m = re.search(r"──\s*(.+?)계열", s)
            if m:
                current = m.group(1).strip()
            elif "융합" in s:
                current = "융합·기타"
            continue
        groups[s] = current
    return groups


COMPETENCIES = load_list("역량목록.txt", [
    "생성형AI 업무활용(문서·요약·보고서)", "데이터 분석·시각화", "업무 자동화(엑셀·RPA·노코드)",
    "AI 비전(이미지 검사·분류)", "챗봇·고객응대 AI", "AI 마케팅·콘텐츠 제작",
    "AI 개발(모델·API 연동)", "AI 활용 불필요"])
MAJORS = load_list("전공목록.txt", ["경영학", "기계공학", "화학", "간호학", "시각디자인", "컴퓨터공학", "기타"])
MAJOR_GROUP = load_major_groups("전공목록.txt")

try:
    with open(os.path.join(HERE, "기업목록.json"), encoding="utf-8-sig") as f:
        COMPANIES = json.load(f)
except (OSError, json.JSONDecodeError):
    COMPANIES = []

VIDEO_DIR = os.path.join(HERE, "영상")


def find_video(name):
    """영상 폴더에서 name.mp4/.mov/.webm 을 찾고, 없으면 영상링크.txt 의 '이름=주소' 줄을 찾는다."""
    for ext in (".mp4", ".mov", ".webm", ".MP4", ".MOV"):
        path = os.path.join(VIDEO_DIR, name + ext)
        if os.path.exists(path):
            return path
    try:
        with open(os.path.join(VIDEO_DIR, "영상링크.txt"), encoding="utf-8-sig") as f:
            for ln in f:
                if ln.strip().startswith(name + "=") and ln.split("=", 1)[1].strip():
                    return ln.split("=", 1)[1].strip()
    except OSError:
        pass
    return None


MODELS = {"Claude Sonnet 5.5 (정확)": "claude-sonnet-5-5",
          "Claude Haiku 5.5 (저렴·빠름)": "claude-haiku-5-5"}
AI_NOTICE = "ⓘ 이 결과는 AI가 생성했습니다. 최종 판단은 사람이 합니다."
DEMO_NOTICE = "ⓘ 데모 모드: 시연용 예시 결과입니다."

# ---------------------------------------------------------------------------
# 데모 모드용 지식 (전공 계열별 수업 소재, 역량별 실습 문장, 공고 분류 규칙)
# ---------------------------------------------------------------------------
GROUP_HINTS = {
    "인문": ("글을 읽고 핵심을 골라내는 힘이 이미 있어요", "긴 글을 세 줄로 줄일 때, 무엇을 남기고 무엇을 버리나요?"),
    "사회": ("사람과 숫자를 함께 읽는 데 익숙하죠", "매출이나 설문 결과를 볼 때 가장 먼저 무엇을 확인하나요?"),
    "교육": ("어려운 내용을 쉽게 풀어내는 게 강점이에요", "같은 내용을 초등학생과 어른에게 다르게 설명해 본 적 있나요?"),
    "공학": ("공정과 시스템을 구조로 보는 눈이 있죠", "기계나 공정에 문제가 생기기 전, 어떤 신호가 먼저 보일까요?"),
    "자연": ("실험 데이터에서 패턴을 찾는 데 익숙하죠", "실험값이 튀었을 때 그게 오류인지 발견인지 어떻게 판단했나요?"),
    "의약·보건": ("정확성이 생명인 기록을 다뤄 봤죠", "인수인계 때 절대 빠지면 안 되는 정보는 무엇이었나요?"),
    "예체능": ("보는 사람의 마음을 움직이는 감각이 있죠", "같은 제품도 어떤 사진과 문구일 때 더 사고 싶어지나요?"),
    "융합·기타": ("여러 분야를 잇는 시각이 강점이에요", "요즘 일상에서 AI를 써 본 순간이 있나요?"),
}
PRACTICE = {
    "생성형AI": "이 문서를 핵심 3줄로 요약하고, 빠진 정보가 있으면 표시해 줘",
    "데이터": "이 표에서 평균과 크게 다른 값을 찾고, 그 이유를 세 가지로 추측해 줘",
    "자동화": "매주 반복하는 이 엑셀 정리 작업을 단계별로 나누고, 자동화할 수 있는 단계를 표시해 줘",
    "비전": "불량 사진과 정상 사진의 차이를 설명하고, 사람이 쓸 분류 기준표를 만들어 줘",
    "챗봇": "자주 묻는 질문 5개에 대해 친절하고 정확한 답변 초안을 만들어 줘",
    "마케팅": "이 제품을 20대 고객에게 알리는 SNS 문구 3개를 서로 다른 말투로 만들어 줘",
    "개발": "이 API 응답을 받아 표로 정리하는 프로그램의 구조를 단계별로 설명해 줘",
}
RADAR_RULES = [  # (공고 속 단어들, 역량)
    (["불량", "검사", "이미지", "비전", "사진"], "AI 비전(이미지 검사·분류)"),
    (["문의", "응대", "CS", "상담", "고객"], "챗봇·고객응대 AI"),
    (["SNS", "콘텐츠", "상세페이지", "마케팅", "홍보", "디자인"], "AI 마케팅·콘텐츠 제작"),
    (["개발", "프로그래밍", "파이썬", "API", "서버"], "AI 개발(모델·API 연동)"),
    (["매크로", "자동화", "반복", "RPA"], "업무 자동화(엑셀·RPA·노코드)"),
    (["데이터", "분석", "불량률", "통계", "재고"], "데이터 분석·시각화"),
    (["문서", "보고서", "기록", "작성", "행정"], "생성형AI 업무활용(문서·요약·보고서)"),
]
INDUSTRY_RULES = [(["자동차", "부품"], "자동차부품 제조"), (["물류", "유통", "배송"], "유통·물류"),
                  (["병원", "요양", "의료", "의무"], "의료·돌봄"), (["화학", "소재"], "화학·소재"),
                  (["식품"], "식품 제조"), (["관광", "여행"], "관광·문화"), (["소프트웨어", "SW", "IT"], "소프트웨어"),
                  (["섬유", "원단", "패션"], "섬유·패션"), (["건설", "건축"], "건설"), (["기계", "금형"], "기계·금속")]
JOB_WORDS = ["품질관리", "고객지원", "사무행정", "원무", "생산관리", "마케팅", "개발", "디자인", "영업", "물류"]


def keyword_pick(text, rules, default):
    best, score = default, 0
    for words, label in rules:
        s = sum(text.count(w) for w in words)
        if s > score:
            best, score = label, s
    return best


def practice_for(comp):
    for key, sentence in PRACTICE.items():
        if key in comp:
            return sentence
    return PRACTICE["생성형AI"]


# ---------------------------------------------------------------------------
# 사이드바
# ---------------------------------------------------------------------------
with st.sidebar:
    if os.path.exists(LOGO):
        st.image(LOGO, width=110)
    else:
        st.title("🎓 T.O.DAY")
    st.caption("기업이 T.O를 내는 날, AI가 인재를 키운다")
    st.divider()
    api_key = st.text_input("Claude API 키", type="password",
                            value=os.environ.get("ANTHROPIC_API_KEY", ""),
                            help="console.anthropic.com 에서 발급. 비워 두면 데모 모드로 동작합니다.")
    MODEL = MODELS[st.selectbox("AI 모델", list(MODELS.keys()))]
    DEMO = not api_key.strip()
    if DEMO:
        st.warning("데모 모드: 시연용 예시 결과를 보여줍니다.")
    else:
        st.success("AI 모드: 실제 Claude가 답합니다.")
    st.divider()
    st.metric("등록된 기업 T.O", f"{len(COMPANIES)}건")
    st.metric("지원 전공", f"{len(MAJORS)}개")
    st.caption("팀 IRUA · 2026 대구 로컬 AI 그라운드 출품 시연용 · 기업·학생은 가상 예시")


# ---------------------------------------------------------------------------
# AI 호출
# ---------------------------------------------------------------------------
def call_claude(system, messages, max_tokens=1500):
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key.strip())
        resp = client.messages.create(model=MODEL, max_tokens=max_tokens, system=system, messages=messages)
        return "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")
    except Exception as e:
        st.error(f"AI 호출 중 문제가 생겼어요: {e}")
        return ""


def parse_json(text):
    if not text:
        return None
    m = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
    if m:
        text = m.group(1)
    starts = [i for i in (text.find("{"), text.find("[")) if i != -1]
    if not starts:
        return None
    end = max(text.rfind("}"), text.rfind("]"))
    try:
        return json.loads(text[min(starts):end + 1])
    except json.JSONDecodeError:
        return None


def all_cards():
    cards = list(COMPANIES)
    custom = st.session_state.get("custom_card")
    if custom:
        cards.append(custom)
    return cards


def card_label(c):
    return f"{c.get('기업명', '새 기업')} · {c.get('직무명', '')}"


# 생활비 비교용 기준값 (추정치, 출처는 화면에 표시). 숫자는 이 표만 고치면 앱 전체에 반영됩니다.
COST = {
    "서울_연봉_차이": 1000,      # 만원/년. KOSIS 2025 상용근로자 급여 기준 대구·서울 격차 약 1천만 원 이상(매일신문 2026.5.27)
    "세후_비율": 0.87,           # 4대보험·소득세를 단순 반영한 추정
    "월세_대구": 32,             # 만원. 국토부 실거래가 원룸 월세 중앙값(보증금 400만), 2025.12~2026.11
    "월세_서울": 71,             # 만원. 다방 서울 원룸 평균(보증금 1,000만), 2026.3
    "점심_대구": 0.75,           # 만원. 대구 칼국수 7천원대(참가격, 2026.3)
    "점심_서울": 1.0,            # 만원. 서울 칼국수 1만 38원(참가격, 2026.3)
    "통근_대구": 73.0,           # 분/일 왕복. 한국노동연구원(2019 기준)
    "통근_서울": 90.4,           # 분/일 왕복. 수도권 평균, 같은 자료
    "근속지원_월": 30,           # 만원. 청년일자리도약장려금 비수도권형 2년 최대 720만 원 ÷ 24개월
}
COST_SOURCES = ("출처: KOSIS·매일신문(임금), 국토교통부 실거래가·다방(월세), 한국소비자원 참가격(외식), "
                "한국노동연구원(통근), 고용노동부(도약장려금). 서로 기준이 다른 통계를 합친 **추정치**입니다.")

TRACK_INFO = {
    "약정": "🤝 **약정 트랙** · 기업은 실습 전 조건부 채용을, 학생은 수료 후 일정 기간 근무를 약속해요. "
           "정규직 채용 시 청년일자리도약장려금(기업 인건비 + 청년 근속지원)과 연계해 안내합니다.",
    "자유": "🧭 **자유 트랙** · 채용 의무가 없어요. 학생은 탐색하고, 기업은 부담 없이 처음 참여합니다. "
           "다른 지역을 선택해도 불이익은 없어요.",
}


def show_public_info(card):
    track = card.get("트랙", "자유")
    st.markdown(TRACK_INFO.get(track, TRACK_INFO["자유"]))
    badge = "✅ 검증된 기업 (정보 공개 완료)" if card.get("검증기업") else "⏳ 정보 공개 진행 중"
    rows = [
        ("신입 연봉", f"{card['신입_연봉']:,}만 원" if card.get("신입_연봉") else "미공개"),
        ("근무 시간", card.get("근무시간", "미공개")),
        ("실습비 (월)", f"{card['실습비']}만 원" if card.get("실습비") else "협의"),
        ("실습 업무 범위", card.get("업무범위", "실습계획서로 확정")),
        ("실습생 채용 제안 이력", card.get("채용이력", "첫 참여")),
        ("직원 수", f"{card['직원수']}명" if card.get("직원수") else "미공개"),
    ]
    st.markdown(f"**🔎 기업 공개 정보** · {badge}")
    st.dataframe(pd.DataFrame(rows, columns=["항목", "내용"]), hide_index=True, width="stretch")
    if card.get("직원수") and card["직원수"] < 5:
        st.caption("※ 고용보험 5인 미만 기업은 청년일자리도약장려금 대상이 아니에요. 자유 트랙·구청 지원사업을 안내합니다.")


def show_cost_compare(card, ctx):
    base = card.get("신입_연봉") or 3000
    with st.expander("💸 서울로 가면 한 달에 얼마나 더 남을까? (실제 차이 계산)"):
        st.caption("결과가 서울에 유리해도 그대로 보여 줍니다. 판단은 청년이 합니다.")
        c1, c2 = st.columns(2)
        with c1:
            dg = st.number_input("대구 연봉 (만원)", 1500, 15000, int(base), 100, key=f"dg_{ctx}")
            sl = st.number_input("서울 연봉 (만원)", 1500, 20000, int(base + COST["서울_연봉_차이"]), 100,
                                 key=f"sl_{ctx}", help="기본값: 대구 + 연 1,000만 원 (지역 평균 격차)")
        with c2:
            home = st.checkbox("대구에서는 본가에서 출퇴근", key=f"home_{ctx}")
            sub = st.checkbox("대구에서 근속지원금 받음 (도약장려금, 요건 충족 시)",
                              value=card.get("트랙") == "약정" and (card.get("직원수") or 5) >= 5, key=f"sub_{ctx}")
        def month(pay, rent, lunch, bonus):
            net = pay * COST["세후_비율"] / 12
            return round(net), rent, round(lunch * 20), bonus, round(net - rent - lunch * 20 + bonus)
        d = month(dg, 0 if home else COST["월세_대구"], COST["점심_대구"], COST["근속지원_월"] if sub else 0)
        s_ = month(sl, COST["월세_서울"], COST["점심_서울"], 0)
        table = pd.DataFrame({
            "항목 (만원/월)": ["세후 월급(추정)", "월세", "점심 20회", "근속지원금", "**남는 돈**"],
            "대구": list(d), "서울": list(s_)})
        st.dataframe(table, hide_index=True, width="stretch")
        gap = s_[-1] - d[-1]
        extra_h = (COST["통근_서울"] - COST["통근_대구"]) * 22 / 60
        if gap > 0:
            st.info(f"서울이 한 달에 약 **{gap}만 원** 더 남아요. 대신 출퇴근에 한 달 약 **{extra_h:.0f}시간**을 더 써요.")
        else:
            st.success(f"대구가 한 달에 약 **{-gap}만 원** 더 남아요. 출퇴근 시간도 한 달 약 **{extra_h:.0f}시간** 아껴요.")
        st.caption(COST_SOURCES)


def show_card(card, ctx="card"):
    st.markdown(f"### 📌 {card.get('직무명', '')}")
    st.write(f"**기업:** {card.get('기업명', '')}  ·  **산업:** {card.get('산업', '')}")
    st.write(f"**기업 고민:** {card.get('기업_고민_요약', '')}")
    st.write(f"**핵심 과제:** {card.get('핵심_과제', '')}")
    st.write(f"**실습:** {card.get('실습_기간', '')} ({card.get('실습요일', '요일 협의')})")
    st.write("**필요 역량**")
    st.dataframe(pd.DataFrame(card.get("필요_역량", [])), hide_index=True, width="stretch")
    st.write("**AI가 만든 맞춤 강의 구성** (업계공통 70% + 기업맞춤 30%)")
    st.dataframe(pd.DataFrame(card.get("강의_구성", [])), hide_index=True, width="stretch")
    st.write("**추천 전공:** " + ", ".join(card.get("추천_전공", [])))
    st.divider()
    show_public_info(card)
    show_cost_compare(card, ctx)


# ---------------------------------------------------------------------------
# 데모용 생성기
# ---------------------------------------------------------------------------
def demo_card_from_text(company, worry):
    comp = keyword_pick(worry, RADAR_RULES, "생성형AI 업무활용(문서·요약·보고서)")
    industry = keyword_pick(company + worry, INDUSTRY_RULES, "지역 중소기업")
    return {
        "기업명": company or "새 기업", "직무명": "AI 업무 혁신 실습생", "산업": industry,
        "기업_고민_요약": worry[:80] + ("…" if len(worry) > 80 else ""),
        "핵심_과제": f"기업의 고민을 '{comp}' 방식으로 개선하는 시범 도구 만들기",
        "필요_역량": [{"역량": comp, "수준": "실전", "구분": "업계공통"},
                   {"역량": "생성형AI 업무활용(문서·요약·보고서)", "수준": "입문", "구분": "업계공통"},
                   {"역량": "업무 자동화(엑셀·RPA·노코드)", "수준": "입문", "구분": "기업맞춤"}],
        "추천_전공": [], "추천_계열": [], "실습_기간": "4학년 2학기, 주 2~3일, 12주", "실습요일": "협의",
        "강의_구성": [{"주차": "1~3주", "내용": "생성형 AI 기초와 결과 검증", "구분": "업계공통"},
                  {"주차": "4~6주", "내용": f"{comp} 실습", "구분": "업계공통"},
                  {"주차": "7~8주", "내용": "이 기업 업무에 맞춘 시범 적용", "구분": "기업맞춤"}],
    }


def demo_tutor(name, major, card, turn):
    group = MAJOR_GROUP.get(major, "융합·기타")
    strength, question = GROUP_HINTS.get(group, GROUP_HINTS["융합·기타"])
    comps = [c.get("역량", "") for c in card.get("필요_역량", [])] or ["생성형AI 업무활용"]
    lessons = card.get("강의_구성", []) or [{"내용": "AI 기초"}]
    fit = major in card.get("추천_전공", []) or group in card.get("추천_계열", [])
    bridge = ("이 T.O는 마침 " + major + " 전공자를 찾고 있어요." if fit else
              major + " 전공은 이 T.O의 추천 전공은 아니지만, 그래서 오히려 다른 관점을 줄 수 있어요.")
    if turn == 0:
        return (f"반가워요, {name}님! {major} 전공이군요. {strength}.\n\n"
                f"이번 목표는 **{card.get('기업명', '')}**의 '{card.get('직무명', '')}'이에요. "
                f"이 기업은 \"{card.get('기업_고민_요약', '')}\"라는 고민이 있어요. {bridge}\n\n"
                f"먼저 하나 물어볼게요. **{question}** 이 감각이 오늘 수업의 출발점이에요.")
    if turn == 1:
        return (f"좋아요, 그 감각 그대로 AI에게 일을 맡겨 볼게요.\n\n"
                f"**오늘의 실습: {lessons[0].get('내용', '')}**\n\n"
                f"AI에게 이렇게 요청해 보세요.\n> \"{practice_for(comps[0])}\"\n\n"
                f"그리고 AI의 답에서 **사실과 다르거나 빠진 부분을 하나** 찾아서 알려 주세요. "
                f"AI를 쓰는 것보다 AI의 답을 검증하는 게 진짜 실력이에요.")
    if turn == 2:
        nxt = lessons[1].get("내용", "다음 단계") if len(lessons) > 1 else "기업 맞춤 실습"
        return (f"잘했어요, {name}님! 방금 한 건 **'{comps[0]}'** 역량이에요. "
                f"{card.get('기업명', '')} 같은 대구 기업이 실제로 찾는 능력이죠.\n\n"
                f"{major} 전공의 시각에 AI 활용이 더해지면, 이 기업의 과제 "
                f"'{card.get('핵심_과제', '')}'를 직접 해낼 수 있어요.\n\n"
                f"다음 시간에는 **{nxt}**을(를) 배워요.")
    return (f"좋은 질문이에요. 지금 단계에서는 '{comps[min(1, len(comps) - 1)]}'까지 연결해 보면 좋아요. "
            f"실습 결과물은 포트폴리오에 저장되고, {card.get('실습_기간', '')} 동안 "
            f"{card.get('기업명', '')}와 실제 과제로 이어집니다.")


def demo_match(card, students):
    level_score = {"거의 없음": 5, "가끔 써 봄": 12, "업무·과제에 자주 씀": 20}
    want_majors = card.get("추천_전공", [])
    want_groups = card.get("추천_계열", [])
    days = set(re.split(r"[·,\s/]+", card.get("실습요일", "")))
    keywords = re.findall(r"[가-힣A-Za-z]{2,}", card.get("직무명", "") + card.get("산업", "") + card.get("핵심_과제", ""))
    out = []
    for _, s in students.iterrows():
        major, name = str(s.get("전공", "")), str(s.get("이름", ""))
        group = MAJOR_GROUP.get(major, "융합·기타")
        score, why, need = 30, [], []
        if major in want_majors:
            score += 35
            why.append(f"{major} 전공이 이 T.O의 추천 전공")
        elif group in want_groups:
            score += 20
            why.append(f"{group}계열 전공으로 과제 맥락 이해 가능")
        else:
            need.append("과제 분야의 기초 이해 필요")
        lv = str(s.get("AI경험", ""))
        score += level_score.get(lv, 8)
        if lv == "거의 없음":
            need.append("공통 AI 기초 과정부터 시작")
        interest = str(s.get("관심분야", ""))
        if any(k in interest or interest[:2] in k for k in keywords if len(k) >= 2) or any(
                w in card.get("핵심_과제", "") + card.get("산업", "") for w in re.split(r"[·,\s]+", interest) if len(w) >= 2):
            score += 15
            why.append(f"관심분야({interest})가 과제와 맞음")
        sdays = set(re.split(r"[·,\s/]+", str(s.get("실습가능요일", ""))))
        if days and days != {"협의"} and days != {""}:
            if days & sdays:
                why.append(f"실습 요일 겹침({'·'.join(sorted(days & sdays))})")
            else:
                score -= 15
                need.append("실습 요일 조정 필요")
        out.append({"이름": name, "전공": major, "적합도": max(5, min(98, score)),
                    "추천이유": ", ".join(why) or "기본 요건 충족", "보완할점": ", ".join(need) or "특이사항 없음"})
    return sorted(out, key=lambda r: -r["적합도"])


# ---------------------------------------------------------------------------
# 화면
# ---------------------------------------------------------------------------
st.title("T.O.DAY · 대구 청년과 기업을 잇는 AI 맞춤 현장실습")
st.caption("기업이 평문으로 T.O를 내면 → AI가 역량을 분석하고 → 맞춤 강의를 만들고 → 졸업 준비생과 매칭합니다.")
tab0, tab1, tab2, tabL, tab3, tab4, tab5 = st.tabs(["⓪ 소개", "① T.O 게시판", "② 대구 역량 레이더", "③ 강의실", "④ AI 튜터", "⑤ 실습 매칭", "⑥ 지원금 체크"])

# ---------------------------------------------------------------- ⓪ 소개
with tab0:
    st.subheader("산단과 대학과 거점이 한 생활권에 있는데, 서로 이어지지 않는다")
    intro_video = find_video("소개")
    if intro_video:
        st.video(intro_video)
    st.markdown(
        "대구 북구 노원동 **제3산업단지**는 매출이 늘어도 사람을 구하지 못합니다. 산격동 **경북대학교** 학생들은 "
        "같은 북구의 회사를 모른 채 떠나고, 그 사이의 **도시재생·창업 거점시설**은 채울 프로그램이 부족합니다. "
        "청년 유출은 이 '연결의 실패'의 결과입니다.")
    c1, c2, c3 = st.columns(3)
    c1.markdown("**① 기업이 T.O를 낸다**\n\n고민을 평문으로 쓰면 AI가 필요한 역량을 정리합니다.")
    c2.markdown("**② AI가 인재를 키운다**\n\n4학년 1학기, 그 회사 맞춤 강의를 AI가 만들고 가르칩니다.")
    c3.markdown("**③ 대구에서 만난다**\n\n2학기 현장실습과 거점시설 프로그램으로 연결됩니다.")
    st.info("**대상:** 대구 전역의 대학 4학년(전공 무관)과 중소기업 · **1차 실증지:** 북구 산격동·노원동 생활권 "
            "(경북대학교 · 제3산업단지 · 경북대 혁신타운 도시재생 · 대구그린스타트업타운)")

    st.markdown("#### 🗓 거점시설 프로그램 (1차 실증 계획)")
    st.dataframe(pd.DataFrame([
        {"프로그램": "T.O 데이", "주기": "학기 1회 (2월·8월)", "장소(협의 예정)": "대구그린스타트업타운 교육실", "내용": "기업 5분 발표 + 학생 만남"},
        {"프로그램": "T.O 스터디", "주기": "주 1회", "장소(협의 예정)": "경북대 혁신타운 거점", "내용": "강의 복습·과제 질문"},
        {"프로그램": "멘토 데이", "주기": "월 1회", "장소(협의 예정)": "그린스타트업타운 코워킹", "내용": "AI 기업 현직자 멘토링"},
        {"프로그램": "성과 발표회", "주기": "연 1회 (12월)", "장소(협의 예정)": "제3산단 복합문화센터 등", "내용": "실습 프로젝트 발표·채용 연결"},
    ]), hide_index=True, width="stretch")

    st.markdown("#### 🧭 우리가 붙잡으려는 청년은 누구인가")
    st.dataframe(pd.DataFrame([
        {"청년": "서울이 좋아서 가는 청년", "T.O.DAY의 역할": "막지 않습니다. 대구 기업 경험은 남습니다."},
        {"청년": "남고 싶지만 갈 곳을 못 찾은 청년", "T.O.DAY의 역할": "졸업 전에 대구 기업을 직접 겪게 합니다. (핵심 대상)"},
        {"청년": "연봉 숫자만 보고 차이를 크게 느끼는 청년", "T.O.DAY의 역할": "생활비·근속지원까지 합친 실제 차이를 보여 줍니다."},
    ]), hide_index=True, width="stretch")
    st.caption("목표: 참여 청년 10명 중 6명이 대구에서 첫 직장을 갖는 것. 떠나는 것을 막지 않고, 남을 이유를 만듭니다.")

# ---------------------------------------------------------------- ① T.O 게시판
with tab1:
    st.subheader("① 대구 기업들이 낸 T.O")
    if COMPANIES:
        board = pd.DataFrame([{
            "기업": c.get("기업명", ""), "찾는 인재": c.get("직무명", ""), "산업": c.get("산업", ""),
            "핵심 AI 역량": (c.get("필요_역량") or [{}])[0].get("역량", ""),
            "추천 전공": ", ".join(c.get("추천_전공", [])[:3]), "실습 요일": c.get("실습요일", ""),
            "트랙": c.get("트랙", "자유"), "신입 연봉(만원)": c.get("신입_연봉", ""),
            "공개": "✅" if c.get("검증기업") else "⏳"}
            for c in all_cards()])
        st.dataframe(board, hide_index=True, width="stretch")
        st.caption("기업명은 시연용 가상 예시입니다.")
        pick = st.selectbox("자세히 볼 T.O", range(len(all_cards())), format_func=lambda i: card_label(all_cards()[i]))
        with st.expander("T.O 카드 보기", expanded=True):
            show_card(all_cards()[pick], ctx=f"board_{pick}")

    st.divider()
    st.subheader("새 T.O 내기: 고민을 평문으로 적으면 AI가 T.O 카드를 만듭니다")
    presets = ["직접 입력"] + [c.get("기업명", "") for c in COMPANIES]
    preset = st.selectbox("예시 기업 불러오기", range(len(presets)), format_func=lambda i: presets[i])
    base = COMPANIES[preset - 1] if preset > 0 else {}
    c1, c2 = st.columns(2)
    with c1:
        company = st.text_input("회사 업종", base.get("업종", ""), key=f"company_{preset}")
        worry = st.text_area("요즘 업무 고민 (편하게 적어 주세요)", base.get("고민원문", ""), height=140, key=f"worry_{preset}")
        go1 = st.button("AI로 T.O 카드 만들기", type="primary")
    with c2:
        if go1:
            if not worry.strip():
                st.warning("고민을 한 줄이라도 적어 주세요.")
            elif DEMO:
                card = dict(base) if base else demo_card_from_text(company, worry)
                st.session_state["custom_card"] = card if not base else st.session_state.get("custom_card")
                st.session_state["last_card"] = card
                st.rerun()
            else:
                system = (
                    "너는 대구 중소기업의 고민을 'AI 맞춤 현장실습 T.O 카드'로 바꾸는 전문가다. "
                    "반드시 JSON 하나만 출력한다. 키: 기업명, 직무명, 산업, 기업_고민_요약, 핵심_과제, "
                    "필요_역량(리스트: 역량, 수준[입문/실전/응용], 구분[업계공통/기업맞춤]), "
                    "추천_전공(리스트), 추천_계열(리스트), 실습_기간, 실습요일, 강의_구성(리스트: 주차, 내용, 구분). "
                    f"역량은 다음 중에서만 고른다: {COMPETENCIES}. 추천_전공은 다음 중에서 고른다: {MAJORS}. "
                    "추천_계열은 인문, 사회, 교육, 공학, 자연, 의약·보건, 예체능 중에서 고른다. "
                    "강의는 업계공통 약 70%, 기업맞춤 약 30%. 기업이 말하지 않은 사실은 지어내지 않는다.")
                with st.spinner("AI가 고민을 분석하는 중..."):
                    out = call_claude(system, [{"role": "user", "content": f"업종: {company}\n고민: {worry}"}])
                card = parse_json(out)
                if card:
                    card.setdefault("기업명", company)
                    st.session_state["custom_card"] = card
                    st.session_state["last_card"] = card
                    st.rerun()
                elif out:
                    st.warning("AI 답을 표로 바꾸지 못했어요. 원문을 보여드릴게요.")
                    st.write(out)
        if st.session_state.get("last_card"):
            show_card(st.session_state["last_card"], ctx="new")
            st.caption(DEMO_NOTICE if DEMO else AI_NOTICE)

# ---------------------------------------------------------------- ② 역량 레이더
with tab2:
    st.subheader("② 대구 채용공고를 AI가 읽고, 대구 기업이 원하는 AI 역량을 보여줍니다")
    st.caption("공고문을 붙여 넣으세요. 공고와 공고 사이는 '---' 한 줄로 나눕니다. 회사명은 지워도 됩니다.")
    default_text = "\n".join(read_lines("sample_postings.txt"))
    postings_text = st.text_area("채용공고 붙여넣기", value=default_text, height=220)
    if st.button("AI로 역량 분석하기", type="primary"):
        postings = [p.strip().lstrip("-").strip() for p in postings_text.split("\n---") if p.strip()]
        rows = []
        if DEMO:
            for i, p in enumerate(postings, 1):
                comp = keyword_pick(p, RADAR_RULES, "AI 활용 불필요")
                hit = next((w for words, lab in RADAR_RULES if lab == comp for w in words if w in p), "")
                rows.append({"공고번호": i, "산업": keyword_pick(p, INDUSTRY_RULES, "기타"),
                             "직무": next((w for w in JOB_WORDS if w in p), "일반"),
                             "AI역량": comp, "근거": f"'{hit}' 관련 업무" if hit else "-"})
        else:
            system = (
                "너는 채용공고를 분석해 필요한 AI 활용 역량을 분류하는 분석가다. "
                "각 공고마다 산업, 직무, AI역량, 근거를 뽑는다. "
                f"AI역량은 다음 목록 중 가장 가까운 하나만 고른다: {COMPETENCIES}. "
                "근거는 공고 원문의 표현을 짧게 쓴다. 공고에 없는 내용은 지어내지 않는다. "
                "반드시 JSON 리스트만 출력한다. 각 원소 키: 공고번호, 산업, 직무, AI역량, 근거.")
            prog = st.progress(0.0, text="AI가 공고를 읽는 중...")
            for i in range(0, len(postings), 10):
                body = "\n\n".join(f"[공고 {i + j + 1}]\n{p}" for j, p in enumerate(postings[i:i + 10]))
                part = parse_json(call_claude(system, [{"role": "user", "content": body}], max_tokens=3000)) or []
                rows.extend([part] if isinstance(part, dict) else part)
                prog.progress(min(1.0, (i + 10) / max(1, len(postings))), text="AI가 공고를 읽는 중...")
            prog.empty()
        if rows:
            df = pd.DataFrame(rows)
            df["사람판단"] = ""
            st.session_state["radar"] = df
    df = st.session_state.get("radar")
    if df is not None and len(df):
        st.write(f"**분석한 공고: {len(df)}건**")
        chart = pd.DataFrame({"공고 수": Counter(df["AI역량"])}).sort_values("공고 수", ascending=False)
        st.bar_chart(chart, horizontal=True)
        st.caption(DEMO_NOTICE + " (데모는 단어 규칙으로 분류합니다)" if DEMO else AI_NOTICE)
        st.markdown("#### 정확도 검증: 사람 판단과 비교")
        st.caption("'사람판단' 칸에 팀원이 직접 고른 역량을 넣으면 AI와 얼마나 일치하는지 계산합니다.")
        edited = st.data_editor(
            df, hide_index=True, width="stretch", key="radar_editor",
            column_config={"사람판단": st.column_config.SelectboxColumn("사람판단", options=COMPETENCIES)},
            disabled=["공고번호", "산업", "직무", "AI역량", "근거"])
        judged = edited[edited["사람판단"].astype(str).str.len() > 0]
        if len(judged):
            match = (judged["사람판단"] == judged["AI역량"]).mean() * 100
            st.metric("AI–사람 일치율", f"{match:.0f}%", help=f"사람이 판단한 {len(judged)}건 기준")
        st.download_button("결과 CSV 내려받기", edited.to_csv(index=False).encode("utf-8-sig"),
                           file_name="daegu_ai_radar.csv", mime="text/csv")


# ---------------------------------------------------------------- ③ 강의실
def week_list(card):
    """강의_구성의 '1~3주' 같은 구간을 주차별 수업으로 펼친다."""
    weeks = []
    for row in card.get("강의_구성", []):
        nums = [int(n) for n in re.findall(r"\d+", str(row.get("주차", "")))] or [len(weeks) + 1]
        lo, hi = nums[0], nums[-1]
        for i, w in enumerate(range(lo, hi + 1)):
            part = f" ({i + 1}/{hi - lo + 1})" if hi > lo else ""
            weeks.append({"주차": w, "제목": str(row.get("내용", "")) + part, "구분": row.get("구분", "업계공통")})
    return weeks


def lecture_links():
    """영상/강의목록.txt 의 '주차=주소' 줄을 읽는다. (예: 1=https://youtu.be/...)"""
    links = {}
    try:
        with open(os.path.join(VIDEO_DIR, "강의목록.txt"), encoding="utf-8-sig") as f:
            for ln in f:
                if "=" in ln and not ln.strip().startswith("#"):
                    k, v = ln.split("=", 1)
                    if k.strip().isdigit() and v.strip():
                        links[int(k.strip())] = v.strip()
    except OSError:
        pass
    return links


def demo_lesson(card, week):
    comps = [c.get("역량", "") for c in card.get("필요_역량", [])] or ["생성형AI 업무활용"]
    comp = comps[0] if week["구분"] == "업계공통" else comps[-1]
    company = card.get("기업명", "이 기업")
    if week["구분"] == "업계공통":
        example = f"예를 들어 {card.get('산업', '대구 제조업')} 회사에서는 이 기술로 반복 문서 작업 시간을 줄입니다."
    else:
        example = f"{company}의 실제 고민 \"{card.get('기업_고민_요약', '')}\"에 바로 적용해 봅니다."
    return (f"**핵심 개념** · 이번 주 주제는 '{week['제목']}'이고, 연결 역량은 **{comp}**예요.\n\n"
            f"**왜 필요할까** · {example}\n\n"
            f"**따라 하기** · AI에게 이렇게 요청해 보세요.\n> {practice_for(comp)}\n\n"
            "**검증 체크리스트** · ① 숫자·사실이 원자료와 맞나요? ② 빠진 항목은 없나요? ③ 회사 기밀을 넣지 않았나요?")


def demo_feedback(text, week):
    n = len(text.strip())
    good = "구체적인 사례를 넣은 점이 좋아요." if n > 80 else "핵심은 잡았어요. 사례를 한 줄 더 넣어 보세요."
    return (f"{good} 이번 주 주제 '{week['제목']}'와 연결해 보면, AI 결과를 그대로 쓰지 않고 "
            "**어디를 고쳤는지** 적는 습관이 중요해요. 다음 주에는 고친 이유를 한 문장으로 붙여 보세요.")


with tabL:
    st.subheader("③ 강의실: 4학년 1학기, 목표 기업에 맞춘 주차별 강의")
    cards = all_cards()
    if not cards:
        st.warning("기업목록.json 에 T.O가 없어요.")
    else:
        l1, l2 = st.columns([1, 2])
        with l1:
            l_idx = st.selectbox("수강할 T.O 과정", range(len(cards)), format_func=lambda i: card_label(cards[i]), key="lec_to")
            card = cards[l_idx]
            weeks = week_list(card)
            done_key = f"done_{card.get('기업명', '')}"
            done = st.session_state.setdefault(done_key, set())
            st.progress(len(done) / max(1, len(weeks)), text=f"진도 {len(done)}/{len(weeks)}주")
            st.dataframe(pd.DataFrame([{"주차": f"{w['주차']}주", "강의": w["제목"], "구분": w["구분"],
                                        "상태": "✅" if w["주차"] in done else "·"} for w in weeks]),
                         hide_index=True, width="stretch", height=min(420, 38 * (len(weeks) + 1)))
            common = sum(1 for w in weeks if w["구분"] == "업계공통")
            st.caption(f"업계공통 {common}주 · 기업맞춤 {len(weeks) - common}주 (목표 비율 70:30)")
        with l2:
            w_no = st.selectbox("이번 주 강의", [w["주차"] for w in weeks],
                                format_func=lambda n: f"{n}주차 · " + next(w["제목"] for w in weeks if w["주차"] == n),
                                key=f"lec_week_{l_idx}")
            week = next(w for w in weeks if w["주차"] == w_no)
            st.markdown(f"### {w_no}주차 · {week['제목']}")
            st.caption("🌐 업계공통 강의: 공개 강의 영상 + AI 해설" if week["구분"] == "업계공통"
                       else f"🏭 기업맞춤 강의: {card.get('기업명', '')} 업무 자료로 AI가 만든 텍스트 강의")
            video = lecture_links().get(w_no) or (find_video("강의") if week["구분"] == "업계공통" else None)
            if video:
                st.video(video)
                st.caption("공개 강의를 쓸 때는 강의명·저작자·라이선스를 함께 표시합니다. (예: K-MOOC, MIT OCW · CC BY-NC-SA)")
            lesson_key = f"lesson_{l_idx}_{w_no}"
            if lesson_key not in st.session_state:
                if DEMO:
                    st.session_state[lesson_key] = demo_lesson(card, week)
                elif st.button("AI로 이번 주 강의 만들기", key=f"mk_{lesson_key}"):
                    system = ("너는 대구 중소기업 맞춤 현장실습 강의를 만드는 교수 설계자다. 한국어로 600자 안팎, "
                              "'핵심 개념 / 왜 필요할까 / 따라 하기(AI 프롬프트 예시) / 검증 체크리스트' 네 부분으로 쓴다. "
                              "기업이 말하지 않은 사실이나 통계는 지어내지 않는다.")
                    body = f"T.O: {json.dumps(card, ensure_ascii=False)}\n이번 주: {week}"
                    with st.spinner("AI가 강의를 만드는 중..."):
                        st.session_state[lesson_key] = call_claude(system, [{"role": "user", "content": body}], max_tokens=1200)
            if st.session_state.get(lesson_key):
                with st.container(border=True):
                    st.markdown(st.session_state[lesson_key])
                st.caption(DEMO_NOTICE if DEMO else AI_NOTICE + " 기업맞춤 강의는 기업 확인 후 공개합니다.")

            st.markdown("**✍️ 이번 주 과제** · 위 '따라 하기'를 해 보고, AI 답에서 고친 부분을 적어 내세요.")
            hw = st.text_area("과제 제출", key=f"hw_{lesson_key}", height=100, label_visibility="collapsed")
            if st.button("제출하고 수강 완료", type="primary", key=f"sub_{lesson_key}"):
                if not hw.strip():
                    st.warning("한 줄이라도 적어 주세요.")
                else:
                    if DEMO:
                        fb = demo_feedback(hw, week)
                    else:
                        fb = call_claude("너는 친절한 실습 조교다. 학생 과제에 3~4문장으로 피드백한다. 칭찬 1개, 개선 1개.",
                                         [{"role": "user", "content": f"주제: {week['제목']}\n과제: {hw}"}], max_tokens=400)
                    done.add(w_no)
                    st.session_state[f"fb_{lesson_key}"] = fb
                    st.rerun()
            if st.session_state.get(f"fb_{lesson_key}"):
                st.success("수강 완료! 피드백: " + st.session_state[f"fb_{lesson_key}"])

            if weeks and len(done) == len(weeks):
                st.balloons()
                st.info(f"🎓 **1학기 과정 수료** · {card.get('기업명', '')} '{card.get('직무명', '')}' 맞춤 과정\n\n"
                        f"2학기 현장실습: {card.get('실습_기간', '')} ({card.get('실습요일', '협의')}) · "
                        f"트랙: {card.get('트랙', '자유')} · 다음 단계는 ⑤ 실습 매칭에서 확인하세요.")

# ---------------------------------------------------------------- ④ AI 튜터
with tab3:
    st.subheader("④ 전공과 목표 T.O에 맞춰 가르치는 대구형 AI 튜터")
    cards = all_cards()
    c1, c2 = st.columns([1, 2])
    with c1:
        name = st.text_input("이름", "하윤")
        default_major = MAJORS.index("화학") if "화학" in MAJORS else 0
        major = st.selectbox("전공", MAJORS, index=default_major)
        st.caption(f"계열: {MAJOR_GROUP.get(major, '융합·기타')}")
        level = st.radio("AI 사용 경험", ["거의 없음", "가끔 써 봄", "업무·과제에 자주 씀"], index=0)
        if cards:
            t_idx = st.selectbox("목표 T.O", range(len(cards)), format_func=lambda i: card_label(cards[i]), key="tutor_to")
            card = cards[t_idx]
            st.info(f"**{card.get('직무명', '')}**\n\n과제: {card.get('핵심_과제', '')}")
        else:
            card = {}
        profile = (name, major, card.get("직무명", ""))
        restart = st.button("대화 새로 시작")
        if st.session_state.get("chat_profile") != profile or restart:
            st.session_state["chat"] = []
            st.session_state["chat_profile"] = profile
    with c2:
        st.caption("주차별 강의와 과제는 ③ 강의실에서 듣고, 여기서는 튜터에게 질문해요.")
        for m in st.session_state.get("chat", []):
            with st.chat_message(m["role"]):
                st.write(m["content"])
        q = st.chat_input("튜터에게 질문하거나 '시작'이라고 입력하세요")
        if q:
            st.session_state["chat"].append({"role": "user", "content": q})
            with st.chat_message("user"):
                st.write(q)
            if DEMO:
                turn = sum(1 for m in st.session_state["chat"] if m["role"] == "assistant")
                answer = demo_tutor(name, major, card, turn)
            else:
                system = (
                    f"너는 대구 청년을 위한 AI 활용 튜터다. 학생 이름은 {name}, 전공은 {major}"
                    f"({MAJOR_GROUP.get(major, '')}계열), AI 경험은 '{level}'이다. "
                    f"목표는 대구 기업 T.O '{card.get('직무명', '')}'에 필요한 역량을 키우는 것이다. "
                    f"T.O 정보: {json.dumps(card, ensure_ascii=False)}. "
                    "규칙: 1) 정답을 바로 주지 말고 질문으로 스스로 생각하게 이끈다. "
                    "2) 예시는 학생의 전공 경험과 이 대구 기업의 과제에서 가져온다. "
                    "3) 한 번에 짧게(5~8문장) 답한다. 4) 모르는 통계나 실제 기업명은 지어내지 않는다. "
                    "5) AI 결과를 검증하는 습관을 강조한다. 6) 한국어로 친근하게 답한다.")
                with st.spinner("튜터가 생각하는 중..."):
                    answer = call_claude(system, st.session_state["chat"], max_tokens=800)
            if answer:
                st.session_state["chat"].append({"role": "assistant", "content": answer})
                with st.chat_message("assistant"):
                    st.write(answer)
                    st.caption(DEMO_NOTICE if DEMO else AI_NOTICE)

# ---------------------------------------------------------------- ④ 매칭
with tab4:
    st.subheader("⑤ T.O에 맞는 졸업 준비생을 AI가 추천합니다 (결정은 사람이)")
    cards = all_cards()
    if not cards:
        st.warning("기업목록.json 에 T.O가 없어요.")
    else:
        m_idx = st.selectbox("대상 T.O", range(len(cards)), format_func=lambda i: card_label(cards[i]), key="match_to")
        card = cards[m_idx]
        st.info(f"**{card.get('직무명', '')}** · 추천 전공: {', '.join(card.get('추천_전공', [])[:5])} · "
                f"실습 요일: {card.get('실습요일', '협의')} · 트랙: {card.get('트랙', '자유')}")
        if "students" not in st.session_state:
            path = os.path.join(HERE, "sample_students.csv")
            st.session_state["students"] = (pd.read_csv(path, encoding="utf-8-sig") if os.path.exists(path) else
                                            pd.DataFrame(columns=["이름", "전공", "AI경험", "관심분야", "실습가능요일"]))
        st.caption("학생은 가상 인물입니다. 성별·나이·출신학교는 AI 입력에 넣지 않습니다.")
        students = st.data_editor(st.session_state["students"], num_rows="dynamic",
                                  hide_index=True, width="stretch", key="stu_editor")
        if st.button("AI 추천 받기", type="primary"):
            if DEMO:
                result = demo_match(card, students)
            else:
                system = (
                    "너는 T.O(기업 실습 정원)에 맞는 학생을 추천하는 도우미다. 추천만 하고 결정은 사람이 한다. "
                    "성별·나이·출신학교는 고려하지 않는다. 전공 관련성, AI 경험, 관심분야, 실습 가능 요일만 본다. "
                    "반드시 JSON 리스트만 출력. 각 원소 키: 이름, 전공, 적합도(0~100 정수), 추천이유, 보완할점. 적합도 높은 순.")
                body = f"T.O 카드: {json.dumps(card, ensure_ascii=False)}\n\n학생 목록:\n{students.to_csv(index=False)}"
                with st.spinner("AI가 추천을 만드는 중..."):
                    result = parse_json(call_claude(system, [{"role": "user", "content": body}], max_tokens=2000))
            if result:
                st.session_state["match"] = result
                st.session_state["match_for"] = m_idx
        if st.session_state.get("match") and st.session_state.get("match_for") == m_idx:
            res = pd.DataFrame(st.session_state["match"])
            st.dataframe(res.head(5), hide_index=True, width="stretch",
                         column_config={"적합도": st.column_config.ProgressColumn("적합도", min_value=0, max_value=100, format="%d")})
            st.caption((DEMO_NOTICE if DEMO else AI_NOTICE) + " 상위 5명만 표시. 기업과 학생이 직접 선택합니다.")


# ---------------------------------------------------------------- ⑤ 지원금 체크
# 기준: 2026 청년일자리도약장려금(비수도권형) 공개 안내 요약. 매년 바뀌므로 고용24 공고로 다시 확인할 것.
SUBSIDY_INFO = {
    "이름": "청년일자리도약장려금 (2026, 비수도권형)",
    "기업": "청년을 정규직으로 채용하고 6개월 이상 고용을 유지하면 인건비 지원",
    "청년": "비수도권 참여기업에서 6개월 이상 근속하면 2년간 최대 720만 원 근속 지원",
    "신청": "채용일로부터 3개월 이내, 고용24에서 신청 (예산 소진 시 조기 마감)",
}

with tab5:
    st.subheader("⑥ 이 채용, 지원금 받을 수 있을까? (기업·청년 함께 확인)")
    st.caption(f"기준: {SUBSIDY_INFO['이름']} · 요건과 금액은 매년 바뀝니다. **최종 확인은 고용24**에서 하세요.")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**🏭 기업 정보**")
        region = st.selectbox("사업장 소재지", ["대구", "경북", "부산·울산·경남", "그 밖의 비수도권", "서울·경기·인천(수도권)"], key="sub_region")
        insured = st.number_input("고용보험 가입 직원 수", min_value=0, max_value=1000, value=8, step=1, key="sub_insured")
        regular = st.radio("채용 형태", ["정규직", "계약직·인턴"], horizontal=True, key="sub_regular")
    with c2:
        st.markdown("**🎓 청년 정보**")
        age = st.number_input("청년 나이 (만)", min_value=14, max_value=45, value=24, step=1, key="sub_age")
        hire_date = st.date_input("채용일 (예정일도 가능)", key="sub_hire")

    checks = [
        ("비수도권 사업장", region != "서울·경기·인천(수도권)", "수도권 기업은 청년 근속 지원이 없고 기업 지원 요건도 달라요."),
        ("고용보험 5인 이상", insured >= 5, "5인 미만 기업은 대상이 아니에요. T.O.DAY 자유 트랙과 구청 지원사업을 확인해 보세요."),
        ("정규직 채용", regular == "정규직", "정규직 채용이 기본 조건이에요. 정규직 전환을 전제로 한 채용은 운영기관에 상담하세요."),
        ("청년 나이 만 15~34세", 15 <= age <= 34, "청년 기준 나이를 벗어나요. 병역 기간 등 예외는 운영기관에 확인하세요."),
    ]
    ok_all = all(ok for _, ok, _ in checks)

    st.markdown("#### 자격 확인")
    for label, ok, why in checks:
        if ok:
            st.success(f"✅ {label}")
        else:
            st.error(f"❌ {label} — {why}")

    if ok_all:
        st.info("👉 **대상일 가능성이 높아요.** 기업은 인건비, 청년은 근속 지원금을 함께 받을 수 있어요. "
                "아래 날짜를 놓치지 마세요.")
    else:
        st.warning("👉 **이 조건으로는 대상이 아닐 수 있어요.** 빨간 항목을 확인하세요.")

    st.markdown("#### 놓치면 안 되는 날짜")
    h = pd.Timestamp(hire_date)
    today = pd.Timestamp.today().normalize()
    milestones = [
        ("📝 신청 마감 (채용 후 3개월)", h + pd.DateOffset(months=3), "기한을 넘기면 지원금을 받을 수 없어요."),
        ("🏁 6개월 고용 유지", h + pd.DateOffset(months=6), "6개월 미만 근속이면 기업·청년 모두 지원이 없어요."),
        ("💰 청년 근속 지원 기간 끝 (2년)", h + pd.DateOffset(years=2), "청년 근속 지원금은 2년에 걸쳐 나눠 지급돼요."),
    ]
    rows = []
    for name, d, note in milestones:
        left = (d - today).days
        dday = f"D-{left}" if left > 0 else ("D-DAY" if left == 0 else f"{-left}일 지남")
        rows.append({"할 일": name, "날짜": d.strftime("%Y.%m.%d"), "남은 날": dday, "주의": note})
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")

    with st.expander("제도 요약 보기"):
        for k in ["기업", "청년", "신청"]:
            st.markdown(f"- **{k}:** {SUBSIDY_INFO[k]}")
        st.caption("T.O.DAY는 지원금을 직접 주지 않습니다. 대상 여부와 일정을 안내해 신청을 놓치지 않게 돕습니다.")
