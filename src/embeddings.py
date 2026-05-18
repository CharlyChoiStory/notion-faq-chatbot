"""
embeddings.py
─────────────
FAQ 데이터를 임베딩하여 선택 가능한 Vector DB에 저장/검색하는 모듈.

지원 백엔드:
- 기본: ChromaDB 로컬 저장소
- 선택: Supabase Postgres + pgvector

전환 방법:
    VECTOR_DB_BACKEND=chroma      # 기본값
    VECTOR_DB_BACKEND=supabase    # 공개 웹/클라우드용

임베딩 모델:
- 기본: OpenAI text-embedding-3-small
- 테스트: RAG_TEST_EMBEDDINGS=1 이면 네트워크/API 없이 결정적 해시 임베딩 사용

실행 방법:
    python src/embeddings.py
"""

from __future__ import annotations

import hashlib
import math
import os
from typing import Any

import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv

from local_loader import load_faq_from_files
from ontology import annotate_faq, expand_query_with_ontology

load_dotenv()

# ── 경로/백엔드 설정 ───────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VECTOR_DB_BACKEND = os.getenv("VECTOR_DB_BACKEND", "chroma").strip().lower()

CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", os.path.join(BASE_DIR, "data", "chroma_db"))
COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "local_faq")

SUPABASE_DB_URL = os.getenv("SUPABASE_DB_URL", "")
SUPABASE_VECTOR_TABLE = os.getenv("SUPABASE_VECTOR_TABLE", "faq_vectors")

# ── 임베딩 설정 ─────────────────────────────────────────────
OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
LOCAL_EMBEDDING_MODEL = "jhgan/ko-sroberta-multitask"
TEST_EMBEDDING_DIM = 32
OPENAI_EMBEDDING_DIM = int(os.getenv("OPENAI_EMBEDDING_DIM", "1536"))


class DeterministicHashEmbeddingFunction:
    """테스트 전용: 외부 API/모델 다운로드 없이 작동하는 결정적 임베딩 함수."""

    def name(self) -> str:
        return "deterministic-hash-test-embedding"

    def __call__(self, input):
        return [deterministic_hash_embedding(text) for text in input]

    def embed_documents(self, texts):
        return [deterministic_hash_embedding(text) for text in texts]

    def embed_query(self, text=None, input=None):
        t = text if text is not None else input
        if isinstance(t, list):
            return [deterministic_hash_embedding(x) for x in t]
        return deterministic_hash_embedding(t)


def deterministic_hash_embedding(text: str, dim: int = TEST_EMBEDDING_DIM) -> list[float]:
    """테스트 전용 결정적 임베딩 벡터."""
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    return [((digest[i % len(digest)] / 255.0) * 2.0) - 1.0 for i in range(dim)]


def get_active_embedding_dim() -> int:
    return TEST_EMBEDDING_DIM if os.getenv("RAG_TEST_EMBEDDINGS") == "1" else OPENAI_EMBEDDING_DIM


def get_active_embedding_model_name() -> str:
    if os.getenv("RAG_TEST_EMBEDDINGS") == "1":
        return "deterministic-hash-test-embedding"
    return OPENAI_EMBEDDING_MODEL if os.getenv("OPENAI_API_KEY") else LOCAL_EMBEDDING_MODEL


def embed_texts(texts: list[str]) -> list[list[float]]:
    """백엔드 독립 임베딩 생성. Supabase 저장 시 직접 벡터가 필요하다."""
    if os.getenv("RAG_TEST_EMBEDDINGS") == "1":
        return [deterministic_hash_embedding(text) for text in texts]

    if os.getenv("OPENAI_API_KEY"):
        from openai import OpenAI

        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.embeddings.create(
            model=OPENAI_EMBEDDING_MODEL,
            input=texts,
        )
        return [item.embedding for item in response.data]

    # Chroma 로컬 fallback과 맞추기 위한 sentence-transformers fallback.
    # Supabase 공개 웹 배포에서는 OPENAI_API_KEY 사용을 권장한다.
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(LOCAL_EMBEDDING_MODEL)
    return model.encode(texts, normalize_embeddings=True).tolist()


def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def vector_literal(vector: list[float]) -> str:
    """pgvector가 받는 '[0.1,0.2,...]' 문자열로 변환."""
    return "[" + ",".join(f"{x:.8f}" for x in vector) + "]"


def normalize_metadata_value(value: Any) -> Any:
    """Chroma/Supabase 공통 저장을 위해 복합 타입을 문자열화."""
    if value is None:
        return ""
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (list, tuple, set)):
        return ", ".join(str(v) for v in value)
    return str(value)


def prepare_documents(faq_list: list[dict]) -> tuple[list[str], list[dict], list[str]]:
    """FAQ 리스트를 문서/메타데이터/id로 변환."""
    documents: list[str] = []
    metadatas: list[dict] = []
    ids: list[str] = []

    for i, faq in enumerate(faq_list):
        doc_text = f"질문: {faq['question']}\n답변: {faq['answer']}"
        ontology_meta = annotate_faq(faq["question"], faq["answer"])
        metadata = {
            "question": faq["question"],
            "answer": faq["answer"],
            "source": faq.get("source", "Local FAQ"),
            "faq_id": faq.get("faq_id", f"faq_{i:04d}"),
            "tags": faq.get("tags", ""),
            "chunk_type": faq.get("chunk_type", "faq"),
            **ontology_meta,
        }
        documents.append(doc_text)
        metadatas.append({k: normalize_metadata_value(v) for k, v in metadata.items()})
        ids.append(f"faq_{i:04d}")

    return documents, metadatas, ids


# ── ChromaDB backend ───────────────────────────────────────

def get_chroma_collection():
    """ChromaDB 클라이언트와 컬렉션을 반환합니다."""
    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)

    if os.getenv("RAG_TEST_EMBEDDINGS") == "1":
        embedding_fn = DeterministicHashEmbeddingFunction()
    elif os.getenv("OPENAI_API_KEY"):
        embedding_fn = embedding_functions.OpenAIEmbeddingFunction(
            api_key=os.getenv("OPENAI_API_KEY"),
            model_name=OPENAI_EMBEDDING_MODEL,
        )
    else:
        embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=LOCAL_EMBEDDING_MODEL
        )

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_fn,
        metadata={"hnsw:space": "cosine"},
    )
    return collection


def build_index_chroma(faq_list: list[dict], reset: bool = False):
    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)

    if reset:
        try:
            client.delete_collection(COLLECTION_NAME)
            print("🗑️  기존 Chroma 인덱스 삭제 완료")
        except Exception:
            pass

    collection = get_chroma_collection()
    documents, metadatas, ids = prepare_documents(faq_list)

    print(f"\n💾 {len(documents)}개 FAQ 임베딩 & ChromaDB 저장 중...")
    print(f"   모델: {get_active_embedding_model_name()}")

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


def search_faq_chroma(query: str, top_k: int = 3) -> list[dict]:
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
        retrieved.append(metadata_to_result(metadata, 1 - results["distances"][0][i]))
    return retrieved


# ── Supabase pgvector backend ──────────────────────────────

def require_supabase_db_url() -> str:
    if not SUPABASE_DB_URL:
        raise RuntimeError(
            "VECTOR_DB_BACKEND=supabase 사용 시 SUPABASE_DB_URL이 필요합니다. "
            "Supabase Project Settings > Database > Connection string(Postgres URI)을 .env에 넣어 주세요."
        )
    return SUPABASE_DB_URL


def get_psycopg():
    try:
        import psycopg
        from psycopg import sql
    except ImportError as exc:
        raise RuntimeError("Supabase backend에는 psycopg[binary] 설치가 필요합니다: pip install 'psycopg[binary]'") from exc
    return psycopg, sql


def ensure_supabase_schema(conn) -> None:
    """Supabase Postgres에 pgvector 테이블을 준비한다."""
    _, sql = get_psycopg()
    dim = get_active_embedding_dim()
    table = sql.Identifier(SUPABASE_VECTOR_TABLE)
    with conn.cursor() as cur:
        cur.execute("create extension if not exists vector")
        cur.execute(sql.SQL("""
            create table if not exists {table} (
                id text primary key,
                document text not null,
                metadata jsonb not null default '{{}}'::jsonb,
                embedding vector({dim}) not null,
                created_at timestamptz not null default now()
            )
        """).format(table=table, dim=sql.SQL(str(dim))))
        cur.execute(sql.SQL("""
            create index if not exists {idx}
            on {table}
            using ivfflat (embedding vector_cosine_ops)
            with (lists = 100)
        """).format(
            idx=sql.Identifier(f"{SUPABASE_VECTOR_TABLE}_embedding_idx"),
            table=table,
        ))
    conn.commit()


def build_index_supabase(faq_list: list[dict], reset: bool = False):
    psycopg, sql = get_psycopg()
    documents, metadatas, ids = prepare_documents(faq_list)
    embeddings = embed_texts(documents)

    print(f"\n💾 {len(documents)}개 FAQ 임베딩 & Supabase pgvector 저장 중...")
    print(f"   모델: {get_active_embedding_model_name()}")
    print(f"   테이블: {SUPABASE_VECTOR_TABLE}")

    with psycopg.connect(require_supabase_db_url()) as conn:
        ensure_supabase_schema(conn)
        table = sql.Identifier(SUPABASE_VECTOR_TABLE)
        with conn.cursor() as cur:
            if reset:
                cur.execute(sql.SQL("delete from {table}").format(table=table))
                print("🗑️  기존 Supabase 벡터 레코드 삭제 완료")

            for doc_id, document, metadata, embedding in zip(ids, documents, metadatas, embeddings):
                cur.execute(
                    sql.SQL("""
                        insert into {table} (id, document, metadata, embedding)
                        values (%s, %s, %s, %s::vector)
                        on conflict (id) do update set
                            document = excluded.document,
                            metadata = excluded.metadata,
                            embedding = excluded.embedding
                    """).format(table=table),
                    (doc_id, document, metadata, vector_literal(embedding)),
                )
        conn.commit()

        with conn.cursor() as cur:
            cur.execute(sql.SQL("select count(*) from {table}").format(table=table))
            count = cur.fetchone()[0]

    print(f"\n✅ 총 {count}개 문서 인덱싱 완료!")
    print("   저장 위치: Supabase Postgres + pgvector")
    return {"backend": "supabase", "table": SUPABASE_VECTOR_TABLE, "count": count}


def search_faq_supabase(query: str, top_k: int = 3) -> list[dict]:
    psycopg, sql = get_psycopg()
    expanded_query = expand_query_with_ontology(query)
    query_embedding = embed_texts([expanded_query])[0]
    table = sql.Identifier(SUPABASE_VECTOR_TABLE)

    with psycopg.connect(require_supabase_db_url()) as conn:
        ensure_supabase_schema(conn)
        with conn.cursor() as cur:
            cur.execute(
                sql.SQL("""
                    select metadata, 1 - (embedding <=> %s::vector) as score
                    from {table}
                    order by embedding <=> %s::vector
                    limit %s
                """).format(table=table),
                (vector_literal(query_embedding), vector_literal(query_embedding), top_k),
            )
            rows = cur.fetchall()

    return [metadata_to_result(metadata, float(score)) for metadata, score in rows]


# ── Public API ─────────────────────────────────────────────

def metadata_to_result(metadata: dict, score: float) -> dict:
    return {
        "question": metadata.get("question", ""),
        "answer": metadata.get("answer", ""),
        "score": score,
        "source": metadata.get("source", ""),
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
    }


def build_index(faq_list: list[dict], reset: bool = False):
    """FAQ 데이터를 선택된 Vector DB backend에 저장합니다."""
    if VECTOR_DB_BACKEND == "supabase":
        return build_index_supabase(faq_list, reset=reset)
    if VECTOR_DB_BACKEND == "chroma":
        return build_index_chroma(faq_list, reset=reset)
    raise ValueError(f"지원하지 않는 VECTOR_DB_BACKEND입니다: {VECTOR_DB_BACKEND}")


def search_faq(query: str, top_k: int = 3) -> list[dict]:
    """선택된 Vector DB backend에서 FAQ를 검색합니다."""
    if VECTOR_DB_BACKEND == "supabase":
        return search_faq_supabase(query, top_k=top_k)
    if VECTOR_DB_BACKEND == "chroma":
        return search_faq_chroma(query, top_k=top_k)
    raise ValueError(f"지원하지 않는 VECTOR_DB_BACKEND입니다: {VECTOR_DB_BACKEND}")


# ── 직접 실행 시: 로컬 샘플 문서에서 로드 후 인덱싱 ──────────────
if __name__ == "__main__":
    default_sample = os.path.join(BASE_DIR, "data", "uploads", "plastic_surgery_faq_knowledge_base.md")
    source_path = os.environ.get("FAQ_SOURCE_FILE", default_sample)

    faq_list = load_faq_from_files([source_path])
    print(f"📄 로컬 문서 로드 완료: {source_path}")
    print(f"   FAQ/청크 수: {len(faq_list)}")

    build_index(faq_list, reset=True)

    print("\n🔍 검색 테스트:")
    test_query = "상담 예약은 어떻게 하나요?"
    results = search_faq(test_query, top_k=3)
    for r in results:
        print(f"  [유사도: {r['score']:.3f}] [{r.get('ontology_label')}] Q: {r['question']}")
