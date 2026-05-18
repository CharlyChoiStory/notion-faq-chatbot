# 🔑 API 설정 가이드

> 프로젝트에 필요한 API 키 발급 및 설정 방법

---

## 필요한 API 키 목록

| API | 용도 | 무료 여부 |
|-----|------|-----------|
| Notion API | FAQ 데이터 추출 | ✅ 무료 |
| OpenAI API | 임베딩 생성 | 💰 유료 (소량 무료) |
| Anthropic API | Claude 답변 생성 | 💰 유료 |

---

## 1️⃣ Notion API 키 발급

### 단계별 방법
1. [Notion Developers](https://www.notion.so/my-integrations) 접속
2. **"New integration"** 클릭
3. 이름 입력 (예: `faq-chatbot`)
4. Workspace 선택 후 **Submit**
5. **"Internal Integration Token"** 복사 → `.env`에 저장

### Notion 페이지 연동
1. 연동할 Notion 페이지 열기
2. 우측 상단 `···` 메뉴 클릭
3. **"Connect to"** → 방금 만든 Integration 선택
4. 페이지 URL에서 ID 복사
   ```
   https://notion.so/페이지이름-{PAGE_ID}
                                ↑ 이 부분이 PAGE_ID
   ```

---

## 2️⃣ OpenAI API 키 발급

1. [OpenAI Platform](https://platform.openai.com) 접속 및 로그인
2. 우측 상단 프로필 → **"API Keys"**
3. **"Create new secret key"** 클릭
4. 키 복사 → `.env`에 저장

> ⚠️ 키는 생성 시 한 번만 표시되므로 반드시 즉시 복사!

---

## 3️⃣ Anthropic (Claude) API 키 발급

1. [Anthropic Console](https://console.anthropic.com) 접속 및 로그인
2. 좌측 메뉴 **"API Keys"** 클릭
3. **"Create Key"** 클릭
4. 키 복사 → `.env`에 저장

---

## 4️⃣ .env 파일 설정

프로젝트 루트의 `.env` 파일에 아래 형식으로 입력:

```env
# Notion
NOTION_API_KEY=secret_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
NOTION_PAGE_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# OpenAI
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Anthropic (Claude)
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

---

## ⚠️ 보안 주의사항

- `.env` 파일은 절대 GitHub에 올리지 않기
- `.gitignore`에 `.env` 추가 확인
- API 키는 타인과 공유하지 않기
- 키가 유출된 경우 즉시 해당 플랫폼에서 삭제 후 재발급

---

## 💰 예상 비용 (소규모 FAQ 기준)

| 항목 | 예상 비용 |
|------|-----------|
| OpenAI 임베딩 (1회성 인덱싱) | $0.01 미만 |
| Claude API (테스트 포함) | $1~5 |
| 합계 | 약 $5 이하 |
