# 02. 아키텍처

## 전체 데이터 흐름

```text
사용자 파일 업로드
md / txt / pdf / docx
        ↓
src/local_loader.py
텍스트 추출 + FAQ 구조 파싱 + 일반 문서 청킹 fallback
        ↓
src/ontology.py
성형외과 업무 온톨로지 태깅
        ↓
src/embeddings.py
OpenAI text-embedding-3-small 임베딩 생성
        ↓
ChromaDB
로컬 벡터 DB 저장
        ↓
사용자 질문 입력
        ↓
질문 온톨로지 확장 + 벡터 검색
        ↓
src/rag_chain.py
검색 결과 + 안전 프롬프트 + ChatGPT 답변 생성
        ↓
src/app.py
카카오톡 스타일 Streamlit UI 표시
```

## 핵심 모듈

### `src/local_loader.py`

역할:

- Markdown, txt, PDF, Word 문서 로딩
- `FAQ-001` 같은 구조화 FAQ 자동 파싱
- FAQ 구조가 없으면 섹션/문단 청킹

### `src/ontology.py`

역할:

- 성형외과 도메인 분류
- 예약, 비용, 수술 전 준비, 수술 후 관리, 응급/부작용 의심 등 자동 태깅
- 외부 Markdown JSON 온톨로지 적용
- 의료 위험도와 라우팅 액션 계산

### `src/embeddings.py`

역할:

- FAQ를 임베딩하고 ChromaDB에 저장
- 사용자 질문 검색
- 테스트 모드에서는 API 없이 결정적 해시 임베딩 사용

### `src/rag_chain.py`

역할:

- 검색 결과를 프롬프트로 구성
- 의료 안전 규칙 적용
- OpenAI ChatGPT 호출
- 내부 메타데이터/참조 기준 문구 제거

### `src/app.py`

역할:

- Streamlit UI
- 상단 병원명 `AI미인 성형외과`
- 파일 업로드 즉시 자동 인덱싱
- 답변만 깔끔하게 표시

## 저장 위치

```text
data/uploads/       업로드된 원본 문서
data/chroma_db/     로컬 벡터 DB, Git에는 포함하지 않음
```
