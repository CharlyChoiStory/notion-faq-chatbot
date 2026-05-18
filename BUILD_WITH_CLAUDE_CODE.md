# Claude Code로 재빌드/이어받기 안내

이 ZIP은 **성형외과 AI 상담 코디네이터 / RAG FAQ 챗봇** 프로젝트를 다른 컴퓨터에서 다시 실행하거나 Claude Code로 이어 개발할 수 있도록 정리한 패키지입니다.

## 1. 포함된 핵심 기능

- Streamlit 기반 로컬 웹앱
- 로컬 FAQ 문서 업로드 및 파싱
- ChromaDB 벡터 검색 기반 RAG
- OpenAI ChatGPT 답변 생성
- OpenAI API Key가 없을 때도 일부 데모 fallback 답변 제공
- AI 상담 코디네이터 톤앤매너
- 가격/견적 문의 금액 노출 차단
- 상담원 핸드오프 링크 및 상담원 전용 요약 페이지
- 고객 발화 분석: 관심 부위, 희망 변화, 걱정 요소, 희망 일정, 긴급도
- 보톡스/주차장 등 일반 질문의 과잉 상담원 연결 방지
- 채팅 말풍선 HTML 태그 노출 방지

## 2. ZIP에서 제외한 항목

보안과 이식성을 위해 아래는 포함하지 않았습니다.

- `.env` : 실제 OpenAI API Key 등 민감정보
- `.venv/` : 로컬 가상환경
- `.git/` : Git 내부 이력
- `data/chroma_db/` : 실행 중 재생성되는 벡터DB
- `data/counselor_cases/` : 로컬 테스트 중 생성된 상담 케이스 로그
- `__pycache__/`, `.DS_Store`, `.vercel/` 등 캐시/로컬 설정

## 3. 다른 컴퓨터에서 실행하기

터미널에서 ZIP을 푼 뒤 프로젝트 폴더로 이동합니다.

```bash
cd notion-faq-chatbot
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
```

`.env` 파일을 열어 OpenAI API Key를 입력합니다.

```bash
OPENAI_API_KEY=sk-...
OPENAI_CHAT_MODEL=gpt-4o-mini
```

로컬 실행:

```bash
streamlit run src/app.py \
  --server.port 8501 \
  --server.address 127.0.0.1 \
  --server.headless true \
  --server.enableCORS false \
  --server.enableXsrfProtection false \
  --browser.gatherUsageStats false
```

브라우저에서 접속:

```text
http://127.0.0.1:8501
```

## 4. FAQ 지식베이스 구축

앱 왼쪽 사이드바에서 FAQ 문서를 업로드하면 자동으로:

1. 문서 저장
2. FAQ 파싱
3. 온톨로지/정책 태깅
4. ChromaDB 벡터 인덱스 생성

이 진행됩니다.

샘플 문서는 `data/uploads/` 안에 포함했습니다. 다른 컴퓨터에서 앱을 띄운 뒤 사이드바에 다시 업로드하면 됩니다.

## 5. 테스트 실행

```bash
source .venv/bin/activate
python -m py_compile src/*.py tests/*.py
python tests/test_counselor.py
python tests/test_ontology.py
```

현재 기준 통과 상태:

- `test_counselor.py`: 10/10
- `test_ontology.py`: 8/8

## 6. Claude Code에 줄 첫 지시문 예시

Claude Code를 프로젝트 루트에서 열고 아래처럼 지시하면 됩니다.

```text
이 프로젝트는 성형외과 AI 상담 코디네이터/RAG FAQ 챗봇입니다.
먼저 README.md, CLAUDE.md, BUILD_WITH_CLAUDE_CODE.md를 읽고 구조를 파악하세요.
목표는 로컬 실행 가능한 Streamlit 앱을 유지하면서 다음 제약을 반드시 지키는 것입니다.

1. 고객에게 “FAQ에서 찾을 수 없습니다” 같은 내부 RAG 실패 문구를 노출하지 마세요.
2. 가격/견적 문의에는 구체적인 금액을 절대 노출하지 말고 상담원 연결로 유도하세요.
3. 주차장/위치/진료시간 같은 일반 문의에는 상담원 연결 링크를 붙이지 마세요.
4. 보톡스 같은 단순 시술명 질문에는 일반 안내를 제공하고 무조건 상담원 연결하지 마세요.
5. 채팅 말풍선에서 </div> 같은 HTML 태그가 고객 화면에 노출되지 않게 유지하세요.
6. 수정 후 반드시 tests/test_counselor.py와 tests/test_ontology.py를 실행해 회귀를 확인하세요.
7. GitHub push나 외부 터널/배포는 사용자가 명시적으로 지시하기 전까지 하지 마세요.
```

## 7. 주요 파일

- `src/app.py`  
  Streamlit UI, 채팅 화면, 상담원 전용 페이지 라우팅/렌더링

- `src/rag_chain.py`  
  RAG 검색, OpenAI 답변 생성, 가격 필터링, 상담원 핸드오프 판정, 일반 fallback 답변

- `src/counselor.py`  
  고객 발화 분석 및 상담 케이스 JSON 생성/로드

- `src/embeddings.py`  
  FAQ 벡터 인덱스 구축 및 검색

- `src/local_loader.py`  
  md/txt/pdf/docx FAQ 문서 로딩/파싱

- `src/ontology.py`  
  성형외과 FAQ 정책/위험도/라우팅 메타데이터 처리

- `tests/test_counselor.py`  
  상담원 연결, 가격 차단, 보톡스/주차장 회귀 테스트

- `tests/test_ontology.py`  
  온톨로지/정책 라우팅 테스트

## 8. 최근 중요한 수정 이력 요약

- 상담원 핸드오프 요약 기능 추가
- 가격/견적 문의 금액 노출 차단
- 상담원 대시보드 카드형 UI 개선
- 보톡스 질문이 엉뚱한 FAQ에 끌려 상담원 연결되는 문제 수정
- 주차장 같은 일반 문의에 상담원 링크가 붙는 문제 수정
- Streamlit 채팅 말풍선에서 HTML 닫는 태그가 노출되는 문제 수정

## 9. 운영상 주의

- 이 앱은 의료 진단 도구가 아니라 **AI 상담 코디네이터 데모**입니다.
- 진단, 처방, 수술 가능 여부, 부작용 판단, 결과 보장 표현은 피해야 합니다.
- 실제 병원 운영 적용 전에는 의료광고/개인정보/상담 기록 보관 정책 검토가 필요합니다.
- 현재 패키지는 로컬 테스트용입니다. 외부 공개/배포는 별도 승인 후 진행하세요.
