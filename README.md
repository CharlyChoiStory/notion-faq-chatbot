# 🏥 성형외과 FAQ RAG 챗봇

> 로컬 문서 업로드 기반 RAG FAQ 챗봇 데모 시스템  
> 대상 샘플: `~/Desktop/plastic_surgery_faq_knowledge_base.md`

---

## 🎯 프로젝트 개요

- **목적**: 성형외과 FAQ/규정집 문서를 업로드하면 자동으로 파싱하고 벡터 DB를 구축하여 상담 FAQ 챗봇으로 활용
- **데모 목적**: RAG 시스템 구축 과정을 교육용으로 보여주는 실습 프로젝트
- **데이터 소스**: Notion 연결 취소. 로컬 `md`, `txt`, `pdf`, `docx` 파일 업로드 방식 사용
- **주의**: 진단, 처방, 수술 가능 여부, 부작용 판단, 결과 보장은 하지 않는 FAQ 안내용 데모 시스템

---

## 🏗️ 아키텍처

```text
[로컬 문서 업로드]
  md / txt / pdf / docx
        ↓
[텍스트 추출]
        ↓
[FAQ-001 구조 자동 파싱 또는 섹션 청킹]
        ↓
[가벼운 성형외과 업무 온톨로지 자동 태깅]
  built-in rules + data/uploads/plastic_surgery_ontology_sample.md
        ↓
[OpenAI text-embedding-3-small]
        ↓
[Vector DB]
  - local: ChromaDB
  - cloud: Supabase Postgres + pgvector
        ↓
[사용자 질문]
        ↓
[온톨로지 기반 질문 확장 + 벡터 검색]
        ↓
[OpenAI ChatGPT 답변 생성]
        ↓
[Streamlit 카카오톡 스타일 UI]
```

---

## 🛠️ 기술 스택

- 데이터 소스: 로컬 파일 업로드 (`md`, `txt`, `pdf`, `docx`)
- 문서 파싱: 자체 `local_loader.py`, `pypdf`, `python-docx`
- 임베딩: OpenAI `text-embedding-3-small`
- 벡터 DB: ChromaDB 또는 Supabase Postgres + pgvector
- LLM: OpenAI `gpt-4o-mini`
- UI: Streamlit
- 지식 구조화: Lightweight Business Ontology

---

## 📁 프로젝트 구조

```text
notion-faq-chatbot/
├── README.md
├── .env.example
├── requirements.txt
├── src/
│   ├── local_loader.py        # 로컬 md/txt/pdf/docx 추출 및 FAQ 파싱
│   ├── ontology.py            # 성형외과 업무 온톨로지 자동 태깅
│   ├── embeddings.py          # 임베딩 & ChromaDB/Supabase Vector DB 저장/검색
│   ├── rag_chain.py           # RAG 검색 → 프롬프트 → ChatGPT 답변
│   ├── app.py                 # Streamlit 챗봇 UI
│   └── notion_loader.py       # 이전 Notion 연동 파일, 현재 데모에서는 미사용
├── data/
│   ├── uploads/               # 업로드된 원본 문서
│   └── chroma_db/             # 로컬 벡터 DB 저장소
└── tests/
    ├── test_local_loader.py
    ├── test_ontology.py
    └── test_rag.py
```

---

## 🧠 성형외과 업무 온톨로지 자동 적용

FAQ를 벡터 DB에 저장할 때 `src/ontology.py`가 자동으로 업무 유형과 정책 조건을 태깅합니다.

외부 온톨로지 소스:

```text
~/Desktop/plastic_surgery_ontology_sample.md
```

이 md 파일 안의 JSON 코드블록에서 다음 정보를 자동 추출해 기본 규칙과 병합합니다.

- `procedure_categories`: 눈성형, 코성형, 필러, 보톡스, 리프팅, 지방흡입/지방이식
- `question_types`: 예약문의, 비용문의, 수술전준비, 수술후관리, 부작용의심, 서류문의, 환불취소문의
- `symptom_risk_levels`: low / medium / high 증상 위험도
- `routing_rules`: 즉시 병원 연락, 응급실 안내, 상담실 연결 등
- `answer_policies`: 반드시 지킬 답변 원칙과 금지 표현

자동 감지 업무 유형:

- 진료시간
- 예약/상담
- 위치/주차
- 수술/시술 전 준비
- 수술/시술 후 주의사항
- 붓기/멍/회복
- 실밥/내원 일정
- 비용/비급여
- 서류/증명서
- 응급/부작용 의심
- 개인정보/사진 제한
- 수술/시술 항목

자동 태깅 항목:

- `ontology_domain`
- `ontology_label`
- `policy_stage`
- `policy_target`
- `policy_period`
- `policy_exceptions`
- `policy_channels`
- `requires_human_review`
- `medical_risk_level`
- `routing_rule_id`
- `routing_action`
- `recommended_response`
- `forbidden_response`
- `ontology_source`

주의: 이 온톨로지는 공식 의료 판단기가 아니라 교육용/데모용 자동 태깅 도우미입니다.

---

## 🚀 빠른 시작

### 1. 환경 설정

```bash
cd ~/Desktop/notion-faq-chatbot
source .venv/bin/activate
```

처음 설치가 필요한 경우:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. OpenAI API Key 설정

```bash
cp .env.example .env
```

`.env`에 다음 값을 입력합니다.

```bash
OPENAI_API_KEY=sk-...
OPENAI_CHAT_MODEL=gpt-4o-mini
```

### 3. 샘플 문서 파싱 테스트

```bash
python src/local_loader.py
```

기대 결과:

```text
loaded_faq_count=82
FAQ-001 병원 진료시간이 어떻게 되나요?
...
```

### 4. Streamlit 앱 실행

```bash
streamlit run src/app.py
```

앱에서 다음 중 하나를 선택합니다.

- `🧪 데스크탑 샘플 FAQ로 구축`
- 직접 `md/pdf/txt/docx` 파일 업로드 후 `📚 업로드 문서로 벡터 DB 구축`

---

## ✅ 검증 명령

```bash
python -m py_compile src/*.py tests/*.py
python tests/test_local_loader.py
python tests/test_ontology.py
python tests/test_indexing.py
```

---

## 📌 현재 개발 현황

- [x] Notion 연결 제거
- [x] 로컬 md/txt/pdf/docx 업로드 구조 구현
- [x] 성형외과 샘플 FAQ md 파싱
- [x] FAQ-001 구조 자동 Q/A 파싱
- [x] 일반 문서 섹션 청킹 fallback
- [x] 가벼운 성형외과 업무 온톨로지 태깅
- [x] 데스크탑 `plastic_surgery_ontology_sample.md` 외부 온톨로지 자동 적용
- [x] 의료 위험도/라우팅 규칙/금지응답/권장응답 메타데이터 적용
- [x] OpenAI 임베딩 + ChatGPT 답변 구조로 정리
- [x] Streamlit UI에서 문서 업로드/벡터 DB 구축 버튼 제공

---

## ⚠️ 의료/상담 안전 문구

이 시스템은 성형외과 고객응대 FAQ 데모입니다.  
진단, 처방, 수술 가능 여부, 부작용 판단, 결과 보장을 하지 않습니다.  
심한 통증, 지속적인 출혈, 호흡곤란, 고열, 갑작스러운 시야 이상 등은 즉시 병원 또는 가까운 응급실에 문의해야 합니다.
