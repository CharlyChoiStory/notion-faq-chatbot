# 06. 테스트 체크리스트

## 문법 검사

```bash
.venv/bin/python -m py_compile src/*.py tests/*.py
```

기대 결과:

```text
exit_code=0
```

## 로컬 문서 파싱 테스트

```bash
.venv/bin/python tests/test_local_loader.py
```

기대 결과:

```text
결과: 4/4 통과
```

## 온톨로지 테스트

```bash
.venv/bin/python tests/test_ontology.py
```

기대 결과:

```text
결과: 8/8 통과
```

## ChromaDB 인덱싱 테스트, API 없는 테스트 모드

```bash
RAG_TEST_EMBEDDINGS=1 .venv/bin/python tests/test_indexing.py
```

기대 결과:

```text
결과: 1/1 통과
```

## OpenAI 임베딩 Smoke Test

실제 OpenAI API Key가 있는 경우:

```bash
CHROMA_DB_PATH=/tmp/rag_openai_smoke_db \
CHROMA_COLLECTION_NAME=smoke_openai_upload \
.venv/bin/python - <<'PY'
import sys, shutil
sys.path.insert(0, 'src')
from embeddings import build_index, search_faq
shutil.rmtree('/tmp/rag_openai_smoke_db', ignore_errors=True)
faqs = [{
    'question': '상담 예약은 어떻게 하나요?',
    'answer': '상담 예약은 전화, 카카오톡, 네이버 예약으로 가능합니다.',
    'source': 'smoke_test.md',
    'faq_id': 'SMOKE-001',
    'tags': '상담예약',
}]
build_index(faqs, reset=True)
res = search_faq('상담 예약 방법 알려주세요', top_k=1)
print('smoke_result_count=', len(res))
print('top_question=', res[0]['question'] if res else 'NONE')
PY
```

기대 결과:

```text
smoke_result_count= 1
top_question= 상담 예약은 어떻게 하나요?
```

## UI 확인

브라우저에서 확인:

```text
http://localhost:8501
```

체크리스트:

- [ ] 상단 중앙에 `AI미인 성형외과` 표시
- [ ] 사이드바에 파일 업로드만 단순 표시
- [ ] 파일 업로드 시 자동 구축 완료 메시지 표시
- [ ] 답변 아래에 출처/유사도/정책 카드가 표시되지 않음
- [ ] 답변에 `참조 기준:` 문구가 표시되지 않음
