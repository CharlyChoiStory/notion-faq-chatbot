"""
test_rag.py
───────────
기본 RAG 파이프라인 테스트
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_search_returns_results():
    """검색 결과가 반환되는지 확인"""
    from embeddings import search_faq
    results = search_faq("환불 방법", top_k=3)
    assert isinstance(results, list), "결과는 리스트여야 합니다"
    print(f"✅ 검색 결과 {len(results)}개 반환됨")

def test_search_score_range():
    """유사도 점수가 0~1 범위인지 확인"""
    from embeddings import search_faq
    results = search_faq("회원가입", top_k=3)
    for r in results:
        assert 0 <= r["score"] <= 1, f"유사도 범위 오류: {r['score']}"
    print("✅ 유사도 점수 범위 정상 (0~1)")

def test_answer_generation():
    """답변 생성 구조 확인"""
    from rag_chain import generate_answer
    result = generate_answer("테스트 질문입니다")
    assert "answer" in result, "answer 키가 없습니다"
    assert "sources" in result, "sources 키가 없습니다"
    assert "is_found" in result, "is_found 키가 없습니다"
    print(f"✅ 답변 생성 구조 정상")
    print(f"   is_found: {result['is_found']}")
    print(f"   answer 길이: {len(result['answer'])}자")

def test_unknown_question():
    """FAQ에 없는 질문 처리 확인"""
    from rag_chain import generate_answer
    result = generate_answer("오늘 서울 날씨가 어때요?")
    print(f"✅ 없는 질문 처리: is_found={result['is_found']}")
    print(f"   답변: {result['answer'][:100]}...")

if __name__ == "__main__":
    print("🧪 RAG 파이프라인 테스트 시작\n")
    tests = [
        test_search_returns_results,
        test_search_score_range,
        test_answer_generation,
        test_unknown_question,
    ]
    passed = 0
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ {test.__name__} 실패: {e}")

    print(f"\n{'='*40}")
    print(f"결과: {passed}/{len(tests)} 테스트 통과")
