# 03. 로컬 세팅 방법

## 1. 프로젝트 복사/클론

GitHub에서 받을 경우:

```bash
git clone <GITHUB_REPO_URL>
cd notion-faq-chatbot
```

zip으로 받을 경우:

```bash
unzip notion-faq-chatbot.zip
cd notion-faq-chatbot
```

## 2. Python 가상환경 생성

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 3. 패키지 설치

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

중요:

```text
openai==1.35.0
httpx==0.27.2
```

`httpx==0.28.x`에서는 다음 오류가 발생할 수 있습니다.

```text
Client.__init__() got an unexpected keyword argument 'proxies'
```

## 4. 환경변수 설정

```bash
cp .env.example .env
```

`.env`에 본인의 OpenAI API Key를 입력합니다.

```bash
OPENAI_API_KEY=sk-...
OPENAI_CHAT_MODEL=gpt-4o-mini
```

주의: `.env`는 Git에 올리지 않습니다.

## 5. 앱 실행

```bash
streamlit run src/app.py
```

또는 현재 프로젝트 기준:

```bash
.venv/bin/streamlit run src/app.py --server.port 8501 --server.address 0.0.0.0
```

브라우저:

```text
http://localhost:8501
```

## 6. 사용 방법

1. 왼쪽 사이드바에서 FAQ 문서 업로드
2. 자동 구축 완료 메시지 확인
3. 하단 입력창에 질문 입력

예시 질문:

```text
상담 예약은 어떻게 하나요?
쌍꺼풀 비용은 얼마인가요?
수술 후 피가 나면 어떻게 해야 하나요?
```
