"""
[Step 6.5] 정보 갭 탐지
KG 관계를 따라가서 대화에 필요하지만 프로필에 없는 정보를 찾고,
자연스러운 질문 힌트를 생성합니다.

- emotion 의도일 때는 동작하지 않음 (공감/위로 우선)
- 한 턴에 최대 1개 질문만 생성 (과도한 질문 방지)
"""
import json
from typing import Optional
from models import UserProfile, RetrievedDocument


# KG 엔티티 ID → 필요한 프로필 필드 + 자연스러운 질문
# 대화에서 이 엔티티가 등장하면, 해당 프로필 필드가 비어있는지 확인
ENTITY_INFO_NEEDS = {
    # --- AMH 수치가 필요한 상황 ---
    "C_ohss": {
        "field": "amh",
        "priority": 3,
        "hint": "참고로 AMH 수치를 알고 계시면 더 맞춤 안내가 가능한데, 혹시 아시나요?",
    },
    "C_dor": {
        "field": "amh",
        "priority": 3,
        "hint": "AMH 수치를 알고 계시면 난소 기능 상태를 더 정확히 안내해드릴 수 있어요. 혹시 검사 받으셨나요?",
    },
    "H_AMH": {
        "field": "amh",
        "priority": 2,
        "hint": "AMH 수치가 얼마인지 알고 계시면 알려주세요. 더 맞춤 안내가 가능해요.",
    },
    "H_FSH": {
        "field": "amh",
        "priority": 1,
        "hint": "혹시 AMH 수치도 같이 확인하셨나요? 함께 보면 더 정확한 안내가 가능해요.",
    },
    "TX_COH": {
        "field": "amh",
        "priority": 2,
        "hint": "과배란 유도 반응은 AMH 수치에 따라 달라질 수 있어요. 혹시 수치를 알고 계시나요?",
    },

    # --- 진단명이 필요한 상황 ---
    "C_pcos": {
        "field": "diagnoses",
        "check_value": "pcos",
        "priority": 2,
        "hint": "혹시 다낭성난소증후군(PCOS) 진단을 받으신 적이 있으신가요?",
    },
    "C_endometriosis": {
        "field": "diagnoses",
        "check_value": "endometriosis",
        "priority": 2,
        "hint": "자궁내막증 진단을 받으신 적이 있으신가요?",
    },
    "C_tubal": {
        "field": "diagnoses",
        "check_value": "tubal",
        "priority": 2,
        "hint": "혹시 난관 관련 진단을 받으신 적이 있으신가요?",
    },
    "C_male_factor": {
        "field": "diagnoses",
        "check_value": "male_factor",
        "priority": 1,
        "hint": "남성 요인 검사도 받으셨는지 궁금해요. 혹시 결과를 알고 계시나요?",
    },

    # --- 프로토콜 정보가 필요한 상황 ---
    "TX_long_protocol": {
        "field": "protocol",
        "priority": 2,
        "hint": "어떤 프로토콜(장기요법/단기요법/길항제/자연주기)로 진행 중이신지 알면 더 정확한 안내가 가능해요.",
    },
    "TX_short_protocol": {
        "field": "protocol",
        "priority": 2,
        "hint": "어떤 프로토콜(장기요법/단기요법/길항제/자연주기)로 진행 중이신지 알면 더 정확한 안내가 가능해요.",
    },
    "TX_antagonist_protocol": {
        "field": "protocol",
        "priority": 2,
        "hint": "어떤 프로토콜로 진행 중이신지 알면 더 정확한 안내가 가능해요.",
    },
    "TX_mild_ivf": {
        "field": "protocol",
        "priority": 1,
        "hint": "자극 방법이 어떻게 되시는지 알면 더 맞춤 안내가 가능해요.",
    },

    # --- 현재 단계(phase) 정보가 필요한 상황 ---
    "TX_ET": {
        "field": "current_phase",
        "priority": 2,
        "hint": "이식 후 며칠째인지 알면 더 맞춤 안내가 가능해요. 혹시 알려주실 수 있나요?",
    },
    "TX_FET": {
        "field": "current_phase",
        "priority": 2,
        "hint": "이식 후 며칠째인지 알면 더 맞춤 안내가 가능해요. 혹시 알려주실 수 있나요?",
    },
    # TX_egg_retrieval → KG에 채란 전용 엔티티 없음, TX_COH(과배란 유도)가 대신 커버

    # --- 배아 등급 ---
    "A_implantation": {
        "field": "embryo_grade",
        "priority": 1,
        "hint": "배아 등급을 알고 계시면 알려주세요. 더 구체적인 안내가 가능해요.",
    },

    # --- 지역 정보 (지원금 관련) ---
    "POL_subsidy": {
        "field": "region",
        "priority": 3,
        "hint": "거주 지역을 알면 지자체별 추가 지원금도 안내해드릴 수 있어요. 어디에 거주하고 계세요?",
    },
    "POL_insurance": {
        "field": "region",
        "priority": 1,
        "hint": "거주 지역에 따라 지원 내용이 다를 수 있어요. 혹시 어디에 사세요?",
    },
}

# 트리플 관계 유형을 따라갈 때 정보 갭과 연결되는 관계들
RELEVANT_RELATIONS = {
    "위험_인자", "관련_검사", "관련_질환", "관련_약물",
    "합병증", "치료_방법", "치료방법", "예방_방법",
}


class InfoGapDetector:
    """대화에 필요하지만 프로필에 없는 정보를 탐지"""

    def __init__(self, knowledge_enricher):
        self.triples = []
        # knowledge_enricher에서 이미 로드된 트리플 가져오기
        triples_data = knowledge_enricher.triples
        if isinstance(triples_data, dict):
            self.triples = triples_data.get("triples", [])
        elif isinstance(triples_data, list):
            self.triples = triples_data

        print(f"[InfoGapDetector] 초기화 완료 (트리플: {len(self.triples)}건)")

    # 사용자가 현재 단계와 다른 시술을 언급하는지 판단하기 위한 키워드
    _STAGE_KEYWORDS = {
        "인공수정": ["인공수정", "iui"],
        "체외수정": ["시험관", "체외수정", "ivf", "배아 이식", "이식", "채란", "난자 채취", "과배란"],
        "동결배아 이식": ["동결배아", "fet", "해동"],
    }

    def _is_asking_about_other_stage(self, user_input: str, profile: UserProfile) -> bool:
        """사용자가 현재 단계가 아닌 다른 시술에 대해 물어보는지 확인"""
        if not user_input or not profile.treatment_stage:
            return False
        input_lower = user_input.lower()
        current_stage = profile.treatment_stage

        for stage, keywords in self._STAGE_KEYWORDS.items():
            if stage == current_stage:
                continue
            for kw in keywords:
                if kw in input_lower:
                    return True
        return False

    def detect(
        self,
        entity_ids: set[str],
        profile: UserProfile,
        intent: str,
        user_input: str = "",
    ) -> Optional[str]:
        """
        대화에 등장한 엔티티를 기반으로 프로필에서 빠진 정보를 탐지.

        Returns:
            자연스러운 질문 힌트 문자열, 또는 None (갭 없음/emotion 모드)
        """
        # emotion 모드에서는 정보 수집 안 함
        if intent == "emotion":
            return None

        # 사용자가 증상/불편감을 호소하는 중이면 정보 수집 안 함
        SYMPTOM_KEYWORDS = ["아파", "아프", "아픈", "통증", "불편", "불편해", "불편함", "아프다", "힘들어", "힘드", "속쓰려", "메스껍", "어지럽"]
        if any(kw in user_input for kw in SYMPTOM_KEYWORDS):
            return None

        # 사용자가 다른 시술에 대해 물어보는 중이면 세부 정보 묻지 않음
        if self._is_asking_about_other_stage(user_input, profile):
            return None

        self._current_input = user_input

        if not entity_ids:
            return None

        # policy 의도에서는 정책 관련 필드만 질문 (의학 정보 제외)
        POLICY_RELEVANT_FIELDS = {"region", "marriage_status", "dual_income"}

        # 1단계: 직접 매칭 — 등장한 엔티티가 INFO_NEEDS에 있는지
        candidates = []
        for eid in entity_ids:
            if eid in ENTITY_INFO_NEEDS:
                need = ENTITY_INFO_NEEDS[eid]
                if intent == "policy" and need["field"] not in POLICY_RELEVANT_FIELDS:
                    continue
                if self._is_missing(profile, need):
                    candidates.append(need)

        # 2단계: 트리플 탐색 — 등장한 엔티티에서 1홉 따라가서 연결된 엔티티 확인
        expanded_ids = self._expand_via_triples(entity_ids)
        for eid in expanded_ids - entity_ids:  # 새로 발견된 것만
            if eid in ENTITY_INFO_NEEDS:
                need = ENTITY_INFO_NEEDS[eid]
                if intent == "policy" and need["field"] not in POLICY_RELEVANT_FIELDS:
                    continue
                if self._is_missing(profile, need):
                    # 트리플 경유는 우선순위 1 낮춤
                    candidates.append({**need, "priority": max(need["priority"] - 1, 0)})

        if not candidates:
            return None

        # 우선순위가 가장 높은 것 1개만 반환
        best = max(candidates, key=lambda x: x["priority"])
        return best["hint"]

    # 필드별 관련 키워드 — 사용자 질문에 이 키워드가 있어야 해당 필드를 물어봄
    _FIELD_RELEVANCE = {
        "amh": ["amh", "난소", "과배란", "자극", "dor", "난소기능", "수치", "호르몬", "검사"],
        "embryo_grade": ["배아", "등급", "이식", "배양"],
        "protocol": ["프로토콜", "장기요법", "단기요법", "길항제", "자연주기", "자극"],
        "current_phase": ["이식", "채란", "난자 채취", "배란"],
    }

    def _is_relevant_to_question(self, field: str) -> bool:
        """정보 갭의 필드가 현재 질문 주제와 관련 있는지 확인"""
        user_input = getattr(self, "_current_input", "")
        if not user_input:
            return True  # 질문 텍스트가 없으면 기본적으로 허용

        keywords = self._FIELD_RELEVANCE.get(field)
        if not keywords:
            return True  # 매핑이 없는 필드는 항상 허용 (region 등)

        input_lower = user_input.lower()
        return any(kw in input_lower for kw in keywords)

    def _is_missing(self, profile: UserProfile, need: dict) -> bool:
        """프로필에서 해당 필드가 비어있는지 확인"""
        field = need["field"]

        # 질문 주제와 관련 없으면 물어보지 않음
        if not self._is_relevant_to_question(field):
            return False

        value = getattr(profile, field, None)

        # diagnoses 필드는 특정 값이 포함되어 있는지 확인
        if field == "diagnoses" and "check_value" in need:
            if isinstance(value, list) and value:
                # 이미 진단 목록이 있고, 해당 진단이 포함되어 있으면 → 갭 아님
                # 진단 목록이 있지만 해당 진단이 없으면 → 물어볼 수 있음
                # 하지만 "모름"이 포함되어 있으면 → 물어볼 필요 없음
                if "unknown" in value:
                    return False
                return need["check_value"] not in value
            return not value  # 빈 리스트면 missing

        # 일반 필드
        if value is None or value == "" or value == []:
            return True
        return False

    def _expand_via_triples(self, entity_ids: set[str]) -> set[str]:
        """트리플을 1홉 따라가서 연결된 엔티티 ID 수집"""
        expanded = set(entity_ids)

        for triple in self.triples:
            relation = triple.get("relation", "")
            if relation not in RELEVANT_RELATIONS:
                continue

            subj_id = triple.get("subject_id", "")
            obj_id = triple.get("object_id", "")

            if subj_id in entity_ids and obj_id:
                expanded.add(obj_id)
            if obj_id in entity_ids and subj_id:
                expanded.add(subj_id)

        return expanded
