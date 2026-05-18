"""
ontology.py
───────────
가벼운 업무 온톨로지(Lightweight Business Ontology) 모듈.

목적:
- FAQ 원문을 벡터DB에 넣기 전에 고객센터 핵심 용어/정책 조건을 자동 태깅
- 사용자 질문을 표준 용어 중심으로 확장하여 검색 품질 보강
- RAG 답변에 "이 답변이 어떤 정책 유형/조건에 근거했는지" 표시

주의:
- 이 모듈은 공식 정책 판정기가 아니라 교육용/데모용 자동 태깅 도우미입니다.
- 확신도가 낮거나 복수 domain이 감지되면 requires_review=True로 표시합니다.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable, Any


@dataclass(frozen=True)
class TermRule:
    key: str
    label: str
    definition: str
    synonyms: tuple[str, ...]
    related: tuple[str, ...] = ()


TERMS: dict[str, TermRule] = {
    "clinic_hours": TermRule(
        key="clinic_hours",
        label="진료시간",
        definition="병원 운영 시간, 휴진일, 상담 가능 시간 안내",
        synonyms=("진료시간", "영업시간", "운영시간", "몇 시", "토요일", "휴진", "공휴일", "오늘 영업"),
        related=("reservation",),
    ),
    "reservation": TermRule(
        key="reservation",
        label="예약/상담",
        definition="상담 예약, 당일 상담, 예약 변경, 예약 취소 안내",
        synonyms=("예약", "상담", "당일 상담", "예약 변경", "예약 취소", "방문", "초진", "재진", "카톡 예약", "네이버 예약"),
        related=("clinic_hours", "location"),
    ),
    "location": TermRule(
        key="location",
        label="위치/주차",
        definition="병원 위치, 교통, 주차, 찾아오는 길 안내",
        synonyms=("위치", "주소", "어디", "찾아", "주차", "교통", "지하철", "건물"),
        related=("reservation",),
    ),
    "pre_care": TermRule(
        key="pre_care",
        label="수술/시술 전 준비",
        definition="수술 또는 시술 전 금식, 약물, 음주, 흡연, 준비사항 안내",
        synonyms=("수술 전", "시술 전", "준비", "금식", "약", "복용", "음주", "흡연", "화장", "렌즈"),
        related=("post_care", "procedure"),
    ),
    "post_care": TermRule(
        key="post_care",
        label="수술/시술 후 주의사항",
        definition="수술 또는 시술 후 관리, 회복, 세안, 운동, 음주, 흡연 등 일반 주의사항",
        synonyms=("수술 후", "시술 후", "주의사항", "회복", "세안", "운동", "샤워", "음주", "흡연", "찜질"),
        related=("pre_care", "emergency"),
    ),
    "swelling_bruise": TermRule(
        key="swelling_bruise",
        label="붓기/멍/회복",
        definition="붓기, 멍, 통증 등 회복 과정의 일반 안내",
        synonyms=("붓기", "부기", "멍", "통증", "회복", "흉터", "빨개", "부었", "아파"),
        related=("post_care", "emergency"),
    ),
    "stitches": TermRule(
        key="stitches",
        label="실밥/내원 일정",
        definition="실밥 제거, 소독, 경과 확인, 사후 내원 일정 안내",
        synonyms=("실밥", "실밥 제거", "소독", "경과", "내원", "재방문", "체크"),
        related=("post_care",),
    ),
    "cost": TermRule(
        key="cost",
        label="비용/비급여",
        definition="상담 전 예상 비용 범위와 비급여 항목 안내",
        synonyms=("비용", "가격", "얼마", "비급여", "견적", "수술비", "시술비", "할인", "이벤트"),
        related=("reservation",),
    ),
    "documents": TermRule(
        key="documents",
        label="서류/증명서",
        definition="진료확인서, 영수증, 세부내역서 등 서류 발급 안내",
        synonyms=("서류", "증명서", "진료확인서", "영수증", "세부내역서", "보험", "실비", "제증명"),
        related=("privacy",),
    ),
    "emergency": TermRule(
        key="emergency",
        label="응급/부작용 의심",
        definition="심한 통증, 출혈, 고열, 시야 이상 등 즉시 병원 또는 응급실 연결이 필요한 상황",
        synonyms=("응급", "부작용", "출혈", "피가", "고열", "염증", "호흡곤란", "시야", "감염", "심한 통증", "열이"),
        related=("post_care",),
    ),
    "privacy": TermRule(
        key="privacy",
        label="개인정보/사진 제한",
        definition="주민등록번호, 신분증, 얼굴 사진, 카드번호 등 민감정보 입력 제한 안내",
        synonyms=("개인정보", "주민등록번호", "신분증", "사진", "얼굴 사진", "카드번호", "계좌번호", "처방전"),
        related=("documents",),
    ),
    "procedure": TermRule(
        key="procedure",
        label="수술/시술 항목",
        definition="눈, 코, 윤곽, 리프팅, 보톡스, 필러 등 시술/수술 항목의 일반 상담 안내",
        synonyms=("눈", "코", "윤곽", "리프팅", "보톡스", "필러", "쌍꺼풀", "눈매교정", "코수술", "재수술", "지방이식"),
        related=("reservation", "pre_care", "post_care"),
    ),
    "refund": TermRule(
        key="refund",
        label="환불",
        definition="결제 금액을 고객에게 돌려주는 절차",
        synonyms=("환불", "환급", "돈 돌려", "돈을 돌려", "돌려받", "결제 취소", "카드 취소", "승인 취소"),
        related=("return", "cancel"),
    ),
    "return": TermRule(
        key="return",
        label="반품",
        definition="고객이 받은 상품을 회사로 돌려보내는 절차",
        synonyms=("반품", "회수", "돌려보내", "상품 반환", "물건 반환", "물건 돌려"),
        related=("refund", "exchange"),
    ),
    "cancel": TermRule(
        key="cancel",
        label="취소",
        definition="주문 또는 결제를 확정 전/배송 전 단계에서 무효화하는 절차",
        synonyms=("취소", "주문 취소", "구매 취소", "예약 취소", "배송 전 취소", "출고 전 취소"),
        related=("refund",),
    ),
    "exchange": TermRule(
        key="exchange",
        label="교환",
        definition="상품을 다른 상품 또는 정상 상품으로 바꾸는 절차",
        synonyms=("교환", "교체", "바꿔", "바꾸", "다른 상품", "새 상품"),
        related=("return", "as"),
    ),
    "as": TermRule(
        key="as",
        label="AS",
        definition="구매 후 수리, 점검, 교체를 지원하는 사후 서비스",
        synonyms=("AS", "A/S", "수리", "고장", "점검", "사후서비스", "사후 서비스"),
        related=("exchange",),
    ),
}

STAGE_RULES: dict[str, tuple[str, ...]] = {
    "before_consultation": ("상담 전", "예약 전", "방문 전"),
    "consultation": ("상담", "초진", "재진", "내원"),
    "before_procedure": ("수술 전", "시술 전", "전날", "당일 전", "준비"),
    "after_procedure": ("수술 후", "시술 후", "회복", "사후", "경과"),
    "emergency": ("응급", "즉시", "응급실", "심한", "지속적인 출혈"),
    "before_payment": ("결제 전", "결제하기 전", "미결제"),
    "after_payment": ("결제 후", "결제 완료", "결제한", "구매 후"),
    "before_shipping": ("배송 전", "출고 전", "발송 전"),
    "after_shipping": ("배송 후", "출고 후", "발송 후", "배송중", "배송 중"),
    "after_delivery": ("수령 후", "받은 후", "도착 후", "배송 완료", "상품 수령"),
}

TARGET_RULES: dict[str, tuple[str, ...]] = {
    "eye": ("눈", "쌍꺼풀", "눈매교정", "트임", "상안검", "하안검"),
    "nose": ("코", "코수술", "콧대", "코끝", "비중격"),
    "lifting": ("리프팅", "실리프팅", "안면거상", "탄력"),
    "injection": ("보톡스", "필러", "주사", "스킨부스터"),
    "general_clinic": ("병원", "상담", "예약", "진료", "주차"),
    "general_product": ("일반상품", "일반 상품", "상품", "제품"),
    "digital_product": ("디지털", "온라인 콘텐츠", "콘텐츠", "다운로드", "전자책"),
    "subscription": ("구독", "정기결제", "멤버십"),
    "custom_order": ("주문제작", "맞춤 제작", "커스텀", "개별 제작"),
}

EXCEPTION_RULES: dict[str, tuple[str, ...]] = {
    "medical_judgment": ("진단", "처방", "수술 가능", "사진 보면", "염증인가", "정상인가", "재수술해야"),
    "emergency_symptom": ("심한 통증", "지속적인 출혈", "호흡곤란", "고열", "시야 이상", "응급"),
    "minor": ("미성년자", "보호자", "가족관계"),
    "opened": ("개봉", "포장 훼손", "봉인 훼손"),
    "used": ("사용", "착용", "설치"),
    "damaged": ("훼손", "파손", "오염"),
    "custom_order": ("주문제작", "맞춤 제작", "커스텀"),
}

CHANNEL_RULES: dict[str, tuple[str, ...]] = {
    "phone": ("전화", "연락처", "콜", "02-"),
    "kakao": ("카카오톡", "카톡", "채널"),
    "naver": ("네이버", "네이버 예약"),
    "app": ("앱", "어플", "모바일"),
    "web": ("웹", "홈페이지", "사이트", "마이페이지"),
    "cs": ("고객센터", "상담", "문의", "전화", "채팅"),
    "store": ("매장", "오프라인", "방문"),
}

PERIOD_RULES: tuple[str, ...] = (
    "당일", "24시간", "1일", "2일", "3일", "5일", "7일", "일주일", "10일", "14일", "2주", "30일", "한 달", "1개월", "3개월", "6개월", "90일"
)

_repo_root = Path(__file__).resolve().parents[1]
DEFAULT_ONTOLOGY_MD_PATH = Path(os.getenv(
    "PLASTIC_SURGERY_ONTOLOGY_PATH",
    str(_repo_root / "samples" / "2.plastic_surgery_ontology_sample.md"),
))
EXTERNAL_ONTOLOGY: dict[str, Any] = {}
ROUTING_RULES: list[dict[str, Any]] = []
ANSWER_POLICIES: dict[str, list[str]] = {"must_do": [], "must_not_do": []}
SYMPTOM_RISK_RULES: dict[str, tuple[str, ...]] = {}
QUESTION_TYPE_META: dict[str, dict[str, str]] = {}


def _slug(text: str) -> str:
    """온톨로지 라벨을 안전한 내부 key로 변환한다."""
    explicit = {
        "눈성형": "procedure_eye",
        "코성형": "procedure_nose",
        "필러": "procedure_filler",
        "보톡스": "procedure_botox",
        "리프팅": "procedure_lifting",
        "지방흡입_지방이식": "procedure_fat",
        "예약문의": "qtype_reservation",
        "비용문의": "qtype_cost",
        "수술전준비": "qtype_pre_care",
        "수술후관리": "qtype_post_care",
        "부작용의심": "qtype_adverse_event",
        "서류문의": "qtype_documents",
        "환불취소문의": "qtype_refund_cancel",
    }
    if text in explicit:
        return explicit[text]
    cleaned = re.sub(r"[^0-9A-Za-z가-힣_]+", "_", text).strip("_")
    return f"external_{cleaned}" if cleaned else "external_unknown"


def extract_json_block_from_markdown(markdown_text: str) -> dict[str, Any]:
    """Markdown 안의 첫 번째 json 코드블록을 dict로 파싱한다."""
    match = re.search(r"```json\s*(.*?)\s*```", markdown_text, re.DOTALL | re.IGNORECASE)
    if not match:
        raise ValueError("Markdown 파일에서 ```json 코드블록을 찾지 못했습니다.")
    return json.loads(match.group(1))


def load_external_ontology(path: str | Path = DEFAULT_ONTOLOGY_MD_PATH) -> dict[str, Any]:
    """외부 md 온톨로지 샘플을 로드한다. 파일이 없으면 빈 dict를 반환한다."""
    p = Path(path).expanduser()
    if not p.exists():
        return {}
    return extract_json_block_from_markdown(p.read_text(encoding="utf-8", errors="ignore"))


def apply_external_ontology(data: dict[str, Any] | None = None) -> dict[str, Any]:
    """외부 온톨로지를 기본 규칙에 병합한다."""
    global EXTERNAL_ONTOLOGY, ROUTING_RULES, ANSWER_POLICIES
    if data is None:
        data = load_external_ontology()
    if not data:
        return {}

    EXTERNAL_ONTOLOGY = data

    for label, spec in data.get("procedure_categories", {}).items():
        key = _slug(label)
        synonyms = tuple(dict.fromkeys([label, *spec.get("synonyms", []), *spec.get("subtypes", [])]))
        TERMS[key] = TermRule(
            key=key,
            label=label,
            definition=f"성형외과 시술/수술 분류: {label}",
            synonyms=synonyms,
            related=("procedure", "pre_care", "post_care"),
        )
        TARGET_RULES[key] = synonyms
        high_signals = tuple(spec.get("high_risk_signals", []))
        if high_signals:
            EXCEPTION_RULES[f"high_risk_{key}"] = high_signals
            SYMPTOM_RISK_RULES[f"high:{label}"] = high_signals

    for label, spec in data.get("question_types", {}).items():
        key = _slug(label)
        synonyms = tuple(dict.fromkeys([label, *spec.get("synonyms", [])]))
        TERMS[key] = TermRule(
            key=key,
            label=label,
            definition=f"질문 유형: {label} / 기본 대응: {spec.get('default_action', '')}",
            synonyms=synonyms,
            related=(),
        )
        QUESTION_TYPE_META[key] = {
            "risk_level": spec.get("risk_level", "unknown"),
            "default_action": spec.get("default_action", ""),
            "forbidden": ", ".join(spec.get("forbidden", [])),
        }

    for risk_level, spec in data.get("symptom_risk_levels", {}).items():
        symptoms = tuple(spec.get("symptoms", []))
        if symptoms:
            SYMPTOM_RISK_RULES[risk_level] = symptoms
            if risk_level in {"high", "medium"}:
                EXCEPTION_RULES[f"symptom_{risk_level}"] = symptoms

    ROUTING_RULES = list(data.get("routing_rules", []))
    ANSWER_POLICIES = data.get("answer_policies", ANSWER_POLICIES)
    return data


def _normalize_text(text: str) -> str:
    """한국어 구어체 증상 표현을 온톨로지 키워드와 비교하기 쉽게 정규화한다."""
    normalized = text.lower()
    replacements = {
        "숨쉬기가 힘들": "숨쉬기 힘듦 호흡곤란",
        "숨쉬기 힘들어요": "숨쉬기 힘듦 호흡곤란",
        "숨쉬기 힘들어": "숨쉬기 힘듦 호흡곤란",
        "숨 쉬기 힘들": "숨쉬기 힘듦 호흡곤란",
        "숨쉬기 힘들": "숨쉬기 힘듦 호흡곤란",
        "숨이 차": "호흡곤란",
        "숨이 안": "호흡곤란",
        "답답해요": "호흡곤란 숨쉬기 힘듦",
        "답답해": "호흡곤란 숨쉬기 힘듦",
        "피가 계속 나": "피가 계속 남 지속 출혈",
        "피가 멈추지": "코피가 멈추지 않음 지속 출혈",
        "앞이 흐릿": "앞이 흐림 시야 이상",
        "앞이 흐려": "앞이 흐림 시야 이상",
        "잘 안 보여": "잘 안 보임 시야 이상",
        "잘 안 보임": "시야 이상",
        "하얗게 변했": "하얗게 변함 피부색 변화",
        "검게 변했": "검게 변함 피부색 변화",
        "진료시간": "진료시간 영업시간 운영시간",
        "진료 시간": "진료시간 영업시간 운영시간",
        "예약금": "예약금 환불 취소",
        "환불": "환불 취소 예약금",
    }
    for old, new in replacements.items():
        normalized = normalized.replace(old, new)
    return normalized


def _contains_any(text: str, words: Iterable[str]) -> bool:
    lowered = _normalize_text(text)
    return any(w.lower() in lowered for w in words)


def detect_domains(text: str) -> list[dict]:
    """텍스트에서 업무 domain 후보를 감지한다."""
    hits = []
    for key, rule in TERMS.items():
        matched = [w for w in rule.synonyms if w.lower() in _normalize_text(text)]
        if matched:
            hits.append({
                "key": key,
                "label": rule.label,
                "definition": rule.definition,
                "matched_terms": matched,
                "score": min(1.0, 0.45 + 0.15 * len(matched)),
            })
    return sorted(hits, key=lambda x: x["score"], reverse=True)


def detect_first(text: str, rules: dict[str, tuple[str, ...]]) -> str:
    for key, words in rules.items():
        if _contains_any(text, words):
            return key
    return "unknown"


def detect_all(text: str, rules: dict[str, tuple[str, ...]]) -> list[str]:
    return [key for key, words in rules.items() if _contains_any(text, words)]


def detect_period(text: str) -> str:
    for period in PERIOD_RULES:
        if period in text:
            return period
    return "unknown"


def detect_medical_risk_level(text: str) -> str:
    """외부 온톨로지의 증상 위험도 규칙으로 low/medium/high를 판정한다."""
    # high를 최우선으로 본다.
    for level in ("high", "medium", "low"):
        words = SYMPTOM_RISK_RULES.get(level, ())
        if _contains_any(text, words):
            return level
    # procedure별 high risk 신호도 high로 처리한다.
    for key, words in SYMPTOM_RISK_RULES.items():
        if key.startswith("high:") and _contains_any(text, words):
            return "high"
    return "unknown"


def _condition_matches(text: str, condition: dict[str, Any]) -> bool:
    """routing rule의 condition이 현재 텍스트에 맞는지 확인한다."""
    procedure = condition.get("procedure")
    if procedure:
        proc_key = _slug(procedure)
        words = TARGET_RULES.get(proc_key, (procedure,))
        if not _contains_any(text, words):
            return False

    question_type = condition.get("question_type")
    if question_type:
        qtype_key = _slug(question_type)
        rule = TERMS.get(qtype_key)
        # 예약문의 규칙은 환불/취소 키워드가 없을 때만 매칭 (예약금 환불 오분류 방지)
        if question_type == "예약문의" and _contains_any(text, ("환불", "취소", "예약금", "노쇼")):
            return False
        words = rule.synonyms if rule else (question_type,)
        if not _contains_any(text, words):
            return False

    symptom_contains = condition.get("symptom_contains")
    if symptom_contains and not _contains_any(text, symptom_contains):
        return False

    return True


def detect_routing(text: str) -> dict[str, str]:
    """외부 온톨로지 routing_rules를 적용해 위험도/대응을 찾는다."""
    for rule in ROUTING_RULES:
        if _condition_matches(text, rule.get("condition", {})):
            return {
                "routing_rule_id": rule.get("rule_id", ""),
                "medical_risk_level": rule.get("risk_level", "unknown"),
                "routing_action": rule.get("action", ""),
                "recommended_response": rule.get("recommended_response", ""),
                "forbidden_response": ", ".join(rule.get("forbidden_response", [])),
            }
    return {
        "routing_rule_id": "",
        "medical_risk_level": detect_medical_risk_level(text),
        "routing_action": "",
        "recommended_response": "",
        "forbidden_response": "",
    }


def annotate_faq(question: str, answer: str) -> dict:
    """FAQ Q/A 하나에 업무 온톨로지 메타데이터를 자동 부여한다."""
    text = f"{question}\n{answer}"
    domains = detect_domains(text)
    primary = domains[0] if domains else None
    confidence = primary["score"] if primary else 0.0

    # domain이 없거나 복수 domain이 비슷하게 잡히면 사람 검토 필요
    requires_review = False
    review_reason = ""
    if not primary:
        requires_review = True
        review_reason = "업무 domain을 자동 판정하지 못했습니다."
    elif len(domains) >= 2 and domains[1]["score"] >= primary["score"] - 0.15:
        requires_review = True
        review_reason = "복수 업무 domain이 함께 감지되어 용어 병합/구분 검토가 필요합니다."

    routing = detect_routing(text)
    if routing.get("medical_risk_level") == "high":
        requires_review = True
        review_reason = (review_reason + " / " if review_reason else "") + "고위험 증상 또는 즉시 대응 라우팅 규칙이 감지되었습니다."

    return {
        "ontology_domain": primary["key"] if primary else "unknown",
        "ontology_label": primary["label"] if primary else "미분류",
        "ontology_definition": primary["definition"] if primary else "자동 분류 실패",
        "ontology_confidence": round(confidence, 2),
        "ontology_matched_terms": ", ".join(primary["matched_terms"]) if primary else "",
        "ontology_related": ", ".join(TERMS[primary["key"]].related) if primary else "",
        "policy_stage": detect_first(text, STAGE_RULES),
        "policy_target": detect_first(text, TARGET_RULES),
        "policy_period": detect_period(text),
        "policy_exceptions": ", ".join(detect_all(text, EXCEPTION_RULES)),
        "policy_channels": ", ".join(detect_all(text, CHANNEL_RULES)),
        "requires_human_review": requires_review,
        "review_reason": review_reason,
        "routing_rule_id": routing.get("routing_rule_id", ""),
        "medical_risk_level": routing.get("medical_risk_level", "unknown"),
        "routing_action": routing.get("routing_action", ""),
        "recommended_response": routing.get("recommended_response", ""),
        "forbidden_response": routing.get("forbidden_response", ""),
        "ontology_source": EXTERNAL_ONTOLOGY.get("ontology_name", "built_in_rules"),
    }


def expand_query_with_ontology(query: str) -> str:
    """사용자 질문을 표준 용어/동의어로 확장해 검색 recall을 높인다."""
    domains = detect_domains(query)
    if not domains:
        return query

    primary = domains[0]
    rule = TERMS[primary["key"]]
    expansion_terms = [rule.label, *rule.synonyms[:4]]
    related_labels = [TERMS[k].label for k in rule.related if k in TERMS]
    return (
        f"{query}\n"
        f"[온톨로지 검색 확장] 표준업무={rule.label}; "
        f"관련표현={', '.join(dict.fromkeys(expansion_terms))}; "
        f"관련업무={', '.join(related_labels) if related_labels else '없음'}"
    )


def ontology_context_for_prompt(docs: list[dict]) -> str:
    """검색된 문서들의 온톨로지 메타데이터를 LLM 프롬프트에 넣기 좋은 문자열로 만든다."""
    lines = []
    for i, doc in enumerate(docs, 1):
        lines.append(
            f"[정책 메타 {i}] "
            f"유형={doc.get('ontology_label', '미분류')} "
            f"단계={doc.get('policy_stage', 'unknown')} "
            f"대상={doc.get('policy_target', 'unknown')} "
            f"기간={doc.get('policy_period', 'unknown')} "
            f"위험도={doc.get('medical_risk_level', 'unknown')} "
            f"대응={doc.get('routing_action', '') or '기본 FAQ 답변'} "
            f"예외={doc.get('policy_exceptions', '') or '없음'} "
            f"검토필요={doc.get('requires_human_review', False)}"
        )
    return "\n".join(lines)


def term_table() -> list[dict]:
    """UI/문서화를 위한 용어표 반환."""
    return [asdict(rule) for rule in TERMS.values()]


# 모듈 import 시 데스크탑 md 온톨로지를 자동 적용한다.
apply_external_ontology()


if __name__ == "__main__":
    sample = {
        "question": "상품을 받은 후 환불할 수 있나요?",
        "answer": "일반 상품은 수령 후 7일 이내에 고객센터를 통해 환불 신청이 가능합니다. 단, 개봉 또는 사용한 상품은 제한될 수 있습니다.",
    }
    print(annotate_faq(**sample))
    print(expand_query_with_ontology("돈 돌려받을 수 있나요?"))
