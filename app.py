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


def show_card(card):
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
st.title("T.O.DAY · 대구 청년과 기업을 잇는 AI 교생실습")
st.caption("기업이 평문으로 T.O를 내면 → AI가 역량을 분석하고 → 맞춤 강의를 만들고 → 졸업 준비생과 매칭합니다.")
tab0, tab1, tab2, tab3, tab4 = st.tabs(["⓪ 소개", "① T.O 게시판", "② 대구 역량 레이더", "③ AI 튜터", "④ 실습 매칭"])

# ---------------------------------------------------------------- ⓪ 소개
with tab0:
    st.subheader("서울에 있고 대구에 없는 건 일자리가 아니라 '연결의 밀도'다")
    intro_video = find_video("소개")
    if intro_video:
        st.video(intro_video)
    c1, c2, c3 = st.columns(3)
    c1.markdown("**① 기업이 T.O를 낸다**\n\n고민을 평문으로 쓰면 AI가 필요한 역량을 정리합니다.")
    c2.markdown("**② AI가 인재를 키운다**\n\n전공마다 다른 맞춤 강의를 AI가 만들고 가르칩니다.")
    c3.markdown("**③ 대구에서 만난다**\n\n기업 실전 실습과 거점시설 네트워크로 연결됩니다.")

# ---------------------------------------------------------------- ① T.O 게시판
with tab1:
    st.subheader("① 대구 기업들이 낸 T.O")
    if COMPANIES:
        board = pd.DataFrame([{
            "기업": c.get("기업명", ""), "찾는 인재": c.get("직무명", ""), "산업": c.get("산업", ""),
            "핵심 AI 역량": (c.get("필요_역량") or [{}])[0].get("역량", ""),
            "추천 전공": ", ".join(c.get("추천_전공", [])[:3]), "실습 요일": c.get("실습요일", "")}
            for c in all_cards()])
        st.dataframe(board, hide_index=True, width="stretch")
        st.caption("기업명은 시연용 가상 예시입니다.")
        pick = st.selectbox("자세히 볼 T.O", range(len(all_cards())), format_func=lambda i: card_label(all_cards()[i]))
        with st.expander("T.O 카드 보기", expanded=True):
            show_card(all_cards()[pick])

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
                    "너는 대구 중소기업의 고민을 'AI 교생실습 T.O 카드'로 바꾸는 전문가다. "
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
            show_card(st.session_state["last_card"])
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

# ---------------------------------------------------------------- ③ AI 튜터
with tab3:
    st.subheader("③ 전공과 목표 T.O에 맞춰 가르치는 대구형 AI 튜터")
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
        lecture_video = find_video("강의")
        if lecture_video:
            with st.expander("🎬 오늘의 강의 영상", expanded=True):
                st.video(lecture_video)
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
    st.subheader("④ T.O에 맞는 졸업 준비생을 AI가 추천합니다 (결정은 사람이)")
    cards = all_cards()
    if not cards:
        st.warning("기업목록.json 에 T.O가 없어요.")
    else:
        m_idx = st.selectbox("대상 T.O", range(len(cards)), format_func=lambda i: card_label(cards[i]), key="match_to")
        card = cards[m_idx]
        st.info(f"**{card.get('직무명', '')}** · 추천 전공: {', '.join(card.get('추천_전공', [])[:5])} · "
                f"실습 요일: {card.get('실습요일', '협의')}")
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
