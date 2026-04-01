"""
[Step 6] 지식 그래프 보강 — v2 (임상 추론 지원)

v1 → v2 변경사항:
- _get_entity_details: name+description만 → 구조화된 필드 포함
  (symptoms, risk_factors, complications, diagnosed_by, dose, timing 등)
- _get_timeline_info: 기본 phase만 → side_effects, complications, risk_factors 포함
- 새 섹션: "### 맞춤 대화를 위한 임상 컨텍스트" 추가
"""
import json
from config import KG_PATH, TRIPLES_PATH, TIMELINE_PATH
from models import RetrievedDocument, UserProfile


class KnowledgeEnricher:
    def __init__(
        self,
        kg_path: str = KG_PATH,
        triples_path: str = TRIPLES_PATH,
        timeline_path: str = TIMELINE_PATH,
    ):
        self.kg = {}
        self.triples = []
        self.timeline = {}
        self._load(kg_path, triples_path, timeline_path)

    def _load(self, kg_path: str, triples_path: str, timeline_path: str):
        """데이터 파일 로드"""
        try:
            with open(kg_path, "r", encoding="utf-8") as f:
                self.kg = json.load(f)
            print(f"[KnowledgeEnricher] KG 로드: {len(self.kg.get('entities', {}))} 카테고리")
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"[KnowledgeEnricher] KG 로드 실패: {e}")

        try:
            with open(triples_path, "r", encoding="utf-8") as f:
                raw = json.load(f)
            if isinstance(raw, dict) and "triples" in raw:
                self.triples = raw["triples"]
            else:
                self.triples = raw
            print(f"[KnowledgeEnricher] Triples 로드: {len(self.triples)}건")
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"[KnowledgeEnricher] Triples 로드 실패: {e}")

        try:
            with open(timeline_path, "r", encoding="utf-8") as f:
                self.timeline = json.load(f)
            print(f"[KnowledgeEnricher] Timeline 로드 완료")
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"[KnowledgeEnricher] Timeline 로드 실패: {e}")

    def enrich(
        self,
        documents: list[RetrievedDocument],
        profile: UserProfile,
        intent: str,
        user_message: str = "",
    ) -> str:
        """
        검색 결과 + 프로필을 기반으로 KG 컨텍스트를 생성합니다.

        1. 검색 결과의 entity_ids에서 KG 엔티티 상세 조회 (v2: 구조화 필드 포함)
        2. triples에서 관련 엔티티 탐색
        3. 타임라인 정보 (v2: 부작용, 합병증, 위험요인 포함)
        4. 현재 단계 정보
        5. 통합 컨텍스트 문자열 반환
        """
        context_parts = []

        # ── 1. 엔티티 상세 정보 (v2: 구조화 필드 포함) ──
        entity_ids = set()
        for doc in documents:
            entity_ids.update(doc.entity_ids)

        print(f"[KnowledgeEnricher] entity_ids: {entity_ids or '(없음)'}")

        if entity_ids:
            entity_info = self._get_entity_details(entity_ids)
            if entity_info:
                context_parts.append("### 관련 의학 정보")
                context_parts.append(entity_info)

        # ── 2. 관련 트리플 탐색 ──
        if entity_ids:
            related_info = self._get_related_triples(entity_ids)
            if related_info:
                context_parts.append("### 관련 연결 정보")
                context_parts.append(related_info)

        # ── 3. 타임라인 (v2: 부작용/합병증/위험요인 포함) ──
        if intent == "medical":
            timeline_info = self._get_timeline_info(profile)
            if timeline_info:
                context_parts.append("### 시술 사이클 타임라인")
                context_parts.append(timeline_info)

        # ── 4. 현재 단계 정보 ──
        stage_info = self._get_stage_info(profile.stage_id)
        if stage_info:
            context_parts.append("### 현재 단계 상세")
            context_parts.append(stage_info)

        result = "\n\n".join(context_parts) if context_parts else ""

        # ── 디버그 로그 ──
        if result:
            print(f"[KnowledgeEnricher] === LLM에 전달되는 KG 컨텍스트 ({len(result)}자) ===")
            # 섹션별 길이 출력
            for part in context_parts:
                first_line = part.split('\n')[0][:80]
                print(f"  {first_line}... ({len(part)}자)")
            print(f"[KnowledgeEnricher] === 전체 내용 (앞 800자) ===")
            print(result[:800])
            print(f"[KnowledgeEnricher] === 끝 ===")
        else:
            print(f"[KnowledgeEnricher] KG 컨텍스트 없음")

        return result

    # ─────────────────────────────────────────────────────
    # v2: 구조화된 엔티티 상세 정보
    # ─────────────────────────────────────────────────────
    def _get_entity_details(self, entity_ids: set) -> str:
        """
        KG에서 엔티티 상세 정보 조회 (v2)
        - conditions: symptoms, severe, risk_factors, complications, diagnosed_by, management
        - medications: dose, timing, purpose, forms, products
        - tests: items, timing, purpose
        - treatments: description
        """
        entities = self.kg.get("entities", {})
        details = []

        for eid in entity_ids:
            for category, items in entities.items():
                if not isinstance(items, list):
                    continue
                for item in items:
                    if item.get("id") != eid:
                        continue

                    name = item.get("name", "")
                    if not name:
                        break

                    lines = [f"**{name}**"]

                    # 기본 설명
                    desc = item.get("description", "")
                    if desc:
                        lines.append(f"  설명: {desc}")

                    # ── conditions 전용 필드 ──
                    if category == "conditions":
                        symptoms = item.get("symptoms", [])
                        if symptoms:
                            if isinstance(symptoms, list):
                                lines.append(f"  증상: {', '.join(symptoms)}")
                            else:
                                lines.append(f"  증상: {symptoms}")

                        severe = item.get("severe", [])
                        if severe:
                            if isinstance(severe, list):
                                lines.append(f"  심각 증상 (즉시 병원): {', '.join(severe)}")
                            else:
                                lines.append(f"  심각 증상: {severe}")

                        risk_factors = item.get("risk_factors") or item.get("위험_요인", [])
                        if risk_factors:
                            if isinstance(risk_factors, list):
                                lines.append(f"  위험 요인: {', '.join(risk_factors)}")

                        complications = item.get("complications") or item.get("합병증", [])
                        if complications:
                            if isinstance(complications, list):
                                lines.append(f"  합병증: {', '.join(complications)}")

                        diagnosed_by = item.get("diagnosed_by", [])
                        if diagnosed_by:
                            # ID → 이름 변환
                            diag_names = self._resolve_entity_names(diagnosed_by)
                            if diag_names:
                                lines.append(f"  진단 검사: {', '.join(diag_names)}")

                        treated_by = item.get("treated_by", [])
                        if treated_by:
                            treat_names = self._resolve_entity_names(treated_by)
                            if treat_names:
                                lines.append(f"  치료법: {', '.join(treat_names)}")

                        management = item.get("management", "")
                        if management:
                            lines.append(f"  관리: {management}")

                    # ── medications 전용 필드 ──
                    elif category == "medications":
                        dose = item.get("dose", "")
                        if dose:
                            lines.append(f"  용량: {dose}")

                        timing = item.get("timing") or item.get("dosing", "")
                        if timing:
                            lines.append(f"  복용 시기: {timing}")

                        purpose = item.get("purpose") or item.get("목적", "")
                        if purpose:
                            lines.append(f"  목적: {purpose}")

                        forms = item.get("forms", "")
                        if forms:
                            lines.append(f"  제형: {forms}")

                        products = item.get("products", "")
                        if products:
                            lines.append(f"  제품명: {products}")

                        high_risk = item.get("high_risk_dose", "")
                        if high_risk:
                            lines.append(f"  고위험군 용량: {high_risk}")

                        note = item.get("note", "")
                        if note:
                            lines.append(f"  참고: {note}")

                    # ── tests 전용 필드 ──
                    elif category == "tests":
                        test_items = item.get("items") or item.get("검사_항목", [])
                        if test_items and isinstance(test_items, list):
                            lines.append(f"  검사 항목: {', '.join(test_items)}")

                        timing = item.get("timing", "")
                        if timing:
                            lines.append(f"  시기: {timing}")

                        purpose = item.get("purpose", "")
                        if purpose:
                            lines.append(f"  목적: {purpose}")

                    details.append("\n".join(lines))
                    break  # 해당 엔티티 찾았으므로 다음 category로

        return "\n\n".join(details[:10])  # 최대 10개

    def _resolve_entity_names(self, entity_ids: list) -> list:
        """엔티티 ID 목록 → 이름 목록으로 변환"""
        entities = self.kg.get("entities", {})
        names = []
        for eid in entity_ids:
            if not isinstance(eid, str):
                names.append(str(eid))
                continue
            # KG entity가 아닌 직접 텍스트인 경우 (예: "체중 감량")
            if not eid.startswith(("C_", "T_", "TX_", "M_", "H_", "A_", "PSY_", "P_")):
                names.append(eid)
                continue
            found = False
            for category, items in entities.items():
                if not isinstance(items, list):
                    continue
                for item in items:
                    if item.get("id") == eid:
                        names.append(item.get("name", eid))
                        found = True
                        break
                if found:
                    break
            if not found:
                names.append(eid)
        return names

    # ─────────────────────────────────────────────────────
    # 트리플 탐색 (기존과 동일)
    # ─────────────────────────────────────────────────────
    def _get_related_triples(self, entity_ids: set) -> str:
        """triples에서 관련 엔티티 연결 탐색"""
        related = []

        for triple in self.triples:
            subj_id = triple.get("subject_id", "")
            obj_id = triple.get("object_id", "")

            if subj_id in entity_ids or obj_id in entity_ids:
                subj = triple.get("subject", "")
                rel = triple.get("relation", "")
                obj = triple.get("object", "")
                related.append(f"- {subj} → ({rel}) → {obj}")

        return "\n".join(related[:8])  # 최대 8개

    # ─────────────────────────────────────────────────────
    # 현재 단계 정보 (기존과 동일)
    # ─────────────────────────────────────────────────────
    def _get_stage_info(self, stage_id: str) -> str:
        """KG stages에서 현재 단계 정보"""
        stages = self.kg.get("stages", [])

        for stage in stages:
            if isinstance(stage, dict) and stage.get("id") == stage_id:
                parts = []
                if stage.get("description"):
                    parts.append(stage["description"])
                if stage.get("typical_duration"):
                    parts.append(f"일반적 소요기간: {stage['typical_duration']}")
                if stage.get("key_actions"):
                    actions = stage["key_actions"]
                    if isinstance(actions, list):
                        parts.append(f"주요 행동: {', '.join(actions[:5])}")
                return "\n".join(parts)

        return ""

    # ─────────────────────────────────────────────────────
    # v2: 타임라인 + 부작용/합병증/위험요인
    # ─────────────────────────────────────────────────────
    def _get_timeline_info(self, profile: UserProfile) -> str:
        """
        timeline_extension에서 현재 단계 타임라인 (v2)
        - 기본 phase별 expected_symptoms
        - side_effects (OHSS 등)
        - complications_detail
        - ohss_risk_factors (IVF)
        - post_care (FET)
        - embryo_grading (IVF)
        """
        stage_timelines = self.timeline.get("stage_timelines", {})
        stage_id = profile.stage_id

        timeline = stage_timelines.get(stage_id, {})
        if not timeline:
            print(f"[KnowledgeEnricher:timeline] stage_id={stage_id} → 타임라인 없음")
            return ""

        # 디버그: 어떤 데이터가 있는지 확인
        available_keys = [k for k in timeline.keys() if k not in ('stage_id', 'stage_name', 'alias', 'total_duration', 'description')]
        print(f"[KnowledgeEnricher:timeline] stage_id={stage_id}, 사용 가능 데이터: {available_keys}")

        parts = []

        # ── 기본 cycle_timeline ──
        cycle_timeline = timeline.get("cycle_timeline", [])
        if isinstance(cycle_timeline, list) and cycle_timeline:
            parts.append("**단계별 진행**")
            for step in cycle_timeline[:8]:
                phase = step.get("phase", "")
                if not phase:
                    continue

                phase_str = f"- **{phase}**"
                day_range = step.get("day_range", "")
                if day_range:
                    phase_str += f" ({day_range})"

                # tasks
                tasks = step.get("tasks", [])
                if tasks:
                    task_names = [t.get("action", "") for t in tasks if isinstance(t, dict)]
                    if task_names:
                        phase_str += f"\n  할 일: {', '.join(task_names)}"

                # expected_symptoms
                expected = step.get("expected_symptoms") or []
                if isinstance(expected, list) and expected:
                    phase_str += f"\n  예상 증상: {', '.join(str(s) for s in expected[:5])}"
                elif isinstance(expected, dict):
                    possible = expected.get("possible", [])
                    if possible:
                        phase_str += f"\n  예상 증상: {', '.join(str(s)[:60] for s in possible[:5])}"
                    note = expected.get("important_note", "")
                    if note:
                        phase_str += f"\n  참고: {note}"

                # post_procedure
                post_proc = step.get("post_procedure") or []
                if isinstance(post_proc, list) and post_proc:
                    phase_str += f"\n  주의사항: {', '.join(post_proc[:3])}"

                parts.append(phase_str)

        # ── v2: 부작용 (OHSS 등) ──
        side_effects = timeline.get("side_effects", {})
        print(f"[KnowledgeEnricher:timeline] side_effects 존재: {bool(side_effects)}, keys: {list(side_effects.keys()) if side_effects else 'none'}")
        if side_effects:
            se_parts = []
            for se_key, se_data in side_effects.items():
                is_dict = isinstance(se_data, dict)
                print(f"[KnowledgeEnricher:timeline]   '{se_key}': type={type(se_data).__name__}, is_dict={is_dict}")
                if is_dict:
                    name = se_data.get("name", se_key)
                    symptoms = se_data.get("symptoms", [])
                    incidence = se_data.get("incidence", "")
                    action = se_data.get("action", "")

                    se_str = f"- **{name}**"
                    if incidence:
                        se_str += f" (발생률: {incidence})"
                    if symptoms:
                        se_str += f"\n  증상: {', '.join(symptoms)}"
                    if action:
                        se_str += f"\n  대처: {action}"
                    se_parts.append(se_str)
                    print(f"[KnowledgeEnricher:timeline]   → 추가: {se_str[:80]}")

            # reassurance (안심 정보)
            reassurance = side_effects.get("reassurance", [])
            if reassurance and isinstance(reassurance, list):
                se_parts.append("- **안심 정보**: " + " / ".join(str(r) for r in reassurance))

            print(f"[KnowledgeEnricher:timeline] se_parts={len(se_parts)}개, parts(before)={len(parts)}개")
            if se_parts:
                parts.append("\n**부작용 정보**")
                parts.extend(se_parts)
                print(f"[KnowledgeEnricher:timeline] → 부작용 추가 완료, parts={len(parts)}개")
        else:
            print(f"[KnowledgeEnricher:timeline] side_effects 비어있음 → 스킵")

        # ── v2: OHSS 위험 요인 (IVF) ──
        ohss_rf = timeline.get("ohss_risk_factors", {})
        if ohss_rf:
            factors = ohss_rf.get("factors", [])
            if factors:
                parts.append(f"\n**OHSS 위험 요인**: {', '.join(factors)}")

        # ── v2: 합병증 상세 ──
        complications = timeline.get("complications_detail", {})
        if complications:
            comp_parts = []

            egg_comp = complications.get("egg_retrieval_complications", {})
            if egg_comp:
                items = []
                for k, v in egg_comp.items():
                    if k != "note":
                        items.append(f"{k}: {v}")
                if items:
                    comp_parts.append(f"- 난자 채취 합병증: {', '.join(items)}")

            ectopic = complications.get("ectopic_pregnancy", {})
            if ectopic:
                rate = ectopic.get("rate", "")
                risk = ectopic.get("risk_factors", "")
                comp_parts.append(f"- 자궁외임신: 발생률 {rate}" + (f", 위험요인: {risk}" if risk else ""))

            torsion = complications.get("ovarian_torsion", "")
            if torsion:
                comp_parts.append(f"- 난소 비틀림: {torsion}")

            if comp_parts:
                parts.append("\n**합병증 참고**")
                parts.extend(comp_parts)

        # ── v2: 배아 등급 (IVF) ──
        embryo_grading = timeline.get("embryo_grading", {})
        if embryo_grading:
            day5 = embryo_grading.get("day5_blastocyst", {})
            if day5:
                icm = day5.get("ICM_grade", {})
                te = day5.get("TE_grade", {})
                if icm or te:
                    grading_str = "- 배반포 등급 체계:"
                    if icm:
                        grading_str += f"\n  ICM(내세포괴): " + ", ".join(f"{k}={v}" for k, v in icm.items())
                    if te:
                        grading_str += f"\n  TE(영양외배엽): " + ", ".join(f"{k}={v}" for k, v in te.items())
                    parts.append("\n**배아 등급 기준**")
                    parts.append(grading_str)

        # ── v2: 이식 후 관리 (FET) ──
        post_care = timeline.get("post_care", {})
        if post_care:
            parts.append("\n**이식 후 관리**")
            if isinstance(post_care, dict):
                for k, v in post_care.items():
                    if isinstance(v, list):
                        parts.append(f"- {k}: {', '.join(str(i) for i in v)}")
                    elif isinstance(v, str):
                        parts.append(f"- {k}: {v}")

        # ── v2: 호르몬 보충 프로토콜 (FET) ──
        hormone_protocol = timeline.get("hormone_supplement_protocol", {})
        if hormone_protocol:
            parts.append("\n**호르몬 보충 프로토콜**")
            if isinstance(hormone_protocol, dict):
                for phase_name, phase_data in hormone_protocol.items():
                    if isinstance(phase_data, dict):
                        meds = phase_data.get("medications", [])
                        duration = phase_data.get("duration", "")
                        line = f"- {phase_name}"
                        if duration:
                            line += f" ({duration})"
                        if meds:
                            med_names = [m.get("name", "") for m in meds if isinstance(m, dict)]
                            if med_names:
                                line += f": {', '.join(med_names)}"
                        parts.append(line)

        return "\n".join(parts)