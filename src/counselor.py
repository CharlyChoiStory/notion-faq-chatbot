"""
counselor.py
────────────
상담원 연결용 케이스 생성/조회 및 고객 맥락 분석 유틸리티.

주의: 이 모듈은 의료 진단을 하지 않고, 상담원이 빠르게 맥락을 파악하도록
고객 발화와 챗봇 답변을 안전한 상담 요약 형태로 정리한다.
"""

from __future__ import annotations

import json
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CASE_DIR = PROJECT_ROOT / "data" / "counselor_cases"

AREA_KEYWORDS = {
    # 보톡스/필러 같은 시술명은 '눈' 등 이전 대화 맥락보다 최신 질문에서 우선 판정한다.
    "피부/보톡스": ("보톡스", "필러", "스킨부스터", "레이저", "여드름", "색소", "피부"),
    "눈": ("눈", "쌍꺼풀", "쌍수", "눈매교정", "트임", "상안검", "하안검", "매몰", "절개"),
    "코": ("코", "콧대", "코끝", "콧볼", "휜코", "비중격", "코수술"),
    "리프팅": ("리프팅", "처짐", "탄력", "실리프팅", "안면거상"),
    "윤곽": ("윤곽", "턱", "광대", "사각턱", "이중턱"),
    "가슴": ("가슴", "유방", "가슴성형"),
}

CHANGE_KEYWORDS = {
    "자연스러운 인상 개선": ("자연", "티 안", "안 티", "과하지", "은은"),
    "또렷한 인상 개선": ("또렷", "선명", "크게", "눈이 커", "화려"),
    "어려 보이는 인상 개선": ("어려", "동안", "젊", "처짐", "탄력"),
    "기능/불편 개선 상담": ("숨", "호흡", "불편", "통증", "시야", "뜨기 힘"),
}

CONCERN_KEYWORDS = {
    "흉터": ("흉터", "상처"),
    "회복 기간": ("회복", "붓기", "부기", "멍", "일상", "출근"),
    "비용": ("비용", "가격", "얼마", "견적", "이벤트"),
    "부작용": ("부작용", "염증", "감염", "통증", "출혈", "피가", "고열"),
    "결과/자연스러움": ("결과", "자연", "전후", "연예인", "예쁘"),
    "마취/안전": ("마취", "수면", "안전", "무섭", "걱정"),
}

URGENT_KEYWORDS = (
    "심한 통증", "피가 계속", "출혈", "호흡곤란", "숨쉬기 힘", "숨 쉬기 힘",
    "고열", "시야", "감염", "염증", "괴사", "검게", "하얗게", "응급"
)

RESERVATION_KEYWORDS = ("예약", "상담", "이번 주", "오늘", "내일", "토요일", "일요일", "오전", "오후", "가능")
PREVIOUS_NO_KEYWORDS = ("없어요", "없습니다", "처음", "받은 적 없", "한 적 없")
PREVIOUS_YES_KEYWORDS = ("재수술", "전에", "이전", "받았", "했었", "필러 맞", "수술했")
PHOTO_KEYWORDS = ("사진", "셀카", "얼굴 사진", "사진 보고", "봐주")
MINOR_KEYWORDS = ("미성년", "부모님 몰래", "보호자")


def _contains_any(text: str, words: tuple[str, ...]) -> bool:
    return any(word in text for word in words)


def _first_match_label(text: str, mapping: dict[str, tuple[str, ...]], default: str = "확인 필요") -> str:
    for label, words in mapping.items():
        if _contains_any(text, words):
            return label
    return default


def detect_interest_area(question: str, full_context: str) -> str:
    """관심 부위는 최신 질문을 최우선으로 판정한다.

    이전 대화에 '눈/쌍수'가 있어도 최신 질문이 '보톡스 가격'이면
    상담원 페이지에는 '피부/보톡스'로 표시되어야 한다.
    """
    latest_area = _first_match_label(question, AREA_KEYWORDS)
    if latest_area != "확인 필요":
        return latest_area
    return _first_match_label(full_context, AREA_KEYWORDS)


def _all_match_labels(text: str, mapping: dict[str, tuple[str, ...]]) -> list[str]:
    return [label for label, words in mapping.items() if _contains_any(text, words)]


def extract_desired_schedule(text: str) -> str:
    patterns = [
        r"(이번\s*주\s*(?:월|화|수|목|금|토|일)요일?\s*(?:오전|오후|저녁|낮)?\s*\d*시?)",
        r"((?:오늘|내일|모레)\s*(?:오전|오후|저녁|낮)?\s*\d*시?)",
        r"((?:월|화|수|목|금|토|일)요일?\s*(?:오전|오후|저녁|낮)?\s*\d*시?)",
        r"(\d{1,2}월\s*\d{1,2}일\s*(?:오전|오후|저녁|낮)?\s*\d*시?)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()
    if _contains_any(text, RESERVATION_KEYWORDS):
        return "상담 희망 — 구체 일정 확인 필요"
    return "미확인"


def detect_previous_procedure(text: str) -> str:
    if _contains_any(text, PREVIOUS_NO_KEYWORDS):
        return "없음으로 추정"
    if _contains_any(text, PREVIOUS_YES_KEYWORDS):
        return "있음 가능성 — 부위/시기 확인 필요"
    return "미확인"


def determine_urgency(text: str, answer: str, sources: list[dict[str, Any]]) -> str:
    combined = f"{text}\n{answer}"
    if _contains_any(combined, URGENT_KEYWORDS):
        return "높음 — 부작용/응급 가능성, 즉시 상담실 또는 의료진 확인 필요"
    if _contains_any(combined, ("예약", "상담 예약", "상담실 연결", "원장", "가격 정확")):
        return "상담 예약 의향 높음"
    if any(s.get("medical_risk_level") in {"high", "medium"} for s in sources):
        return "중간 이상 — 상담원 확인 권장"
    return "일반 문의"


def determine_handoff_reason(text: str, answer: str, sources: list[dict[str, Any]]) -> str:
    combined = f"{text}\n{answer}"
    reasons = []
    if _contains_any(combined, URGENT_KEYWORDS):
        reasons.append("부작용/응급 의심 표현")
    if _contains_any(combined, PHOTO_KEYWORDS):
        reasons.append("사진 기반 판단 요청")
    if _contains_any(combined, MINOR_KEYWORDS):
        reasons.append("미성년자/보호자 동의 확인 필요")
    if _contains_any(combined, ("비용", "가격", "견적", "이벤트")):
        reasons.append("비용/견적 확인 필요")
    if _contains_any(combined, ("예약", "상담실", "상담원", "원장님", "연결")):
        reasons.append("상담/예약 연결 요청")
    if any(s.get("requires_human_review") for s in sources):
        reasons.append("자동 분류상 사람 검토 필요")
    return ", ".join(dict.fromkeys(reasons)) if reasons else "상담원 확인 권장"


def analyze_customer_context(
    question: str,
    answer: str = "",
    sources: list[dict[str, Any]] | None = None,
    chat_history: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    sources = sources or []
    history_text = "\n".join(item.get("content", "") for item in (chat_history or [])[-8:])
    text = f"{history_text}\n{question}".strip()

    interest_area = detect_interest_area(question, text)
    desired_change = _first_match_label(question, CHANGE_KEYWORDS)
    if desired_change == "확인 필요":
        desired_change = _first_match_label(text, CHANGE_KEYWORDS)
    concerns = _all_match_labels(f"{text}\n{question}", CONCERN_KEYWORDS)

    if not concerns and interest_area != "확인 필요":
        concerns = ["상담 방향 확인 필요"]
    elif not concerns:
        concerns = ["미확인"]

    high_risk_sources = [s for s in sources if s.get("medical_risk_level") in {"high", "medium"}]
    matched_faq = [s.get("question", "") for s in sources[:3] if s.get("question")]

    return {
        "고객 관심 부위": interest_area,
        "희망 변화": desired_change,
        "이전 시술": detect_previous_procedure(text),
        "걱정 요소": ", ".join(dict.fromkeys(concerns)),
        "희망 일정": extract_desired_schedule(text),
        "긴급도": determine_urgency(text, answer, sources),
        "상담 연결 사유": determine_handoff_reason(text, answer, sources),
        "원문 질문": question,
        "챗봇 답변 요약": answer[:600],
        "상담원 확인 포인트": build_next_actions(text, sources),
        "참고 FAQ": matched_faq,
        "위험도 메타": [
            {
                "question": s.get("question", ""),
                "medical_risk_level": s.get("medical_risk_level", "unknown"),
                "routing_action": s.get("routing_action", ""),
                "review_reason": s.get("review_reason", ""),
            }
            for s in high_risk_sources
        ],
    }


def build_next_actions(text: str, sources: list[dict[str, Any]]) -> list[str]:
    actions = []
    if _contains_any(text, URGENT_KEYWORDS):
        actions.append("증상 발생 시점, 수술/시술 날짜, 통증·출혈·열감 정도를 즉시 확인")
        actions.append("필요 시 의료진/응급 안내로 즉시 이관")
    if _contains_any(text, PHOTO_KEYWORDS):
        actions.append("사진은 진단이 아니라 상담 참고자료임을 재안내하고 개인정보 동의 확인")
    if _contains_any(text, ("비용", "가격", "견적", "이벤트")):
        actions.append("확정 가격 대신 부위·방법·재수술 여부 확인 후 상담 기준 안내")
    if _contains_any(text, RESERVATION_KEYWORDS):
        actions.append("이름, 연락처, 희망 날짜/시간대, 관심 부위 수집")
    if _contains_any(text, MINOR_KEYWORDS):
        actions.append("보호자 동의 및 필요 서류 확인")
    if any(s.get("requires_human_review") for s in sources):
        actions.append("자동 분류상 사람 검토가 필요한 항목이 있어 원문 확인")
    if not actions:
        actions.append("관심 부위, 희망 변화, 이전 수술/시술 여부, 걱정 요소를 추가 확인")
    return actions


def create_counselor_case(
    question: str,
    answer: str,
    sources: list[dict[str, Any]] | None = None,
    chat_history: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    CASE_DIR.mkdir(parents=True, exist_ok=True)
    case_id = datetime.now().strftime("%Y%m%d%H%M%S") + "-" + uuid.uuid4().hex[:8]
    analysis = analyze_customer_context(question, answer, sources, chat_history)
    payload = {
        "case_id": case_id,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "analysis": analysis,
        "chat_history": chat_history or [],
        "latest_question": question,
        "latest_answer": answer,
    }
    (CASE_DIR / f"{case_id}.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def load_counselor_case(case_id: str) -> dict[str, Any] | None:
    safe_case_id = re.sub(r"[^0-9A-Za-z_-]", "", case_id)
    path = CASE_DIR / f"{safe_case_id}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))
