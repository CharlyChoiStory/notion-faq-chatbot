# 01. 프로젝트 개요

## 프로젝트명

**AI미인 성형외과 FAQ RAG 챗봇**

## 목적

성형외과 FAQ 문서를 업로드하면 자동으로 지식베이스를 구축하고, 사용자가 자연어로 질문하면 FAQ 기반으로 답변하는 교육용 RAG 데모 시스템입니다.

## 핵심 목표

- Notion API 없이 로컬 문서 기반으로 동작
- `md`, `txt`, `pdf`, `docx` 업로드 지원
- 업로드 즉시 자동 파싱 → 온톨로지 태깅 → ChromaDB 인덱싱
- OpenAI 임베딩과 ChatGPT 답변 생성 사용
- 성형외과 의료 안전 규칙 적용
- 일반 사용자에게 내부 검색 결과/정책 메타데이터를 노출하지 않는 깔끔한 UI

## 현재 상태

- Streamlit 앱 실행 URL: `http://localhost:8501`
- 병원명 상단 표시: `AI미인 성형외과`
- 파일 업로드 즉시 자동 벡터DB 구축
- 답변 하단의 출처/유사도/정책 메타데이터 카드 제거 완료
- `참조 기준: 정책유형=...` 문구 제거 완료
- OpenAI/httpx 버전 호환 문제 해결 완료

## 기술 스택

- Python 3.11
- Streamlit
- ChromaDB
- OpenAI API
  - Embedding: `text-embedding-3-small`
  - Chat: `gpt-4o-mini`
- pypdf
- python-docx
- python-dotenv

## 의료 안전 원칙

이 앱은 교육용 FAQ 안내/상담 라우팅 데모입니다. 진단, 처방, 수술 가능 여부 판단, 부작용 판단, 결과 보장은 하지 않습니다. 심한 통증, 지속 출혈, 호흡곤란, 고열, 시야 이상 등은 병원 또는 응급실 문의를 우선 안내합니다.
