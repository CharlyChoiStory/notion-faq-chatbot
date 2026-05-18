"""
test_indexing.py
────────────────
ChromaDB 인덱싱/검색 파이프라인 테스트.
RAG_TEST_EMBEDDINGS=1 환경에서 외부 API/모델 다운로드 없이 실행한다.
"""

import os
import sys
import tempfile
from pathlib import Path

# embeddings 모듈 import 전에 테스트용 환경 변수를 지정해야 한다.
tmpdir = tempfile.TemporaryDirectory()
os.environ["RAG_TEST_EMBEDDINGS"] = "1"
os.environ["CHROMA_DB_PATH"] = tmpdir.name
os.environ["CHROMA_COLLECTION_NAME"] = "test_local_faq"

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from local_loader import load_faq_from_files
from embeddings import build_index, search_faq

SAMPLE_CANDIDATES = [
    Path.home() / "Desktop" / "plastic_surgery_faq_knowledge_base.md",
    Path(__file__).resolve().parents[1] / "data" / "uploads" / "plastic_surgery_faq_knowledge_base.md",
]
SAMPLE = next((path for path in SAMPLE_CANDIDATES if path.exists()), SAMPLE_CANDIDATES[0])


def test_build_index_and_search_with_local_sample():
    faqs = load_faq_from_files([SAMPLE])[:8]
    collection = build_index(faqs, reset=True)
    assert collection.count() == 8
    results = search_faq("상담 예약은 어떻게 하나요?", top_k=3)
    assert len(results) == 3
    assert all("question" in r and "answer" in r and "ontology_label" in r for r in results)


if __name__ == "__main__":
    try:
        test_build_index_and_search_with_local_sample()
        print("✅ test_build_index_and_search_with_local_sample")
        print("결과: 1/1 통과")
    finally:
        tmpdir.cleanup()
