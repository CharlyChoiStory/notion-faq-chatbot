"""
app.py
──────
Streamlit 챗봇 UI — 카카오톡 스타일 디자인

실행 방법:
    streamlit run src/app.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
from rag_chain import generate_answer
from local_loader import save_uploaded_file, load_faq_from_files
from counselor import create_counselor_case, load_counselor_case
from datetime import datetime
from html import escape

# ── 페이지 설정 ───────────────────────────────────────────
st.set_page_config(
    page_title="성형외과 FAQ 챗봇",
    page_icon="💬",
    layout="centered",
)

# ── 카카오톡 스타일 CSS ───────────────────────────────────
st.markdown("""
<style>
    /* 전체 배경 — 카카오톡 채팅방 배경색 */
    .stApp {
        background-color: #b2c7d9;
    }

    /* 병원명 메인 타이틀 */
    .clinic-title {
        text-align: center;
        font-size: 34px;
        font-weight: 900;
        color: #1f2d3d;
        letter-spacing: -1px;
        margin: 10px 0 14px 0;
        text-shadow: 0 1px 1px rgba(255,255,255,0.55);
    }
    .clinic-title .accent {
        color: #3c1e1e;
    }

    /* 상단 헤더 바 — 카카오톡 네이게이션 바 */
    .chat-header {
        background-color: #3c1e1e;
        color: white;
        padding: 14px 20px;
        border-radius: 0px;
        display: flex;
        align-items: center;
        gap: 12px;
        margin: -1rem -1rem 1rem -1rem;
        box-shadow: 0 2px 6px rgba(0,0,0,0.3);
    }
    .chat-header .avatar {
        width: 40px;
        height: 40px;
        background-color: #ffe812;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 22px;
    }
    .chat-header .title {
        font-size: 17px;
        font-weight: bold;
        color: white;
    }
    .chat-header .subtitle {
        font-size: 12px;
        color: #aaaaaa;
    }

    /* 날짜 구분선 */
    .date-divider {
        text-align: center;
        margin: 16px 0;
        color: #5a7a8a;
        font-size: 12px;
        font-weight: 500;
    }
    .date-divider span {
        background-color: #9ab0c0;
        padding: 3px 12px;
        border-radius: 10px;
        color: #2c4a5a;
    }

    /* 봇 메시지 (왼쪽) — 흰색 말풍선 */
    .bot-row {
        display: flex;
        align-items: flex-start;
        gap: 8px;
        margin: 10px 4px;
        justify-content: flex-start;
    }
    .bot-avatar {
        width: 36px;
        height: 36px;
        background-color: #ffe812;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 18px;
        flex-shrink: 0;
        margin-top: 2px;
    }
    .bot-name {
        font-size: 11px;
        color: #3c4043;
        margin-bottom: 3px;
        font-weight: 600;
    }
    .bot-bubble {
        background-color: #ffffff;
        border-radius: 0px 16px 16px 16px;
        padding: 10px 14px;
        max-width: 72%;
        font-size: 14px;
        line-height: 1.6;
        color: #1a1a1a;
        box-shadow: 0 1px 2px rgba(0,0,0,0.12);
        word-break: keep-all;
    }

    /* 유저 메시지 (오른쪽) — 노란색 말풍선 */
    .user-row {
        display: flex;
        justify-content: flex-end;
        margin: 10px 4px;
    }
    .user-bubble {
        background-color: #ffe812;
        border-radius: 16px 0px 16px 16px;
        padding: 10px 14px;
        max-width: 72%;
        font-size: 14px;
        line-height: 1.6;
        color: #1a1a1a;
        box-shadow: 0 1px 2px rgba(0,0,0,0.12);
        word-break: keep-all;
    }

    /* 시간 표시 */
    .msg-time {
        font-size: 10px;
        color: #5a7a8a;
        align-self: flex-end;
        margin: 0 4px 2px 4px;
        white-space: nowrap;
    }

    /* 상담원 연결 링크 */
    .handoff-card {
        margin-top: 10px;
        padding: 10px 12px;
        border-radius: 12px;
        background-color: #fff7cc;
        border: 1px solid #f0d450;
        color: #1a1a1a;
        font-size: 13px;
        line-height: 1.5;
    }
    .handoff-card a {
        display: inline-block;
        margin-top: 6px;
        padding: 7px 10px;
        border-radius: 8px;
        background-color: #3c1e1e;
        color: #ffffff !important;
        text-decoration: none;
        font-weight: 800;
    }

    /* 출처/정책 메타 박스 */
    .source-tag {
        background-color: #f0f4f7;
        border-left: 3px solid #ffe812;
        padding: 6px 10px;
        border-radius: 0 8px 8px 0;
        font-size: 11px;
        color: #3c4043;
        margin-top: 6px;
    }
    .not-found-tag {
        background-color: #fff8e1;
        border-left: 3px solid #ffc107;
        padding: 6px 10px;
        border-radius: 0 8px 8px 0;
        font-size: 11px;
        color: #7a6000;
        margin-top: 6px;
    }

    /* 입력창 커스텀 — 터널/모바일에서도 클릭 가능하도록 최상위 레이어 보장 */
    .stChatInput,
    [data-testid="stChatInput"],
    [data-testid="stChatInput"] > div {
        background-color: #f0f2f5 !important;
        border-radius: 24px !important;
        position: relative !important;
        z-index: 9999 !important;
        pointer-events: auto !important;
    }
    .stChatInput textarea,
    [data-testid="stChatInput"] textarea,
    textarea[aria-label="Chat input"] {
        background-color: #ffffff !important;
        color: #1a1a1a !important;
        caret-color: #1a1a1a !important;
        pointer-events: auto !important;
        user-select: text !important;
        -webkit-user-select: text !important;
        opacity: 1 !important;
        min-height: 44px !important;
        font-size: 16px !important;
    }
    [data-testid="stChatInput"] button {
        pointer-events: auto !important;
        z-index: 10000 !important;
    }
    /* 커스텀 말풍선이 입력창 위를 덮지 않도록 안전장치 */
    .bot-row, .user-row, .bot-bubble, .user-bubble {
        position: relative;
        z-index: 1;
    }

    /* 사이드바 스타일 */
    [data-testid="stSidebar"] {
        background-color: #3c1e1e;
    }
    [data-testid="stSidebar"] * {
        color: #f7f7f7 !important;
    }
    [data-testid="stSidebar"] .stButton button {
        background-color: #ffe812;
        color: #1a1a1a !important;
        border: none;
        border-radius: 8px;
        font-weight: 800;
        text-shadow: none !important;
    }
    [data-testid="stSidebar"] .stButton button * {
        color: #1a1a1a !important;
        text-shadow: none !important;
    }
    [data-testid="stSidebar"] .stButton button:hover {
        background-color: #f5dc00;
    }

    /* 파일 업로더는 흰 배경 안에서 검정 글자로 강제 */
    [data-testid="stFileUploaderDropzone"] {
        background-color: #ffffff !important;
        border: 2px dashed #8a8a8a !important;
    }
    [data-testid="stFileUploaderDropzone"] * {
        color: #1a1a1a !important;
        text-shadow: none !important;
        opacity: 1 !important;
    }
    [data-testid="stFileUploaderDropzone"] button {
        background-color: #f2f2f2 !important;
        color: #1a1a1a !important;
        border: 1px solid #999999 !important;
    }

    /* Streamlit 기본 요소 숨기기 */
    [data-testid="stChatMessage"] {
        background: transparent !important;
        border: none !important;
        padding: 0 !important;
    }
    .stChatMessage > div {
        background: transparent !important;
    }

    /* 스피너 */
    .stSpinner {
        color: #ffe812 !important;
    }

    /* 스크롤바 */
    ::-webkit-scrollbar { width: 4px; }
    ::-webkit-scrollbar-track { background: #b2c7d9; }
    ::-webkit-scrollbar-thumb { background: #7a9ab0; border-radius: 4px; }
</style>
""", unsafe_allow_html=True)


# ── 헬퍼 함수 ────────────────────────────────────────────
def now_time() -> str:
    return datetime.now().strftime("%p %I:%M").replace("AM", "오전").replace("PM", "오후")

def today_str() -> str:
    now = datetime.now()
    weekdays = ["월", "화", "수", "목", "금", "토", "일"]
    wd = weekdays[now.weekday()]
    return now.strftime(f"%Y년 %m월 %d일 {wd}요일")


def to_html(text: str) -> str:
    """사용자/LLM 텍스트를 안전하게 HTML 말풍선 안에 넣는다."""
    return escape(text or "").replace("\n", "<br>")


def render_user_message_html(content: str, time_str: str) -> str:
    """사용자 말풍선 HTML. Streamlit Markdown 오인 방지를 위해 들여쓰기 없는 단일 구조로 만든다."""
    return (
        '<div class="user-row">'
        f'<div class="msg-time">{to_html(time_str)}</div>'
        f'<div class="user-bubble">{to_html(content)}</div>'
        '</div>'
    )


def render_bot_message_html(content: str, time_str: str, counselor_link: str = "") -> str:
    """봇 말풍선 HTML. 닫는 div가 텍스트로 새지 않도록 들여쓰기/개행을 최소화한다."""
    return (
        '<div class="bot-row">'
        '<div class="bot-avatar">🤖</div>'
        '<div>'
        '<div class="bot-name">성형외과 FAQ 도우미</div>'
        f'<div class="bot-bubble">{to_html(content)}{counselor_link_html(counselor_link)}</div>'
        '</div>'
        f'<div class="msg-time">{to_html(time_str)}</div>'
        '</div>'
    )


def counselor_link_html(link: str) -> str:
    if not link:
        return ""
    safe_link = escape(link, quote=True)
    # 주의: 앞쪽 공백/들여쓰기가 있으면 Streamlit Markdown이 코드블록으로 렌더링할 수 있다.
    return (
        '<div class="handoff-card">'
        '이 문의는 상담원이 이어서 확인하면 더 안전합니다.<br>'
        f'<a href="{safe_link}" target="_blank">상담원 연결 / 상담 요약 보기</a>'
        '</div>'
    )


def render_counselor_page(case_id: str):
    case = load_counselor_case(case_id)
    if not case:
        st.error("상담 케이스를 찾을 수 없습니다. 링크가 잘못되었거나 케이스 파일이 삭제되었을 수 있습니다.")
        st.stop()

    analysis = case.get("analysis", {})

    st.markdown("""
<style>
    .stApp { background: #eef4f8 !important; }
    .block-container { max-width: 1180px !important; padding-top: 2.2rem !important; }
    .counselor-hero {
        background: linear-gradient(135deg, #2d3e50 0%, #506b86 100%);
        color: white;
        padding: 24px 28px;
        border-radius: 22px;
        box-shadow: 0 12px 28px rgba(31, 45, 61, 0.18);
        margin-bottom: 22px;
    }
    .counselor-hero h1 { margin: 0 0 8px 0; font-size: 34px; line-height: 1.2; }
    .counselor-hero p { margin: 0; opacity: 0.88; font-size: 15px; }
    .summary-grid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 14px;
        margin: 16px 0 22px 0;
    }
    .summary-card {
        background: #ffffff;
        border: 1px solid #d8e3ec;
        border-radius: 16px;
        padding: 16px 18px;
        box-shadow: 0 4px 14px rgba(31, 45, 61, 0.08);
        min-height: 92px;
    }
    .summary-label {
        color: #687789;
        font-size: 13px;
        font-weight: 800;
        margin-bottom: 7px;
    }
    .summary-value {
        color: #17212b;
        font-size: 22px;
        line-height: 1.35;
        font-weight: 900;
        word-break: keep-all;
    }
    .summary-card.urgent { border-left: 7px solid #e74c3c; }
    .summary-card.reason { border-left: 7px solid #f1c40f; }
    .section-card {
        background: #ffffff;
        border: 1px solid #d8e3ec;
        border-radius: 18px;
        padding: 20px 22px;
        margin: 16px 0;
        box-shadow: 0 4px 14px rgba(31, 45, 61, 0.08);
    }
    .section-card h2 { margin: 0 0 14px 0; font-size: 24px; color: #17212b; }
    .question-box {
        background: #e8f2ff;
        border-left: 7px solid #3498db;
        color: #102033;
        font-size: 20px;
        font-weight: 800;
        line-height: 1.55;
        padding: 18px 20px;
        border-radius: 14px;
    }
    .answer-box {
        background: #f8fafc;
        border-left: 7px solid #95a5a6;
        color: #1f2d3d;
        font-size: 17px;
        line-height: 1.75;
        padding: 16px 18px;
        border-radius: 14px;
    }
    .action-list li {
        font-size: 18px;
        line-height: 1.75;
        margin-bottom: 8px;
        color: #17212b;
        font-weight: 650;
    }
    .risk-box {
        background: #fff7e6;
        border-left: 7px solid #f39c12;
        color: #3c2a00;
        padding: 14px 16px;
        border-radius: 14px;
        margin: 10px 0;
        font-size: 16px;
        line-height: 1.65;
    }
    .muted-note { color: #6b7886; font-size: 13px; margin-top: 18px; }
    @media (max-width: 850px) {
        .summary-grid { grid-template-columns: 1fr; }
        .counselor-hero h1 { font-size: 28px; }
        .summary-value { font-size: 20px; }
    }
</style>
""", unsafe_allow_html=True)

    def card(label: str, value: str, extra_class: str = "") -> str:
        return (
            f'<div class="summary-card {extra_class}">'
            f'<div class="summary-label">{to_html(label)}</div>'
            f'<div class="summary-value">{to_html(value or "미확인")}</div>'
            '</div>'
        )

    st.markdown(
        f"""
<div class="counselor-hero">
  <h1>👩‍💼 상담원 확인 페이지</h1>
  <p>케이스 ID: {to_html(case.get('case_id', ''))} · 생성시각: {to_html(case.get('created_at', ''))}</p>
</div>
""",
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="summary-grid">'
        + card("관심 부위", analysis.get("고객 관심 부위", "미확인"))
        + card("희망 변화", analysis.get("희망 변화", "미확인"))
        + card("이전 시술", analysis.get("이전 시술", "미확인"))
        + card("걱정 요소", analysis.get("걱정 요소", "미확인"))
        + card("희망 일정", analysis.get("희망 일정", "미확인"))
        + card("긴급도", analysis.get("긴급도", "미확인"), "urgent")
        + '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
<div class="section-card">
  <h2>상담 연결 사유</h2>
  <div class="summary-card reason" style="box-shadow:none; margin:0;">
    <div class="summary-value">{to_html(analysis.get('상담 연결 사유', '미확인'))}</div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    actions_html = "".join(f"<li>{to_html(action)}</li>" for action in analysis.get("상담원 확인 포인트", []))
    st.markdown(
        f"""
<div class="section-card">
  <h2>상담원이 먼저 확인할 것</h2>
  <ul class="action-list">{actions_html}</ul>
</div>
""",
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
<div class="section-card">
  <h2>고객 원문 질문</h2>
  <div class="question-box">{to_html(analysis.get('원문 질문', ''))}</div>
</div>
<div class="section-card">
  <h2>챗봇 답변</h2>
  <div class="answer-box">{to_html(analysis.get('챗봇 답변 요약', ''))}</div>
</div>
""",
        unsafe_allow_html=True,
    )

    if analysis.get("위험도 메타"):
        risk_html = ""
        for item in analysis["위험도 메타"]:
            risk_html += (
                '<div class="risk-box">'
                f'<b>FAQ:</b> {to_html(item.get("question", ""))}<br>'
                f'<b>위험도:</b> {to_html(item.get("medical_risk_level", "unknown"))}<br>'
                f'<b>대응:</b> {to_html(item.get("routing_action", ""))}<br>'
                f'<b>검토 사유:</b> {to_html(item.get("review_reason", ""))}'
                '</div>'
            )
        st.markdown(f'<div class="section-card"><h2>내부 위험도 참고</h2>{risk_html}</div>', unsafe_allow_html=True)

    if analysis.get("참고 FAQ"):
        faq_html = "".join(f"<li>{to_html(faq)}</li>" for faq in analysis["참고 FAQ"])
        st.markdown(
            f'<div class="section-card"><h2>참고 FAQ 후보</h2><ul class="action-list">{faq_html}</ul></div>',
            unsafe_allow_html=True,
        )

    st.markdown(
        '<div class="muted-note">이 페이지는 상담원 보조용 요약입니다. 최종 의료 판단은 의료진 상담을 통해 진행해야 합니다.</div>',
        unsafe_allow_html=True,
    )
    st.stop()



# ── 상담원 전용 페이지 라우팅 ───────────────────────────────
case_id_param = st.query_params.get("counselor_case")
if case_id_param:
    render_counselor_page(case_id_param)


# ── 병원명 메인 타이틀 ─────────────────────────────────────
st.markdown("""
<div class="clinic-title"><span class="accent">AI미인</span> 성형외과</div>
""", unsafe_allow_html=True)


# ── 채팅 헤더 (카카오톡 상단바) ───────────────────────────
st.markdown(f"""
<div class="chat-header">
    <div class="avatar">🤖</div>
    <div>
        <div class="title">성형외과 FAQ 도우미</div>
        <div class="subtitle">로컬 문서 업로드 기반 RAG 챗봇</div>
    </div>
</div>
""", unsafe_allow_html=True)


# ── 세션 상태 초기화 ──────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "initialized" not in st.session_state:
    st.session_state.initialized = False


# ── 사이드바 ──────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🏥 성형외과 FAQ")
    st.caption("문서를 업로드하면 자동으로 파싱·온톨로지 태깅·벡터 DB 구축까지 실행됩니다.")

    uploaded_files = st.file_uploader(
        "FAQ 지식베이스 파일 업로드",
        type=["md", "txt", "pdf", "docx"],
        accept_multiple_files=True,
        help="성형외과 FAQ 규정집처럼 FAQ-001 형식이면 Q/A 단위로 자동 파싱합니다.",
    )

    if uploaded_files:
        upload_signature = tuple((f.name, getattr(f, "size", len(f.getbuffer()))) for f in uploaded_files)
        if st.session_state.get("upload_signature") != upload_signature:
            with st.spinner("업로드 문서 자동 처리 중... 파싱 → 온톨로지 태깅 → 벡터 DB 구축"):
                try:
                    from embeddings import build_index
                    saved_paths = [save_uploaded_file(f) for f in uploaded_files]
                    faq_list = load_faq_from_files(saved_paths)
                    build_index(faq_list, reset=True)
                    st.session_state.upload_signature = upload_signature
                    st.session_state.indexed_count = len(faq_list)
                    st.session_state.indexed_sources = [p.name for p in saved_paths]
                    # 새 지식베이스가 올라오면 이전 대화는 혼동 방지를 위해 초기화
                    st.session_state.messages = []
                    st.session_state.chat_history = []
                    st.success(f"✅ 자동 구축 완료: {len(faq_list)}개 FAQ/문서 청크")
                except Exception as e:
                    st.error(f"❌ 자동 구축 오류: {e}")
        elif st.session_state.get("indexed_count"):
            st.success(f"✅ 준비 완료: {st.session_state.indexed_count}개 FAQ/문서 청크")

    if st.session_state.get("indexed_count"):
        st.caption("소스: " + ", ".join(st.session_state.get("indexed_sources", [])))

    st.markdown("---")
    st.markdown("**예시 질문**")
    st.markdown("• 상담 예약은 어떻게 하나요?")
    st.markdown("• 수술 전 주의사항 알려주세요")
    st.markdown("• 붓기와 멍은 언제 빠지나요?")
    st.markdown("• 비용은 얼마인가요?")
    st.markdown("• 수술 후 피가 나면 어떻게 해야 하나요?")


# ── 날짜 구분선 ───────────────────────────────────────────
st.markdown(f"""
<div class="date-divider">
    <span>{today_str()}</span>
</div>
""", unsafe_allow_html=True)


# ── 첫 인사 메시지 ────────────────────────────────────────
if not st.session_state.messages:
    st.markdown("""
<div class="bot-row">
    <div class="bot-avatar">🤖</div>
    <div>
        <div class="bot-name">성형외과 FAQ 도우미</div>
        <div class="bot-bubble">
            안녕하세요! 👋<br>
            저는 <b>성형외과 FAQ 도우미</b>입니다.<br>
            왼쪽 사이드바에 FAQ 문서를 업로드하면 자동으로 지식베이스가 구축됩니다. 그 뒤 질문해 주세요 😊<br><br>
            <b>주의:</b> 진단, 처방, 수술 가능 여부, 부작용 판단은 의료진 확인이 필요한 내용입니다.
        </div>
    </div>
</div>
""", unsafe_allow_html=True)


# ── 이전 대화 렌더링 ──────────────────────────────────────
for msg in st.session_state.messages:
    time_str = msg.get("time", "")

    if msg["role"] == "user":
        st.markdown(render_user_message_html(msg["content"], time_str), unsafe_allow_html=True)

    else:
        st.markdown(
            render_bot_message_html(msg["content"], time_str, msg.get("counselor_link", "")),
            unsafe_allow_html=True,
        )


# ── 사용자 입력 ───────────────────────────────────────────
if user_input := st.chat_input("메시지를 입력하세요..."):
    time_str = now_time()

    # 유저 말풍선 바로 표시
    st.markdown(render_user_message_html(user_input, time_str), unsafe_allow_html=True)

    st.session_state.messages.append({
        "role": "user",
        "content": user_input,
        "time": time_str,
    })

    # 봇 답변 생성
    with st.spinner(""):
        try:
            result = generate_answer(
                query=user_input,
                chat_history=st.session_state.chat_history,
            )
            answer = result["answer"]
            sources = result["sources"]
            bot_time = now_time()
            counselor_link = ""
            if result.get("needs_handoff"):
                case = create_counselor_case(
                    question=user_input,
                    answer=answer,
                    sources=sources,
                    chat_history=st.session_state.chat_history,
                )
                counselor_link = f"?counselor_case={case['case_id']}"

            # 봇 말풍선 표시
            st.markdown(render_bot_message_html(answer, bot_time, counselor_link), unsafe_allow_html=True)

            # 세션 저장
            st.session_state.messages.append({
                "role": "assistant",
                "content": answer,
                "sources": sources,
                "counselor_link": counselor_link,
                "time": bot_time,
            })
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            st.session_state.chat_history.append({"role": "assistant", "content": answer})

        except Exception as e:
            error_msg = f"❌ 오류: {str(e)}"
            st.markdown(f"""
<div class="bot-row">
    <div class="bot-avatar">🤖</div>
    <div>
        <div class="bot-name">성형외과 FAQ 도우미</div>
        <div class="bot-bubble" style="color:red;">{error_msg}</div>
    </div>
</div>
""", unsafe_allow_html=True)
            st.session_state.messages.append({
                "role": "assistant",
                "content": error_msg,
                "sources": [],
                "time": now_time(),
            })
