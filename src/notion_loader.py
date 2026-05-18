"""
notion_loader.py
─────────────────
Phase 1: Notion 페이지에서 FAQ 데이터를 추출하고 파싱하는 모듈

실행 방법:
    python src/notion_loader.py
"""

import os
from notion_client import Client
from dotenv import load_dotenv

load_dotenv()

# ── Notion 클라이언트 초기화 ──────────────────────────────
notion = Client(auth=os.getenv("NOTION_API_KEY"))
PAGE_ID = os.getenv("NOTION_PAGE_ID")


def get_page_blocks(page_id: str) -> list:
    """Notion 페이지의 모든 블록을 가져옵니다."""
    blocks = []
    cursor = None

    while True:
        response = notion.blocks.children.list(
            block_id=page_id,
            start_cursor=cursor,
            page_size=100,
        )
        blocks.extend(response["results"])
        if not response.get("has_more"):
            break
        cursor = response["next_cursor"]

    return blocks


def extract_text_from_block(block: dict) -> str:
    """블록에서 텍스트를 추출합니다."""
    block_type = block.get("type", "")
    text_content = ""

    # 텍스트가 있는 블록 타입들 처리
    text_types = [
        "paragraph", "heading_1", "heading_2", "heading_3",
        "bulleted_list_item", "numbered_list_item", "toggle", "quote"
    ]

    if block_type in text_types:
        rich_text = block.get(block_type, {}).get("rich_text", [])
        text_content = "".join([t.get("plain_text", "") for t in rich_text])

    return text_content.strip()


def parse_faq_from_blocks(blocks: list) -> list[dict]:
    """
    블록 리스트에서 Q&A 쌍을 파싱합니다.

    지원 형식:
    - Q: 질문 / A: 답변 형식
    - heading + paragraph 형식
    - toggle 블록 형식 (추후 확장)
    """
    faq_list = []
    current_question = None
    current_answer_lines = []

    for block in blocks:
        text = extract_text_from_block(block)
        if not text:
            continue

        block_type = block.get("type", "")

        # ── Q: 로 시작하는 질문 ──
        if text.upper().startswith("Q:") or text.upper().startswith("질문:"):
            # 이전 Q&A 저장
            if current_question and current_answer_lines:
                faq_list.append({
                    "question": current_question,
                    "answer": " ".join(current_answer_lines).strip(),
                })
            current_question = text.split(":", 1)[-1].strip()
            current_answer_lines = []

        # ── A: 로 시작하는 답변 ──
        elif text.upper().startswith("A:") or text.upper().startswith("답변:"):
            answer_text = text.split(":", 1)[-1].strip()
            current_answer_lines.append(answer_text)

        # ── heading을 질문으로 사용하는 경우 ──
        elif block_type in ["heading_1", "heading_2", "heading_3"]:
            if current_question and current_answer_lines:
                faq_list.append({
                    "question": current_question,
                    "answer": " ".join(current_answer_lines).strip(),
                })
            current_question = text
            current_answer_lines = []

        # ── paragraph를 답변으로 사용하는 경우 ──
        elif block_type == "paragraph" and current_question:
            current_answer_lines.append(text)

    # 마지막 Q&A 저장
    if current_question and current_answer_lines:
        faq_list.append({
            "question": current_question,
            "answer": " ".join(current_answer_lines).strip(),
        })

    return faq_list


def load_faq_from_notion() -> list[dict]:
    """Notion 페이지에서 FAQ 데이터를 로드합니다."""
    print(f"📥 Notion 페이지 데이터 로딩 중... (PAGE_ID: {PAGE_ID})")

    blocks = get_page_blocks(PAGE_ID)
    print(f"   ✅ {len(blocks)}개 블록 추출 완료")

    faq_list = parse_faq_from_blocks(blocks)
    print(f"   ✅ {len(faq_list)}개 FAQ 파싱 완료")

    # 파싱 결과 미리보기
    print("\n📋 FAQ 미리보기:")
    for i, faq in enumerate(faq_list[:3], 1):
        print(f"  [{i}] Q: {faq['question'][:50]}...")
        print(f"       A: {faq['answer'][:80]}...")

    return faq_list


# ── 직접 실행 시 테스트 ──────────────────────────────────
if __name__ == "__main__":
    faqs = load_faq_from_notion()
    print(f"\n🎯 총 {len(faqs)}개 FAQ 로드 완료!")
