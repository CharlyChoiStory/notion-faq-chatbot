# 프로젝트 컨텍스트 — Notion FAQ RAG 챗봇

> 이 파일은 Claude Code / Hermes 에이전트가 새 세션에서 자동으로 읽어들이는 컨텍스트 파일입니다.
> `claude -c` 또는 `hermes` 실행 시 자동 로드됩니다.

---

## 👤 개발자 정보

- **이름**: 찰리초이 (Charlie Choi)
- **배경**: 컴퓨터 사이언스 석사 / IT 컨설팅·교육 전문가 (Google Workspace, Gemini)
- **현재**: AI 바이브코딩 교육 수강 중 + 서울시 시니어 AI 강사
- **유튜브**: 찰리초이 스토리 채널 (중장년 대상, 암호화폐·경제·금융 AI 분석)
- **AI 에이전트**: 에르메스(Hermes) + Claude Code + OpenCode 조합으로 작업

---

## 🎯 프로젝트 목적

**Notion FAQ 데이터를 기반으로 한 RAG 자연어 AI 챗봇**

- 소스 데이터: Notion 페이지 (FAQ 형식)
- 목적: 교육용 바이브코딩 실습 프로젝트
- UI: 카카오톡 스타일 Streamlit 챗봇
- 추후: 유튜브 콘텐츠 ("RAG 검색 품질을 높이는 6가지 방법") 연계 예정

---

## 🛠️ 기술 스택

| 역할 | 선택 |
|------|------|
| 데이터 소스 | Notion API |
| RAG 프레임워크 | LlamaIndex |
| 임베딩 | `jhgan/ko-sroberta-multitask` (한국어 특화, 무료) |
| 벡터 DB | ChromaDB (로컬, `data/chroma_db/`) |
| LLM | Claude API (`claude-opus-4-5`) |
| UI | Streamlit — 카카오톡 스타일 |
| 개발 환경 | VSCode + Claude Code + Hermes |

---

## 📁 프로젝트 구조

```
notion-faq-chatbot/
├── CLAUDE.md              ← 이 파일 (Claude Code / Hermes 컨텍스트)
├── AGENTS.md              ← Hermes 전용 컨텍스트
├── README.md
├── .env                   ← API 키 (git 제외)
├── .env.example
├── .gitignore
├── requirements.txt
├── src/
│   ├── notion_loader.py   ← Notion 데이터 추출 & 파싱
│   ├── embeddings.py      ← 임베딩 & ChromaDB 저장/검색
│   ├── rag_chain.py       ← RAG 핵심 로직 (검색 → Claude 답변)
│   └── app.py             ← Streamlit 카카오톡 UI
├── data/
│   └── chroma_db/         ← 벡터 DB 저장소
├── docs/
│   ├── 개발계획.md
│   ├── 구현로드맵.md
│   ├── API설정가이드.md
│   └── 사용법.md
└── tests/
    └── test_rag.py
```

---

## 🗺️ 구현 로드맵 (점진적 개선)

### ✅ Phase 1 — 기본 동작 (현재 목표)
- [x] 프로젝트 구조 생성
- [x] 소스 코드 기본 파일 생성 (notion_loader, embeddings, rag_chain, app)
- [ ] Python 가상환경 & 라이브러리 설치
- [ ] Notion API 연동 테스트
- [ ] 임베딩 & ChromaDB 인덱싱
- [ ] Streamlit 챗봇 실행 확인

### ⏳ Phase 2 — 검색 품질 향상
- [ ] Hybrid Search (BM25 + 벡터 검색 융합)
- [ ] Multi-Query Transformation (질문 3가지 버전 확장)

### ⏳ Phase 3 — 고품질 완성
- [ ] Re-ranking (Cohere 또는 BGE)
- [ ] Parent-Child 청킹
- [ ] Contextual Compression

---

## ⚙️ 주요 설정값

```python
EMBEDDING_MODEL = "jhgan/ko-sroberta-multitask"
LLM_MODEL = "claude-opus-4-5"
CHROMA_COLLECTION = "notion_faq"
SIMILARITY_THRESHOLD = 0.4   # 이 값 이하는 "모른다"고 답변
TOP_K = 3                    # 검색 상위 결과 수
```

---

## 🚀 빠른 시작 명령어

```bash
# 프로젝트 폴더 이동
cd /Users/charlychoi/Desktop/notion-faq-chatbot

# 가상환경 활성화
source venv/bin/activate

# Notion 데이터 인덱싱 (최초 1회)
python src/embeddings.py

# 챗봇 실행
streamlit run src/app.py

# 테스트 실행
python tests/test_rag.py
```

---

## ⚠️ 주의사항 & 알려진 이슈

- M3 MacBook Air 8GB → 로컬 LLM 실행 어려움, API 방식 사용
- `.env` 파일에 API 키 필수 (`.env.example` 참고)
- ChromaDB 재인덱싱 시 `reset=True` 옵션 사용
- 한국어 구어체 처리: `jhgan/ko-sroberta-multitask` 임베딩 권장

---

## 💬 대화 맥락 요약

에르메스(Hermes AI 에이전트)와 찰리가 함께 기획한 프로젝트입니다.
검색 품질 향상을 위해 Hybrid Search, Query Transformation, Re-ranking 등
6가지 전략을 논의하였고, Phase 1 → 2 → 3 순서로 점진적으로 구현하기로 했습니다.
UI는 찰리 요청에 따라 카카오톡 스타일로 디자인되었습니다.
