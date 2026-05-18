# 04. 데이터와 온톨로지

## FAQ 데이터

지원 파일 형식:

```text
.md
.txt
.pdf
.docx
```

업로드된 파일은 다음 위치에 저장됩니다.

```text
data/uploads/
```

현재 샘플 FAQ 파일:

```text
data/uploads/plastic_surgery_faq_knowledge_base.md
```

## FAQ 구조

구조화된 FAQ 문서는 다음 형식을 권장합니다.

```markdown
## FAQ-001. 상담 예약은 어떻게 하나요?

**질문 예시**
- 상담 예약하고 싶어요
- 예약은 어디서 하나요?

**답변**
전화, 카카오톡 채널, 네이버 예약을 통해 상담 예약이 가능합니다.

**태그**
상담예약, 카카오톡, 네이버예약
```

## 온톨로지 파일

외부 온톨로지 샘플 파일은 재개발 편의를 위해 프로젝트 내부에 포함합니다.

```text
data/uploads/plastic_surgery_ontology_sample.md
```

기존 로컬 작업 환경에서는 다음 경로도 fallback으로 인식합니다.

```text
~/Desktop/plastic_surgery_ontology_sample.md
~/Desktop/Working/2.plastic_surgery_ontology_sample.md
~/Downloads/Telegram Desktop/2.plastic_surgery_ontology_sample.md
```

이 파일 안의 JSON 코드블록을 `src/ontology.py`가 자동 추출해 기본 규칙과 병합합니다.

## 적용되는 온톨로지 항목

- `procedure_categories`
  - 눈성형, 코성형, 필러, 보톡스, 리프팅 등
- `question_types`
  - 예약문의, 비용문의, 수술전준비, 수술후관리, 부작용의심 등
- `symptom_risk_levels`
  - low / medium / high
- `routing_rules`
  - 즉시 병원 연락, 응급실 안내, 상담실 연결 등
- `answer_policies`
  - 금지 답변과 권장 답변 정책

## 메타데이터 흐름

```text
FAQ 문서
↓
annotate_faq()
↓
medical_risk_level
routing_action
recommended_response
forbidden_response
↓
ChromaDB metadata
↓
RAG prompt
```

주의: 이 메타데이터는 내부 판단용이며 사용자 UI에는 표시하지 않습니다.

## 구어체 정규화

실제 사용자가 다음처럼 말해도 온톨로지와 연결되도록 정규화합니다.

```text
숨쉬기 힘들어요 → 호흡곤란 / 숨쉬기 힘듦
피가 계속 나요 → 지속 출혈 / 피가 계속 남
앞이 흐려요 → 시야 이상 / 앞이 흐림
하얗게 변했어요 → 피부색 변화
```
