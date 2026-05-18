# 10. Supabase Vector DB 전환 가이드

## 목적

로컬 `data/chroma_db`에 저장하던 벡터 DB를 공개 웹/클라우드 환경에서 접근 가능한 **Supabase Postgres + pgvector**로 교체할 수 있게 합니다.

현재 구조는 백엔드 선택형입니다.

```text
VECTOR_DB_BACKEND=chroma     # 기본 로컬 모드
VECTOR_DB_BACKEND=supabase   # 클라우드 모드
```

## 필요한 Supabase 설정

1. Supabase 프로젝트 생성
2. Database password 확인
3. Project Settings > Database > Connection string > URI 복사
4. `.env`에 입력

```bash
VECTOR_DB_BACKEND=supabase
SUPABASE_DB_URL=postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
SUPABASE_VECTOR_TABLE=faq_vectors
```

## 테이블 생성

앱이 처음 인덱싱할 때 자동으로 다음을 시도합니다.

```sql
create extension if not exists vector;
create table if not exists faq_vectors (
  id text primary key,
  document text not null,
  metadata jsonb not null default '{}'::jsonb,
  embedding vector(1536) not null,
  created_at timestamptz not null default now()
);
create index if not exists faq_vectors_embedding_idx
on faq_vectors
using ivfflat (embedding vector_cosine_ops)
with (lists = 100);
```

Supabase 권한 정책이나 extension 권한 문제로 자동 생성이 막히면 Supabase SQL Editor에서 위 SQL을 직접 실행합니다.

## 임베딩 차원

기본 OpenAI 모델:

```text
text-embedding-3-small → 1536 dimensions
```

환경변수:

```bash
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_EMBEDDING_DIM=1536
```

## 로컬 테스트

기존 Chroma 테스트:

```bash
RAG_TEST_EMBEDDINGS=1 .venv/bin/python tests/test_indexing.py
```

Supabase live 테스트는 실제 `SUPABASE_DB_URL`이 있어야 합니다.

```bash
VECTOR_DB_BACKEND=supabase \
SUPABASE_DB_URL='postgresql://...' \
.venv/bin/python src/embeddings.py
```

## 보안 주의

- `SUPABASE_DB_URL`에는 DB password가 포함됩니다.
- 절대 GitHub에 `.env`를 올리지 않습니다.
- 공개 웹 배포 환경에서는 플랫폼의 Secret/Environment Variable 기능에 등록합니다.

## 현재 구현 파일

```text
src/embeddings.py
```

핵심 함수:

```text
build_index()
search_faq()
build_index_chroma()
search_faq_chroma()
build_index_supabase()
search_faq_supabase()
```
