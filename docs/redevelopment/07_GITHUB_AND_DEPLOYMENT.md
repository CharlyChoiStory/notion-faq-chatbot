# 07. GitHub와 배포 절차

## 현재 상황

이 프로젝트 폴더는 처음에는 Git 저장소가 아니었습니다. 다른 컴퓨터로 이전하거나 GitHub에 올리려면 먼저 Git 초기화가 필요합니다.

## Git 초기화

```bash
git init
git branch -M main
git add .
git commit -m "feat: add plastic surgery FAQ RAG chatbot demo"
```

## GitHub 저장소 생성 후 push

GitHub CLI가 있는 경우:

```bash
gh auth login
gh repo create ai-beauty-clinic-faq-rag --private --source . --push
```

또는 public으로 만들려면:

```bash
gh repo create ai-beauty-clinic-faq-rag --public --source . --push
```

GitHub 웹에서 빈 저장소를 만든 경우:

```bash
git remote add origin https://github.com/<USER>/<REPO>.git
git push -u origin main
```

## Git에 포함하면 안 되는 파일

`.gitignore`에 이미 포함되어야 합니다.

```text
.env
.venv/
__pycache__/
data/chroma_db/
.DS_Store
```

## Vercel 배포 주의

현재 앱은 Streamlit 서버 앱입니다. Vercel은 기본적으로 Next.js/정적 사이트/서버리스 함수에 최적화되어 있어 Streamlit 장기 실행 서버 배포에는 적합하지 않습니다.

권장 배포 옵션:

1. Streamlit Community Cloud
2. Hugging Face Spaces
3. Render
4. Railway
5. Fly.io
6. VM 또는 로컬 서버

## Vercel에 꼭 등록해야 하는 경우

Vercel에는 프로젝트 소개용 랜딩 페이지 또는 API wrapper를 등록하고, 실제 Streamlit 앱은 별도 호스팅으로 연결하는 방식을 권장합니다.

Vercel CLI 설치:

```bash
npm install -g vercel
vercel login
```

등록:

```bash
vercel
```

환경변수 설정:

```bash
vercel env add OPENAI_API_KEY
vercel env add OPENAI_CHAT_MODEL
```

주의: Streamlit 앱을 그대로 Vercel에 배포하면 런타임 제약 때문에 정상 동작하지 않을 수 있습니다.
