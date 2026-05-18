"""
embeddings.py
─────────────
Phase 1: 로컬 FAQ 데이터를 임베딩하여 ChromaDB에 저장하는 모듈

임베딩 모델:
- 기본: OpenAI text-embedding-3-small
- OPENAI_API_KEY가 없을 때: jhgan/ko-sroberta-multitask 로컬 fallback
- 테스트: RAG_TEST_EMBEDDINGS=1 이면 네트워크/API 없이 결정적 해시 임베딩 사용

실행 방법:
    python src/embeddings.py
"""

import os
import hashlib
import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv
from local_loader import load_faq_from_files
from ontology import annotate_faq, expand_query_with_ontology

load_dotenv()

# ── 경로 설정 ─────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", os.path.join(BASE_DIR, "data", "chroma_db"))
COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "local_faq")

# ── Phase 1: OpenAI 임베딩 우선, 없으면 한국어 로컬 임베딩 fallback ─────────────────────
OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"
LOCAL_EMBEDDING_MODEL = "jhgan/ko-sroberta-multitask"


class DeterministicHashEmbeddingFunction:
    """테스트 전용: 외부 API/모델 다운로드 없이 작동하는 결정적 임베딩 함수."""

    def name(self) -> str:
        return "deterministic-hash-test-embedding"

    def _embed(self, texts):
        vectors = []
        for text in texts:
            digest = hashlib.sha256(text.encode("utf-8")).digest()
            vector = [((digest[i % len(digest)] / 255.0) * 2.0) - 1.0 for i in range(32)]
            vectors.append(vector)
        return vectors

    def __call__(self, input):
        return self._embed(input)

    def embed_documents(self, texts):
        return self._embed(texts)

    def embed_query(self, text=None, input=None):
        t = text if text is not None else input
        if isinstance(t, list):
            return self._embed(t)
        return self._embed([t])[0]


def get_chroma_collection():
    """ChromaDB 클라이언트와 컬렉션을 반환합니다."""
    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)

    # 테스트 모드: 네트워크/API 없이 빠르게 ChromaDB 인덱싱 로직 검증
    if os.getenv("RAG_TEST_EMBEDDINGS") == "1":
        embedding_fn = DeterministicHashEmbeddingFunction()
    # OpenAI API 키가 있으면 설치가 가볍고 강의용으로 안정적인 OpenAI 임베딩 사용
    elif os.getenv("OPENAI_API_KEY"):
        embedding_fn = embedding_functions.OpenAIEmbeddingFunction(
            api_key=os.getenv("OPENAI_API_KEY"),
            model_name=OPENAI_EMBEDDING_MODEL,
        )
    else:
        # fallback: 로컬 한국어 sentence-transformers 모델
        embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=LOCAL_EMBEDDING_MODEL
        )

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_fn,
        metadata={"hnsw:space": "cosine"},  # 코사인 유사도
    )
    return collection


def build_index(faq_list: list[dict], reset: bool = False):
    """
    FAQ 데이터를 임베딩하여 ChromaDB에 저장합니다.

    Args:
        faq_list: [{"question": ..., "answer": ...}, ...] 형태의 FAQ 리스트
        reset: True이면 기존 컬렉션 삭제 후 재생성
    """
    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)

    # 초기화 옵션
    if reset:
        try:
            client.delete_collection(COLLECTION_NAME)
            print("🗑️  기존 인덱스 삭제 완료")
        except Exception:
            pass

    collection = get_chroma_collection()

    # ── 문서 준비 ─────────────────────────────────────────
    # Q + A 를 합쳐서 하나의 문서로 저장 (검색 품질 향상)
    documents = []
    metadatas = []
    ids = []

    for i, faq in enumerate(faq_list):
        # 검색용 텍스트: 질문 + 답변 합치기
        doc_text = f"질문: {faq['question']}\n답변: {faq['answer']}"
        documents.append(doc_text)
        ontology_meta = annotate_faq(faq["question"], faq["answer"])
        metadatas.append({
            "question": faq["question"],
            "answer": faq["answer"],
            "source": faq.get("source", "Local FAQ"),
            "faq_id": faq.get("faq_id", f"faq_{i:04d}"),
            "tags": faq.get("tags", ""),
            "chunk_type": faq.get("chunk_type", "faq"),
            **ontology_meta,
        })
        ids.append(f"faq_{i:04d}")

    # ── ChromaDB에 저장 ───────────────────────────────────
    if os.getenv("RAG_TEST_EMBEDDINGS") == "1":
        active_model = "deterministic-hash-test-embedding"
    else:
        active_model = OPENAI_EMBEDDING_MODEL if os.getenv("OPENAI_API_KEY") else LOCAL_EMBEDDING_MODEL
    print(f"\n💾 {len(documents)}개 FAQ 임베딩 & 저장 중...")
    print(f"   모델: {active_model}")

    # 배치 처리 (대용량 FAQ 대비)
    batch_size = 50
    for start in range(0, len(documents), batch_size):
        end = min(start + batch_size, len(documents))
        collection.upsert(
            documents=documents[start:end],
            metadatas=metadatas[start:end],
            ids=ids[start:end],
        )
        print(f"   📦 배치 {start+1}~{end} 저장 완료")

    print(f"\n✅ 총 {collection.count()}개 문서 인덱싱 완료!")
    print(f"   저장 경로: {CHROMA_DB_PATH}")
    return collection


def search_faq(query: str, top_k: int = 3) -> list[dict]:
    """
    Phase 1: 벡터 유사도 검색
    Phase 2에서 Hybrid Search로 교체 예정

    Args:
        query: 사용자 질문
        top_k: 반환할 상위 결과 수

    Returns:
        [{"question": ..., "answer": ..., "score": ...}, ...]
    """
    collection = get_chroma_collection()

    expanded_query = expand_query_with_ontology(query)

    results = collection.query(
        query_texts=[expanded_query],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    retrieved = []
    for i in range(len(results["ids"][0])):
        metadata = results["metadatas"][0][i]
        retrieved.append({
            "question": metadata["question"],
            "answer": metadata["answer"],
            "score": 1 - results["distances"][0][i],  # 코사인 유사도 (1에 가까울수록 높음)
            "source": metadata["source"],
            "faq_id": metadata.get("faq_id", ""),
            "tags": metadata.get("tags", ""),
            "chunk_type": metadata.get("chunk_type", "faq"),
            "ontology_domain": metadata.get("ontology_domain", "unknown"),
            "ontology_label": metadata.get("ontology_label", "미분류"),
            "ontology_definition": metadata.get("ontology_definition", ""),
            "ontology_confidence": metadata.get("ontology_confidence", 0.0),
            "policy_stage": metadata.get("policy_stage", "unknown"),
            "policy_target": metadata.get("policy_target", "unknown"),
            "policy_period": metadata.get("policy_period", "unknown"),
            "policy_exceptions": metadata.get("policy_exceptions", ""),
            "policy_channels": metadata.get("policy_channels", ""),
            "requires_human_review": metadata.get("requires_human_review", False),
            "review_reason": metadata.get("review_reason", ""),
            "routing_rule_id": metadata.get("routing_rule_id", ""),
            "medical_risk_level": metadata.get("medical_risk_level", "unknown"),
            "routing_action": metadata.get("routing_action", ""),
            "recommended_response": metadata.get("recommended_response", ""),
            "forbidden_response": metadata.get("forbidden_response", ""),
            "ontology_source": metadata.get("ontology_source", ""),
        })

    return retrieved


# ── 직접 실행 시: 로컬 샘플 문서에서 로드 후 인덱싱 ──────────────
if __name__ == "__main__":
    # 기본 샘플: Desktop/plastic_surgery_faq_knowledge_base.md
    default_sample = os.path.expanduser("~/Desktop/plastic_surgery_faq_knowledge_base.md")
    source_path = os.environ.get("FAQ_SOURCE_FILE", default_sample)

    # 1. 로컬 파일에서 FAQ 로드
    faq_list = load_faq_from_files([source_path])
    print(f"📄 로컬 문서 로드 완료: {source_path}")
    print(f"   FAQ/청크 수: {len(faq_list)}")

    # 2. 임베딩 & 저장
    build_index(faq_list, reset=True)

    # 3. 검색 테스트
    print("\n🔍 검색 테스트:")
    test_query = "상담 예약은 어떻게 하나요?"
    results = search_faq(test_query, top_k=3)
    for r in results:
        print(f"  [유사도: {r['score']:.3f}] [{r.get('ontology_label')}] Q: {r['question']}")
