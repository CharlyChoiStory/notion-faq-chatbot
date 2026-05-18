"""
test_counselor.py
────────────────
성형외과 AI 상담 코디네이터 개선사항 테스트.
상담원 연결 케이스와 고객 맥락 요약이 외부 API 없이 생성되는지 검증한다.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from counselor import analyze_customer_context, create_counselor_case, load_counselor_case, detect_interest_area
from rag_chain import should_offer_counselor_link, generate_answer, is_price_query, PRICE_VALUE_PATTERN, clean_public_answer


def test_customer_context_summary_for_eye_reservation():
    analysis = analyze_customer_context(
        question="눈이 졸려 보여서 자연스럽게 쌍꺼풀 상담 받고 싶어요. 수술은 처음이고 흉터랑 회복 기간이 걱정돼요. 이번 주 토요일 오후 가능할까요?",
        answer="상담 예약을 도와드릴 수 있습니다.",
        sources=[],
    )
    assert analysis["고객 관심 부위"] == "눈"
    assert analysis["희망 변화"] == "자연스러운 인상 개선"
    assert analysis["이전 시술"] == "없음으로 추정"
    assert "흉터" in analysis["걱정 요소"]
    assert "회복 기간" in analysis["걱정 요소"]
    assert "토요일" in analysis["희망 일정"]
    assert analysis["긴급도"] == "상담 예약 의향 높음"


def test_handoff_link_needed_for_counselor_phrases():
    assert should_offer_counselor_link(
        "코수술 정확한 비용 알려주세요",
        "정확한 비용은 상담 후 안내됩니다. 상담실 연결을 도와드릴 수 있습니다.",
        [],
    ) is True


def test_handoff_link_needed_for_high_risk_source():
    assert should_offer_counselor_link(
        "수술 후 피가 계속 나요",
        "즉시 병원에 연락해 주세요.",
        [{"medical_risk_level": "high", "requires_human_review": True}],
    ) is True


def test_create_and_load_counselor_case():
    case = create_counselor_case(
        question="사진 보고 매몰 가능한지 봐주나요?",
        answer="사진은 상담 참고자료로 활용될 수 있지만 진단은 의료진 상담 후 가능합니다.",
        sources=[],
        chat_history=[],
    )
    loaded = load_counselor_case(case["case_id"])
    assert loaded is not None
    assert loaded["case_id"] == case["case_id"]
    assert loaded["analysis"]["고객 관심 부위"] == "눈"
    assert "사진 기반 판단 요청" in loaded["analysis"]["상담 연결 사유"]


def test_price_query_never_returns_amount():
    assert is_price_query("25세 여성입니다. 쌍수하려고 하는데 가격은 얼마인가요?") is True
    result = generate_answer("25세 여성입니다. 쌍수하려고 하는데 가격은 얼마인가요?")
    assert result["needs_handoff"] is True
    assert result["mode"] == "price_handoff_no_amount"
    assert "상담원" in result["answer"] or "상담실" in result["answer"]
    assert PRICE_VALUE_PATTERN.search(result["answer"]) is None


def test_handoff_html_helper_has_no_indented_code_block_shape():
    app_path = os.path.join(os.path.dirname(__file__), "..", "src", "app.py")
    with open(app_path, encoding="utf-8") as f:
        source = f.read()
    assert "<div class=\\\"handoff-card\\\">" not in source
    assert "'<div class=\"handoff-card\">'" in source


def test_latest_botox_question_overrides_previous_eye_context():
    assert detect_interest_area("보톡스 가격 문의", "이전에는 눈 상담을 했습니다") == "피부/보톡스"
    analysis = analyze_customer_context(
        question="보톡스 가격이 궁금합니다",
        answer="비용은 상담원 연결 후 안내됩니다.",
        sources=[],
        chat_history=[{"role": "user", "content": "눈 쌍수 상담 받고 싶어요"}],
    )
    assert analysis["고객 관심 부위"] == "피부/보톡스"
    assert "비용" in analysis["걱정 요소"]


def test_public_answer_never_exposes_faq_not_found_phrase():
    cleaned = clean_public_answer("죄송합니다, 해당 내용은 FAQ에서 찾을 수 없습니다.")
    assert "FAQ에서 찾을 수 없습니다" not in cleaned
    assert "기본적인 범위" in cleaned


def test_simple_botox_question_has_no_forced_handoff_or_faq_failure():
    result = generate_answer("보톡스")
    assert result["needs_handoff"] is False
    assert "FAQ에서 찾을 수 없습니다" not in result["answer"]
    assert "보톡스" in result["answer"]


def test_parking_question_has_no_counselor_link():
    result = generate_answer("주차장")
    assert result["needs_handoff"] is False
    assert "상담원 연결" not in result["answer"]
    assert "상담실로 연결" not in result["answer"]
    assert "FAQ에서 찾을 수 없습니다" not in result["answer"]


if __name__ == "__main__":
    tests = [
        test_customer_context_summary_for_eye_reservation,
        test_handoff_link_needed_for_counselor_phrases,
        test_handoff_link_needed_for_high_risk_source,
        test_create_and_load_counselor_case,
        test_price_query_never_returns_amount,
        test_handoff_html_helper_has_no_indented_code_block_shape,
        test_latest_botox_question_overrides_previous_eye_context,
        test_public_answer_never_exposes_faq_not_found_phrase,
        test_simple_botox_question_has_no_forced_handoff_or_faq_failure,
        test_parking_question_has_no_counselor_link,
    ]
    passed = 0
    for test in tests:
        try:
            test()
            print(f"✅ {test.__name__}")
            passed += 1
        except Exception as e:
            print(f"❌ {test.__name__}: {e}")
    print(f"결과: {passed}/{len(tests)} 통과")
    if passed != len(tests):
        raise SystemExit(1)
