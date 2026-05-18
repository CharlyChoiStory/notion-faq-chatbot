# 09. 파일 인벤토리

## 루트 파일

### `README.md`

프로젝트 기본 설명과 실행 방법.

### `requirements.txt`

Python 패키지 고정 버전.

중요:

```text
openai==1.35.0
httpx==0.27.2
```

### `.env.example`

환경변수 템플릿. 실제 API Key는 포함하지 않습니다.

### `.gitignore`

`.env`, `.venv`, ChromaDB, 캐시 파일 제외.

### `AGENTS.md`

Hermes 에이전트가 이 프로젝트를 이해하기 위한 컨텍스트.

## `src/`

### `src/app.py`

Streamlit UI. 주요 기능:

- `AI미인 성형외과` 상단 중앙 표시
- 파일 업로드 즉시 자동 인덱싱
- 카카오톡 스타일 말풍선 UI
- 출처/정책/유사도 카드 숨김

### `src/local_loader.py`

로컬 문서 파서.

- md/txt/pdf/docx 지원
- 구조화 FAQ 파싱
- 일반 문서 청킹 fallback

### `src/ontology.py`

성형외과 온톨로지.

- 업무 유형 분류
- 위험도 계산
- 라우팅 규칙 적용
- 외부 md JSON 온톨로지 자동 로드

### `src/embeddings.py`

ChromaDB 인덱싱/검색.

- OpenAI 임베딩
- 테스트용 deterministic hash embedding
- metadata 저장

### `src/rag_chain.py`

RAG 답변 생성.

- 검색 결과 필터링
- 의료 안전 프롬프트
- OpenAI ChatGPT 호출
- 내부 메타데이터 출력 제거

### `src/notion_loader.py`

레거시 Notion loader. 현재 기본 흐름에서는 사용하지 않습니다.

## `tests/`

### `tests/test_local_loader.py`

로컬 FAQ 파싱 테스트.

### `tests/test_ontology.py`

온톨로지/위험도/라우팅 테스트.

### `tests/test_indexing.py`

API 없는 ChromaDB 인덱싱 테스트.

### `tests/test_rag.py`

초기 RAG 테스트 레거시 파일.

## `data/`

### `data/uploads/`

업로드된 원본 문서. 샘플 FAQ 문서는 포함 가능.

### `data/chroma_db/`

로컬 벡터 DB. Git에는 포함하지 않습니다.
