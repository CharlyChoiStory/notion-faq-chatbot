"""
test_ontology.py
────────────────
가벼운 업무 온톨로지 자동 태깅 테스트.
외부 API 없이 실행 가능해야 한다.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ontology import (
    annotate_faq,
    expand_query_with_ontology,
    ontology_context_for_prompt,
    term_table,
    load_external_ontology,
    EXTERNAL_ONTOLOGY,
    ROUTING_RULES,
)


def test_refund_annotation():
    meta = annotate_faq(
        "상품을 받은 후 환불할 수 있나요?",
        "일반 상품은 수령 후 7일 이내 고객센터를 통해 환불 신청이 가능합니다. 단, 개봉한 상품은 제한됩니다.",
    )
    assert meta["ontology_domain"] == "refund"
    assert meta["ontology_label"] == "환불"
    assert meta["policy_stage"] == "after_delivery"
    assert meta["policy_period"] == "7일"
    assert "opened" in meta["policy_exceptions"]


def test_query_expansion():
    expanded = expand_query_with_ontology("돈 돌려받을 수 있나요?")
    assert "온톨로지 검색 확장" in expanded
    assert "환불" in expanded


def test_term_table_has_core_terms():
    labels = {row["label"] for row in term_table()}
    assert {"환불", "반품", "취소", "교환", "AS"}.issubset(labels)


def test_ontology_context_contains_policy_metadata():
    docs = [{
        "question": "환불은 언제 되나요?",
        "answer": "수령 후 7일 이내 가능합니다.",
        "score": 0.91,
        "ontology_label": "환불",
        "policy_stage": "after_delivery",
        "policy_target": "general_product",
        "policy_period": "7일",
        "requires_human_review": False,
        "policy_exceptions": "opened",
    }]
    context = ontology_context_for_prompt(docs)
    assert "유형=환불" in context
    assert "단계=after_delivery" in context
    assert "기간=7일" in context


def test_external_plastic_surgery_ontology_loaded():
    data = load_external_ontology()
    assert data["ontology_name"] == "plastic_surgery_clinic_ontology"
    labels = {row["label"] for row in term_table()}
    assert {"눈성형", "코성형", "필러", "보톡스", "예약문의", "비용문의", "부작용의심"}.issubset(labels)
    assert len(ROUTING_RULES) >= 6


def test_high_risk_routing_from_external_ontology():
    meta = annotate_faq(
        "쌍수 후 시야가 이상하고 심한 통증이 있어요",
        "눈수술 후 시야 이상이나 심한 통증은 즉시 병원 또는 응급실 확인이 필요합니다.",
    )
    assert meta["medical_risk_level"] == "high"
    assert meta["routing_rule_id"] == "RULE-002"
    assert "즉시" in meta["routing_action"]
    assert meta["requires_human_review"] is True


def test_cost_question_routing_from_external_ontology():
    meta = annotate_faq(
        "쌍꺼풀 비용은 얼마인가요?",
        "비용은 개인 상태와 수술 방법에 따라 달라질 수 있어 상담 후 안내됩니다.",
    )
    assert meta["routing_rule_id"] == "RULE-004"
    assert meta["medical_risk_level"] == "medium"
    assert "상담" in meta["routing_action"]


def test_colloquial_symptom_normalization_for_nose_surgery():
    meta = annotate_faq(
        "코수술 후 피가 계속 나고 숨쉬기 힘들어요",
        "코성형 후 출혈이 계속되거나 호흡이 불편하면 즉시 병원으로 연락해 주세요.",
    )
    assert meta["medical_risk_level"] == "high"
    assert meta["routing_rule_id"] == "RULE-003"
    assert "병원" in meta["routing_action"]


if __name__ == "__main__":
    tests = [
        test_refund_annotation,
        test_query_expansion,
        test_term_table_has_core_terms,
        test_ontology_context_contains_policy_metadata,
        test_external_plastic_surgery_ontology_loaded,
        test_high_risk_routing_from_external_ontology,
        test_cost_question_routing_from_external_ontology,
        test_colloquial_symptom_normalization_for_nose_surgery,
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
