# AI미인 성형외과 FAQ RAG 챗봇 재개발 문서 세트

이 문서 세트는 다른 컴퓨터에서 현재 프로젝트를 재개발/복원하기 위한 안내서입니다.

## 문서 목록

1. `01_PROJECT_OVERVIEW.md` — 프로젝트 목적과 현재 완성 상태
2. `02_ARCHITECTURE.md` — 전체 아키텍처와 데이터 흐름
3. `03_LOCAL_SETUP.md` — 새 컴퓨터에서 로컬 실행하는 방법
4. `04_DATA_AND_ONTOLOGY.md` — FAQ 문서와 성형외과 온톨로지 적용 방식
5. `05_UI_REQUIREMENTS.md` — 현재 UI/UX 요구사항
6. `06_TESTING_CHECKLIST.md` — 셀프 테스트 명령과 기대 결과
7. `07_GITHUB_AND_DEPLOYMENT.md` — GitHub push 및 배포 절차
8. `08_TROUBLESHOOTING.md` — 지금까지 발생한 오류와 해결법
9. `09_FILE_INVENTORY.md` — 핵심 파일 역할 목록
10. `10_SUPABASE_VECTOR_DB.md` — Supabase pgvector 클라우드 Vector DB 전환 가이드

## 보안 주의

- 실제 `.env`와 `OPENAI_API_KEY`는 zip에 포함하지 않습니다.
- 다른 컴퓨터에서는 `.env.example`을 복사해 `.env`를 만들고 본인의 API Key를 넣어야 합니다.
