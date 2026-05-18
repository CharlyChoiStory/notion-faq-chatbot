"""
test_local_loader.py
────────────────────
로컬 문서 업로드/파싱 테스트.
외부 API 없이 Desktop의 성형외과 샘플 FAQ md 파일을 파싱한다.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from local_loader import load_faq_from_files, parse_structured_faq
from ontology import annotate_faq


SAMPLE_CANDIDATES = [
    Path.home() / "Desktop" / "plastic_surgery_faq_knowledge_base.md",
    Path.home() / "Desktop" / "notion-faq-chatbot" / "data" / "uploads" / "plastic_surgery_faq_knowledge_base.md",
]
SAMPLE = next((path for path in SAMPLE_CANDIDATES if path.exists()), SAMPLE_CANDIDATES[0])


def test_parse_plastic_surgery_sample_exists():
    assert SAMPLE.exists(), f"샘플 파일이 없습니다: {SAMPLE}"


def test_parse_plastic_surgery_sample_faqs():
    faqs = load_faq_from_files([SAMPLE])
    assert len(faqs) >= 20
    assert any("진료시간" in item["question"] for item in faqs)
    assert any("상담 예약" in item["question"] or "예약" in item["question"] for item in faqs)


def test_plastic_surgery_ontology_annotation():
    faqs = load_faq_from_files([SAMPLE])
    first = next(item for item in faqs if "진료시간" in item["question"])
    meta = annotate_faq(first["question"], first["answer"])
    assert meta["ontology_domain"] == "clinic_hours"
    assert meta["ontology_label"] == "진료시간"


def test_direct_structured_parser():
    text = """
## FAQ-999. 상담 예약은 어떻게 하나요?

**질문 예시**
- 예약하고 싶어요

**답변**
전화 또는 카카오톡 채널로 상담 예약이 가능합니다.

**태그**
상담예약, 카카오톡
"""
    faqs = parse_structured_faq(text, source_name="sample.md")
    assert len(faqs) == 1
    assert faqs[0]["faq_id"] == "FAQ-999"
    assert "카카오톡" in faqs[0]["answer"]


if __name__ == "__main__":
    tests = [
        test_parse_plastic_surgery_sample_exists,
        test_parse_plastic_surgery_sample_faqs,
        test_plastic_surgery_ontology_annotation,
        test_direct_structured_parser,
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
