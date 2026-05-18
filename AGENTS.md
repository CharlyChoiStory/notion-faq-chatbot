# Hermes 에이전트 컨텍스트 — Notion FAQ RAG 챗봇

> 이 파일은 Hermes(에르메스) 에이전트가 이 폴더에서 실행될 때 자동으로 읽습니다.
> `workdir`를 이 폴더로 설정하면 새 세션에서도 맥락이 유지됩니다.

---

## 👤 사용자 정보

- **호칭**: 찰리 (Charlie Choi)
- **에이전트 호칭**: 에르메스 (Hermes)
- **소통 언어**: 한국어
- **컴퓨터**: MacBook Air 15, Apple M3, 8GB RAM, macOS Tahoe 26.4.1

---

## 🎯 이 프로젝트에서 에르메스의 역할

1. **코드 작성 & 디버깅** — Claude Code / OpenCode와 협업
2. **기술 전략 수립** — RAG 검색 품질 향상 방안 설계
3. **콘텐츠 연계** — 개발 과정을 유튜브 콘텐츠화 아이디어 제공
4. **교육 자료 지원** — 시니어 AI 강의 자료 연계

---

## 📌 현재까지 합의된 사항

### 개발 원칙
> **"일단 돌아가게 → 제대로 돌아가게 → 빠르게 돌아가게"**

### 구현 순서 (Phase별)
1. **Phase 1**: 기본 벡터 검색 + 한국어 임베딩 + Streamlit UI
2. **Phase 2**: Hybrid Search (BM25+벡터) + Multi-Query 변환
3. **Phase 3**: Re-ranking + Parent-Child 청킹 + Contextual Compression

### UI 결정
- **카카오톡 스타일** Streamlit 챗봇
  - 배경: `#b2c7d9` (카카오톡 파란빛 회색)
  - 봇 말풍선: 흰색, 왼쪽
  - 유저 말풍선: `#ffe812` 노란색, 오른쪽
  - 시간, 날짜 구분선 포함

### 검색 품질 향상 6가지 전략 (유튜브 콘텐츠 아이디어)
1. Hybrid Search (BM25 + 벡터)
2. Query Transformation (Multi-Query / HyDE / Step-Back)
3. Re-ranking (Cohere / BGE)
4. FAQ 특화 청킹 (Parent-Child)
5. 한국어 특화 임베딩
6. Contextual Compression

---

## 🔧 핵심 파일 역할

| 파일 | 역할 | Phase |
|------|------|-------|
| `src/notion_loader.py` | Notion API → FAQ 파싱 | 1 |
| `src/embeddings.py` | 임베딩 & ChromaDB 저장/검색 | 1→2 |
| `src/rag_chain.py` | RAG 로직 & Claude 답변 생성 | 1→3 |
| `src/app.py` | 카카오톡 스타일 Streamlit UI | 1 |
| `tests/test_rag.py` | 파이프라인 테스트 | 1 |

---

## 🚀 다음 할 일 (Next Steps)

```
[ ] 1. Python 가상환경 생성 및 requirements.txt 설치
[ ] 2. .env 파일에 API 키 입력 (.env.example 참고)
[ ] 3. Notion FAQ 페이지 준비 및 PAGE_ID 확인
[ ] 4. python src/embeddings.py 로 인덱싱 테스트
[ ] 5. streamlit run src/app.py 로 챗봇 실행
[ ] 6. Phase 2 Hybrid Search 구현
```

---

## 💡 유튜브 콘텐츠 연계 메모

- 채널명: **찰리초이 스토리**
- 타깃: 중장년층
- 예정 콘텐츠: "RAG 챗봇 검색 품질을 높이는 6가지 방법"
- 개발 과정 자체를 시연 영상으로 활용 가능
