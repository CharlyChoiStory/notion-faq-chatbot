"""
rag_chain.py
────────────
RAG 핵심 로직: 검색 → 프롬프트 구성 → OpenAI ChatGPT 답변 생성

Phase 1: 로컬 문서 업로드 + 벡터 검색 + ChatGPT 답변
Phase 2: Hybrid Search + Multi-Query (TODO)
Phase 3: Re-ranking + Parent-Child (TODO)
"""

import os
import re
from openai import OpenAI
from dotenv import load_dotenv
from embeddings import search_faq
from ontology import ontology_context_for_prompt

load_dotenv()

# ── OpenAI 설정 ─────────────────────────────────────
MODEL = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")


def get_openai_client() -> OpenAI:
    """OpenAI 클라이언트를 지연 생성한다. 앱은 API 키 없이도 먼저 열릴 수 있어야 한다."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY가 설정되어 있지 않습니다. .env 파일에 OpenAI API Key를 입력해 주세요.")
    return OpenAI(api_key=api_key)

# ── 유사도 임계값: 이 값 이하면 "모른다"고 답변 ────────────
SIMILARITY_THRESHOLD = 0.4


def build_system_prompt() -> str:
    """시스템 프롬프트를 반환합니다."""
    return """당신은 성형외과 FAQ 안내를 돕는 친절하고 정확한 AI 상담 코디네이터입니다.

핵심 정체성:
- 당신은 AI 의사가 아니라 AI 상담 코디네이터입니다.
- 진단하지 말고 분류하세요.
- 추천하지 말고 문진하세요.
- 과장하지 말고 기대치를 조정하세요.
- 상담원을 대체하지 말고 상담원이 더 잘 응대할 수 있도록 연결하세요.

규칙:
1. 제공된 FAQ 컨텍스트를 기반으로만 답변하세요.
2. FAQ에 직접적인 내용이 부족해도 고객에게 "FAQ에서 찾을 수 없습니다"라고 말하지 마세요. 대신 일반적인 안내 가능 범위와 상담 시 확인할 항목을 부드럽게 안내하세요.
3. 답변은 간결하고 친절하게 한국어로 작성하세요.
4. 추측하거나 없는 정보를 만들어내지 마세요.
5. 진단, 처방, 수술 가능 여부, 사진 기반 진단, 특정 수술법 추천, 부작용 판단, 결과 보장은 하지 마세요.
6. "확실히", "100%", "무조건", "부작용 없습니다", "흉터 안 남습니다", "사진상 가능" 같은 표현을 쓰지 마세요.
7. 심한 통증, 지속적인 출혈, 호흡곤란, 고열, 감염 의심, 갑작스러운 시야 이상 등은 즉시 병원 상담실/의료진 또는 응급실 문의를 안내하세요.
8. 비용/가격/견적 문의에는 금액, 가격 범위, 이벤트가를 절대 표시하지 마세요. 수술 방법, 난이도, 재수술 여부, 개인 상태에 따라 달라질 수 있어 상담원 연결 또는 예약 후 안내된다고만 말하세요.
9. 사진은 진단용이 아니라 상담 참고자료로만 활용될 수 있다고 안내하세요.
10. 미성년자, 환불/분쟁, 수술 후 이상 증상, 약 복용/질환/임신, 마취 관련 질문은 상담실 또는 의료진 확인으로 연결하세요.
11. 답변 말미에는 상황에 맞게 상담실 연결 또는 상담 예약을 자연스럽게 제안하세요.
"""


def build_user_prompt(query: str, retrieved_docs: list[dict]) -> str:
    """검색 결과를 포함한 사용자 프롬프트를 구성합니다."""
    if not retrieved_docs:
        context = "직접 일치하는 FAQ 문서는 없습니다. 고객에게 이 문구를 그대로 노출하지 말고, 안전한 일반 안내와 필요한 확인 항목을 안내하세요."
    else:
        context_lines = []
        for i, doc in enumerate(retrieved_docs, 1):
            context_lines.append(
                f"[FAQ {i}]\n"
                f"질문: {doc['question']}\n"
                f"답변: {doc['answer']}\n"
                f"정책유형: {doc.get('ontology_label', '미분류')}\n"
                f"정책조건: 단계={doc.get('policy_stage', 'unknown')}, "
                f"대상={doc.get('policy_target', 'unknown')}, "
                f"기간={doc.get('policy_period', 'unknown')}\n"
                f"의료위험도: {doc.get('medical_risk_level', 'unknown')}\n"
                f"라우팅대응: {doc.get('routing_action', '') or '기본 FAQ 답변'}\n"
                f"권장응답: {doc.get('recommended_response', '') or '없음'}\n"
                f"금지응답: {doc.get('forbidden_response', '') or '없음'}\n"
                f"사람검토필요: {doc.get('requires_human_review', False)}\n"
                f"(유사도: {doc['score']:.2f})"
            )
        context = "\n\n".join(context_lines)

    ontology_context = ontology_context_for_prompt(retrieved_docs) if retrieved_docs else "정책 메타데이터 없음"

    return f"""다음 FAQ 정보를 참고하여 사용자 질문에 답변해주세요.

=== 참고 FAQ ===
{context}
================

=== 온톨로지/정책 메타데이터 ===
{ontology_context}
================================

사용자 질문: {query}

답변 시 주의:
- 성형외과 FAQ 특성상 진단, 처방, 수술 가능 여부, 부작용 판단, 결과 보장은 하지 마세요.
- 응급 의심 표현이 있으면 병원 또는 응급실 연락을 우선 안내하세요.
- 의료위험도=high 또는 라우팅대응이 있으면, 일반 안내보다 즉시 병원 연락/응급 안내를 우선하세요.
- 금지응답에 포함된 표현 방향은 사용하지 마세요.
- 권장응답이 있으면 그 취지를 우선 반영하세요.
- FAQ 원문에 없는 정책은 만들지 마세요.
- 정책유형/단계/기간이 unknown이거나 사람검토필요=True이면 단정하지 말고 확인 필요하다고 말하세요.
- 비용/가격/견적 문의라면 FAQ에 금액이나 범위가 있어도 금액을 절대 표시하지 말고, 상담원 연결/예약을 통해 안내된다고 답하세요.
- 사용자에게 내부 정책유형, 단계명, 기간값, 유사도, 출처 메타데이터, '참조 기준' 문구는 표시하지 마세요.

위 FAQ를 바탕으로 정확하고 친절하게 답변해주세요."""


def clean_public_answer(answer: str) -> str:
    """사용자 화면에 노출하면 안 되는 내부 참조/메타데이터/RAG 실패 문구를 제거한다."""
    cleaned_lines = []
    for line in answer.splitlines():
        stripped = line.strip()
        if stripped.startswith("참조 기준"):
            continue
        if stripped.startswith("정책유형="):
            continue
        cleaned_lines.append(line)
    cleaned = "\n".join(cleaned_lines).strip()
    blocked_phrases = (
        "죄송합니다, 해당 내용은 FAQ에서 찾을 수 없습니다.",
        "해당 내용은 FAQ에서 찾을 수 없습니다.",
        "FAQ에서 찾을 수 없습니다.",
        "업로드된 FAQ에서 해당 질문과 직접 관련된 내용을 찾지 못했습니다.",
    )
    for phrase in blocked_phrases:
        cleaned = cleaned.replace(phrase, "문의하신 내용에 대해 기본적인 범위에서 안내드리겠습니다.")
    return cleaned.strip()


PRICE_QUERY_PATTERN = re.compile(r"(비용|가격|얼마|견적|수술비|시술비|이벤트|할인|금액)")
PRICE_VALUE_PATTERN = re.compile(r"(\d+[\s,]*(?:만\s*)?원|\d+\s*[~\-–]\s*\d+|\d+\s*만원|₩|KRW)")
EXPLICIT_HANDOFF_PATTERN = re.compile(
    r"(상담원\s*연결|사람\s*연결|전화\s*주세요|전화\s*상담|예약하고|예약\s*잡|원장님\s*상담|오늘\s*바로|이번\s*주.*예약|정확한\s*비용|정확한\s*가격|견적)"
)
MEDICAL_HANDOFF_PATTERN = re.compile(
    r"(부작용|심한\s*통증|피가\s*계속|출혈|호흡곤란|숨\s*쉬기\s*힘|고열|시야\s*이상|감염|염증|미성년|보호자|환불|분쟁|사진\s*보고|가능\s*여부|수술\s*가능|마취|임신|약\s*복용|질환)"
)
GENERAL_INFO_PATTERN = re.compile(r"(주차|주차장|위치|주소|진료시간|영업시간|휴진|오시는\s*길|지하철)")
BOTOX_PATTERN = re.compile(r"(보톡스|필러|스킨부스터)")


def is_price_query(query: str) -> bool:
    """가격/견적 문의인지 판정한다."""
    return bool(PRICE_QUERY_PATTERN.search(query or ""))


def build_price_handoff_answer(query: str) -> str:
    """가격 문의에는 금액을 표시하지 않고 상담원 연결을 유도한다."""
    return (
        "비용은 수술/시술 방법, 난이도, 재수술 여부, 개인 상태, 상담 내용에 따라 달라질 수 있어 "
        "챗봇에서 금액을 바로 안내드리기는 어렵습니다.\n\n"
        "정확한 안내를 위해 상담원이 관심 부위와 희망 변화, 이전 수술/시술 여부를 확인한 뒤 "
        "상담 예약 또는 상담실 연결로 도와드리겠습니다."
    )


def remove_unneeded_handoff_sentence(answer: str, query: str) -> str:
    """일반 정보 문의에서 불필요한 상담실/연결 유도 문장을 제거한다."""
    if not GENERAL_INFO_PATTERN.search(query or ""):
        return answer or ""
    sentences = re.split(r"(?<=[.!?。！？요다])\s+", answer or "")
    filtered = []
    for sentence in sentences:
        if re.search(r"(상담실|상담원).*(연결|문의|확인)", sentence):
            continue
        if re.search(r"더\s*궁금한\s*점.*(상담|문의|연결)", sentence):
            continue
        filtered.append(sentence)
    return " ".join(s.strip() for s in filtered if s.strip()).strip()


def remove_price_values(answer: str) -> str:
    """방어적으로 답변 안의 금액 표현을 제거한다."""
    return PRICE_VALUE_PATTERN.sub("[상담 후 안내]", answer or "")


def should_offer_counselor_link(query: str, answer: str, retrieved_docs: list[dict]) -> bool:
    """답변 하단에 상담원 연결 링크를 노출할지 판정한다.

    일반 정보 문의(주차/위치/진료시간)는 답변 안에 '문의'나 '상담실' 단어가 있어도
    상담원 링크를 붙이지 않는다. 링크는 실제 전환/위험/민감 문의에만 붙인다.
    """
    query = query or ""
    if GENERAL_INFO_PATTERN.search(query):
        return False
    if is_price_query(query) or EXPLICIT_HANDOFF_PATTERN.search(query) or MEDICAL_HANDOFF_PATTERN.search(query):
        return True
    for doc in retrieved_docs:
        if doc.get("medical_risk_level") == "high":
            return True
        routing = doc.get("routing_action", "")
        if routing and MEDICAL_HANDOFF_PATTERN.search(routing):
            return True
    return False


def docs_contain_keyword(retrieved_docs: list[dict], pattern: re.Pattern) -> bool:
    """검색 문서의 질문/답변/태그에 해당 키워드군이 실제로 포함되는지 확인한다."""
    for doc in retrieved_docs:
        haystack = " ".join(
            str(doc.get(field, ""))
            for field in ("question", "answer", "tags", "ontology_label", "ontology_domain")
        )
        if pattern.search(haystack):
            return True
    return False


def build_general_fallback_answer(query: str) -> str:
    """검색 결과가 부족할 때 고객에게 보일 부드러운 일반 안내를 만든다."""
    if BOTOX_PATTERN.search(query or ""):
        return (
            "보톡스는 표정 주름이나 근육 사용으로 생기는 라인을 완화하는 목적으로 상담되는 경우가 많습니다. "
            "다만 적합한 부위와 용량, 주기, 주의사항은 개인의 근육 움직임과 피부 상태에 따라 달라질 수 있습니다.\n\n"
            "상담 시 원하시는 부위와 기존 시술 경험, 걱정되는 점을 함께 말씀해 주시면 더 안전하게 안내받으실 수 있습니다."
        )
    if GENERAL_INFO_PATTERN.search(query or ""):
        return (
            "문의하신 병원 이용 정보는 방문 전 확인하시면 좋습니다. "
            "주차, 위치, 진료시간 같은 일반 안내는 병원 이용 편의를 위한 정보이며, "
            "방문 일정에 따라 달라질 수 있는 부분만 추가 확인하시면 됩니다."
        )
    return (
        "문의하신 내용은 상담 전 확인하면 좋은 항목입니다. "
        "정확한 판단이나 확정 안내가 필요한 내용은 개인 상태와 상담 내용에 따라 달라질 수 있으므로, "
        "관심 부위와 궁금한 점을 조금 더 구체적으로 알려주시면 안전한 범위에서 안내드리겠습니다."
    )


def build_demo_fallback_answer(query: str, retrieved_docs: list[dict]) -> str:
    """OPENAI_API_KEY가 없을 때도 데모 테스트가 가능하도록 검색 결과 기반 답변을 만든다."""
    if not retrieved_docs:
        return build_general_fallback_answer(query)

    top = retrieved_docs[0]
    risk = top.get("medical_risk_level", "unknown")
    routing = top.get("routing_action", "")
    recommended = top.get("recommended_response", "")

    if risk == "high" or routing:
        safety = f"\n\n⚠️ 안전 안내: {recommended or routing}\n진단이나 부작용 판단은 의료진 확인이 필요합니다."
    else:
        safety = "\n\n※ 이 답변은 FAQ 문서를 바탕으로 한 안내이며, 정확한 판단은 병원 상담실 확인이 필요합니다."

    return (
        "현재 OpenAI API Key가 없어 데모 모드로 동작 중입니다.\n"
        "검색된 FAQ를 바탕으로 임시 답변을 보여드립니다.\n\n"
        f"{top.get('answer', '')}"
        f"{safety}"
    )


def generate_answer(query: str, chat_history: list = None) -> dict:
    """
    사용자 질문에 대해 RAG 기반 답변을 생성합니다.

    Args:
        query: 사용자 질문
        chat_history: 이전 대화 기록 (멀티턴 지원)

    Returns:
        {
            "answer": 생성된 답변,
            "sources": 참조된 FAQ 목록,
            "is_found": FAQ에서 찾았는지 여부
        }
    """
    # ── Step 1: 벡터 검색 ──────────────────────────────────
    retrieved = search_faq(query, top_k=3)

    # ── Step 2: 유사도 필터링 ─────────────────────────────
    # 낮은 유사도 문서 제거 → 할루시네이션 방지
    filtered = [r for r in retrieved if r["score"] >= SIMILARITY_THRESHOLD]
    is_found = len(filtered) > 0

    # ── Step 3: 가격/견적 문의는 금액을 생성하지 않고 상담원 연결로 즉시 전환 ──
    if is_price_query(query):
        answer = build_price_handoff_answer(query)
        return {
            "answer": answer,
            "sources": filtered,
            "is_found": is_found,
            "needs_handoff": True,
            "mode": "price_handoff_no_amount",
        }

    # ── Step 4: 단순 일반/시술 문의에서 검색 결과가 부족하거나 엉뚱하면 부드러운 일반 안내 ──
    has_botox_query = bool(BOTOX_PATTERN.search(query or ""))
    has_general_info_query = bool(GENERAL_INFO_PATTERN.search(query or ""))
    if (
        (has_botox_query and not docs_contain_keyword(filtered, BOTOX_PATTERN))
        or (has_general_info_query and not docs_contain_keyword(filtered, GENERAL_INFO_PATTERN))
    ):
        answer = build_general_fallback_answer(query)
        return {
            "answer": answer,
            "sources": [],
            "is_found": False,
            "needs_handoff": should_offer_counselor_link(query, answer, []),
            "mode": "general_fallback_category_mismatch",
        }

    # ── Step 5: 프롬프트 구성 ─────────────────────────────
    user_prompt = build_user_prompt(query, filtered)

    # ── Step 6: 대화 히스토리 구성 ────────────────────────
    messages = []
    if chat_history:
        messages.extend(chat_history)
    messages.append({"role": "user", "content": user_prompt})

    # ── Step 7: OpenAI ChatGPT API 호출 ────────────────────────────
    # API Key가 없으면 강의/화면 테스트를 위해 검색 결과 기반 fallback 답변을 반환한다.
    if not os.getenv("OPENAI_API_KEY"):
        fallback_answer = build_demo_fallback_answer(query, filtered)
        return {
            "answer": fallback_answer,
            "sources": filtered,
            "is_found": is_found,
            "needs_handoff": should_offer_counselor_link(query, fallback_answer, filtered),
            "mode": "demo_fallback_no_openai_key",
        }

    client = get_openai_client()
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": build_system_prompt()},
            *messages,
        ],
        max_tokens=1024,
        temperature=0.2,
    )
    answer = remove_price_values(clean_public_answer(response.choices[0].message.content))
    answer = remove_unneeded_handoff_sentence(answer, query)
    needs_handoff = should_offer_counselor_link(query, answer, filtered)

    return {
        "answer": answer,
        "sources": filtered,
        "is_found": is_found,
        "needs_handoff": needs_handoff,
    }


# ── Phase 2 예정: Hybrid Search ───────────────────────────
# def hybrid_search(query: str, top_k: int = 5) -> list[dict]:
#     """BM25 + 벡터 검색 융합 (Phase 2에서 구현)"""
#     pass

# ── Phase 2 예정: Multi-Query Transformation ──────────────
# def expand_query(query: str) -> list[str]:
#     """Claude로 질문을 3가지 버전으로 확장 (Phase 2에서 구현)"""
#     pass

# ── Phase 3 예정: Re-ranking ──────────────────────────────
# def rerank(query: str, docs: list[dict]) -> list[dict]:
#     """Cohere Re-ranker로 결과 재순위화 (Phase 3에서 구현)"""
#     pass


# ── 직접 실행 시 테스트 ───────────────────────────────────
if __name__ == "__main__":
    test_queries = [
        "상담 예약은 어떻게 하나요?",
        "수술 후 피가 나면 괜찮나요?",
        "쌍꺼풀 비용이 궁금해요",
    ]

    for query in test_queries:
        print(f"\n{'='*50}")
        print(f"❓ 질문: {query}")
        result = generate_answer(query)
        print(f"💬 답변: {result['answer']}")
        if result["sources"]:
            print(f"📎 출처: {[s['question'][:30] for s in result['sources']]}")
        else:
            print("📎 출처: FAQ에서 찾지 못함")
