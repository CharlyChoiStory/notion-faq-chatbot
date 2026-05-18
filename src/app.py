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
from datetime import datetime

# ── Streamlit Cloud Secrets → 환경변수 자동 주입 ─────────────
try:
    for _k, _v in st.secrets.items():
        if _k not in os.environ:
            os.environ[_k] = str(_v)
except Exception:
    pass

# ── 서버 시작 시 샘플 FAQ 자동 인덱싱 (ChromaDB가 비어 있을 때) ──
@st.cache_resource(show_spinner="FAQ 지식베이스 초기 구축 중...")
def _auto_index_samples():
    """배포 환경에서 ChromaDB가 비어 있으면 samples/ 폴더로 자동 인덱싱한다."""
    try:
        from embeddings import get_chroma_collection, build_index
        collection = get_chroma_collection()
        if collection.count() > 0:
            return collection.count()
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sample_files = [
            os.path.join(base, "samples", "1.sample-faq-db.md"),
            os.path.join(base, "samples", "3.plastic_surgery_harness_build_data.md"),
        ]
        existing = [f for f in sample_files if os.path.exists(f)]
        if not existing:
            return 0
        faq_list = load_faq_from_files(existing)
        build_index(faq_list, reset=False)
        return len(faq_list)
    except Exception:
        return 0

_auto_index_samples()

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

    /* 입력창 커스텀 */
    .stChatInput {
        background-color: #f0f2f5 !important;
        border-radius: 24px !important;
    }
    .stChatInput textarea {
        background-color: #f0f2f5 !important;
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


# ── 병원 배너 이미지 ──────────────────────────────────────
_banner_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "banner.jpg")
if os.path.exists(_banner_path):
    st.image(_banner_path, use_container_width=True)

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
        st.markdown(f"""
<div class="user-row">
    <div class="msg-time">{time_str}</div>
    <div class="user-bubble">{msg["content"]}</div>
</div>
""", unsafe_allow_html=True)

    else:
        st.markdown(f"""
<div class="bot-row">
    <div class="bot-avatar">🤖</div>
    <div>
        <div class="bot-name">성형외과 FAQ 도우미</div>
        <div class="bot-bubble">
            {msg["content"]}
        </div>
    </div>
    <div class="msg-time">{time_str}</div>
</div>
""", unsafe_allow_html=True)


# ── 사용자 입력 ───────────────────────────────────────────
if user_input := st.chat_input("메시지를 입력하세요..."):
    time_str = now_time()

    # 유저 말풍선 바로 표시
    st.markdown(f"""
<div class="user-row">
    <div class="msg-time">{time_str}</div>
    <div class="user-bubble">{user_input}</div>
</div>
""", unsafe_allow_html=True)

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

            # 봇 말풍선 표시
            st.markdown(f"""
<div class="bot-row">
    <div class="bot-avatar">🤖</div>
    <div>
        <div class="bot-name">성형외과 FAQ 도우미</div>
        <div class="bot-bubble">
            {answer}
        </div>
    </div>
    <div class="msg-time">{bot_time}</div>
</div>
""", unsafe_allow_html=True)

            # 세션 저장
            st.session_state.messages.append({
                "role": "assistant",
                "content": answer,
                "sources": sources,
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
