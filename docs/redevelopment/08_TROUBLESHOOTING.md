# 08. 트러블슈팅

## 1. 업로드 후 자동 구축 오류: `proxies`

오류:

```text
Client.__init__() got an unexpected keyword argument 'proxies'
```

원인:

```text
openai==1.35.0
httpx==0.28.x
```

해결:

```bash
pip install 'httpx==0.27.2'
```

`requirements.txt`에도 다음을 고정합니다.

```text
openai==1.35.0
httpx==0.27.2
```

## 2. API Key 오류

오류:

```text
OPENAI_API_KEY가 설정되어 있지 않습니다
```

해결:

```bash
cp .env.example .env
```

`.env`에 입력:

```bash
OPENAI_API_KEY=sk-...
OPENAI_CHAT_MODEL=gpt-4o-mini
```

## 3. 사이드바 글자가 안 보임

원인:

Streamlit sidebar 전체에 흰색 텍스트 CSS가 적용되어 file uploader 내부 글자까지 흰색으로 상속됨.

해결:

`stFileUploaderDropzone`, Browse files 버튼, 관련 label에 별도 CSS로 검정 텍스트를 강제합니다.

## 4. 답변에 `참조 기준`이 표시됨

원인:

프롬프트에 참조 기준을 표시하라는 지시가 있었음.

해결:

- 프롬프트에서 해당 지시 제거
- 내부 메타데이터 표시 금지 지시 추가
- `clean_public_answer()`로 후처리하여 `참조 기준:` 라인 삭제

## 5. 출처/검색 결과 카드가 표시됨

원인:

`app.py`에서 `sources_html`을 만들어 답변 하단에 렌더링함.

해결:

사용자용 UI에서는 `sources_html` 렌더링 제거. 내부적으로는 `sources`를 세션에 저장할 수 있지만 화면에는 표시하지 않습니다.

## 6. ChromaDB Telemetry Warning

메시지:

```text
Failed to send telemetry event ...
```

이것은 ChromaDB telemetry 관련 warning입니다. 테스트 exit code가 0이면 기능 오류가 아닙니다.

## 7. 샘플 FAQ 파일 경로 문제

과거 테스트는 데스크탑의 다음 파일만 봤습니다.

```text
~/Desktop/plastic_surgery_faq_knowledge_base.md
```

현재는 업로드 저장 경로도 fallback으로 봅니다.

```text
data/uploads/plastic_surgery_faq_knowledge_base.md
```
