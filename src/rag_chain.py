"""
rag_chain.py
────────────
RAG 핵심 로직: 검색 → 프롬프트 구성 → OpenAI ChatGPT 답변 생성

Phase 1: 로컬 문서 업로드 + 벡터 검색 + ChatGPT 답변
Phase 2: Hybrid Search + Multi-Query (TODO)
Phase 3: Re-ranking + Parent-Child (TODO)
"""

import os
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
    return """당신은 성형외과 FAQ 안내를 돕는 친절하고 정확한 AI 도우미입니다.

규칙:
1. 제공된 FAQ 컨텍스트를 기반으로만 답변하세요.
2. FAQ에 없는 내용은 "죄송합니다, 해당 내용은 FAQ에서 찾을 수 없습니다."라고 명확히 안내하세요.
3. 답변은 간결하고 친절하게 한국어로 작성하세요.
4. 추측하거나 없는 정보를 만들어내지 마세요.
5. 진단, 처방, 수술 가능 여부, 부작용 판단, 결과 보장은 하지 마세요.
6. 심한 통증, 지속적인 출혈, 호흡곤란, 고열, 갑작스러운 시야 이상 등은 즉시 병원 또는 응급실 문의를 안내하세요.
7. 비용은 확정 금액처럼 말하지 말고 FAQ에 있는 범위/상담 필요성을 기준으로 안내하세요.
"""


def build_user_prompt(query: str, retrieved_docs: list[dict]) -> str:
    """검색 결과를 포함한 사용자 프롬프트를 구성합니다."""
    if not retrieved_docs:
        context = "관련 FAQ를 찾을 수 없습니다."
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
- 사용자에게 내부 정책유형, 단계명, 기간값, 유사도, 출처 메타데이터, '참조 기준' 문구는 표시하지 마세요.

위 FAQ를 바탕으로 정확하고 친절하게 답변해주세요."""


def clean_public_answer(answer: str) -> str:
    """사용자 화면에 노출하면 안 되는 내부 참조/메타데이터 문구를 제거한다."""
    cleaned_lines = []
    for line in answer.splitlines():
        stripped = line.strip()
        if stripped.startswith("참조 기준"):
            continue
        if stripped.startswith("정책유형="):
            continue
        cleaned_lines.append(line)
    return "\n".join(cleaned_lines).strip()


def build_demo_fallback_answer(query: str, retrieved_docs: list[dict]) -> str:
    """OPENAI_API_KEY가 없을 때도 데모 테스트가 가능하도록 검색 결과 기반 답변을 만든다."""
    if not retrieved_docs:
        return (
            "현재 OpenAI API Key가 없어 데모 모드로 동작 중입니다.\n\n"
            "죄송합니다, 업로드된 FAQ에서 해당 질문과 직접 관련된 내용을 찾지 못했습니다. "
            "성형외과 상담/진료 관련 질문은 병원 상담실에 확인해 주세요."
        )

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

    # ── Step 3: 프롬프트 구성 ─────────────────────────────
    user_prompt = build_user_prompt(query, filtered)

    # ── Step 4: 대화 히스토리 구성 ────────────────────────
    messages = []
    if chat_history:
        messages.extend(chat_history)
    messages.append({"role": "user", "content": user_prompt})

    # ── Step 5: OpenAI ChatGPT API 호출 ────────────────────────────
    # API Key가 없으면 강의/화면 테스트를 위해 검색 결과 기반 fallback 답변을 반환한다.
    if not os.getenv("OPENAI_API_KEY"):
        return {
            "answer": build_demo_fallback_answer(query, filtered),
            "sources": filtered,
            "is_found": is_found,
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
    answer = clean_public_answer(response.choices[0].message.content)

    return {
        "answer": answer,
        "sources": filtered,
        "is_found": is_found,
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
