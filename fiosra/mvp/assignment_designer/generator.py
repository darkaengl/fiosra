import json
import logging
import uuid
from typing import Any, ClassVar
from uuid import UUID

from sqlalchemy import text

from fiosra.mvp.assignment_designer.distractor_engine import distractor_engine
from fiosra.mvp.assignment_designer.schemas import (
    ClarifyAndScaffoldRequest,
    GroundingSource,
    HintRung,
    LLMGenerationMetadata,
    PublicQuestionSpec,
    QuestionDraftRequest,
    QuestionSpec,
    ScaffoldingPlan,
    ScaffoldingStep,
)
from fiosra.mvp.assignment_designer.vault import answer_vault
from fiosra.mvp.database import AsyncSessionLocal
from fiosra.mvp.llm.orchestrator import llm_orchestrator

logger = logging.getLogger(__name__)


class AssignmentGenerator:
    """Build, persist, and publish answer-isolated assignments with teacher-visible grounding."""

    FALLBACK_KCS: ClassVar[dict[str, list[str]]] = {
        "history": ["KC_HIST_HISTORICAL_ARGUMENT", "KC_HIST_PRIMARY_SOURCE_ANALYSIS"],
        "language": ["KC_LANG_CLAIM_CONSTRUCTION", "KC_LANG_EVIDENCE_EVALUATION"],
    }

    @staticmethod
    def _deduplicate(values: list[str]) -> list[str]:
        return list(dict.fromkeys(value for value in values if value))

    @classmethod
    async def _load_grounding_sources(
        cls,
        course_id: UUID | str | None,
        module_id: UUID | str | None,
    ) -> list[GroundingSource]:
        if not course_id:
            return []
        source_sql = text("""
            SELECT chunk_id, title, kc_id, content
            FROM syllabus_chunks
            WHERE course_id = CAST(:course_id AS UUID)
              AND (CAST(:module_id AS UUID) IS NULL OR module_id = CAST(:module_id AS UUID))
            ORDER BY created_at ASC
            LIMIT 5;
        """)
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                source_sql,
                {
                    "course_id": str(course_id),
                    "module_id": str(module_id) if module_id else None,
                },
            )
            rows = result.mappings().all()
        return [
            GroundingSource(
                chunk_id=str(row["chunk_id"]),
                title=row["title"] or "Assigned course material",
                kc_id=row["kc_id"],
                excerpt=(row["content"] or "").strip()[:280],
            )
            for row in rows
        ]

    @classmethod
    async def generate_scaffolding_plan(cls, req: ClarifyAndScaffoldRequest) -> ScaffoldingPlan:
        """Generate an answer-blind scaffold constrained to the selected course corpus when present."""
        grounding_sources = await cls._load_grounding_sources(req.course_id, req.module_id)
        source_titles = ", ".join(source.title for source in grounding_sources[:2])
        temporal = req.answers.get("Q1_TEMPORAL", "").strip()
        misconception = req.answers.get("Q2_MISCONCEPTIONS", "").strip()
        evidence_anchor = req.answers.get("Q3_EVIDENCE", "").strip()

        evidence = evidence_anchor or source_titles or "the assigned course materials"
        scope = temporal or "the setting and boundaries named in the educator's prompt"
        cognitive_trap = misconception or "moving from an observation to an unsupported broad conclusion"
        base_prompt = req.raw_prompt.strip()
        clarification = (
            f"Work within {scope}. Use {evidence} to distinguish direct observations from justified inferences, "
            f"and test the risk of {cognitive_trap}."
        )
        clarified_prompt = base_prompt if clarification.lower() in base_prompt.lower() else f"{base_prompt}\n\n{clarification}"
        source_context = "\n".join(
            f"- {source.title}: {source.excerpt}" for source in grounding_sources
        ) or "No course source is attached; preserve the educator's stated evidence requirement."
        generation = await llm_orchestrator.enhance(
            purpose="assignment_scaffold_prompt",
            system_prompt=(
                "You refine an educator-authored student task for a Socratic reasoning workspace. "
                "Return one or two concise prose sentences only: no markdown, headings, labels, bullets, "
                "numbered lists, claims, or evidence examples. Preserve the stated learning scope, use only "
                "the supplied public sources, require a bounded claim with evidence and uncertainty, and do "
                "not supply an answer, thesis, rubric, solution, or grading judgment."
            ),
            user_prompt=(
                f"Educator draft:\n{base_prompt}\n\nRequired boundaries:\n{clarification}\n\n"
                f"Public course context:\n{source_context}"
            ),
            deterministic_fallback=clarified_prompt,
            pseudonymous_seed=f"assignment:{req.course_id or 'unbound'}:{req.module_id or 'unbound'}:{base_prompt}",
            max_characters=1600,
            max_tokens=240,
        )
        clarified_prompt = generation.content

        source_kcs = [source.kc_id for source in grounding_sources if source.kc_id]
        target_kcs = cls._deduplicate(req.target_kcs or source_kcs)
        if not target_kcs:
            target_kcs = cls.FALLBACK_KCS.get(req.domain.lower(), ["KC_GENERAL"])

        source_label = source_titles or evidence
        target_label = target_kcs[0]
        hint_ladder = [
            HintRung(
                level=0,
                hint_type="metacognitive",
                content=(
                    "State a provisional claim, then name the observation that most directly supports it. "
                    "What remains uncertain?"
                ),
            ),
            HintRung(
                level=1,
                hint_type="conceptual",
                content=(
                    f"Return to {source_label}. Which detail is evidence, and which conclusion would require an inference?"
                ),
            ),
            HintRung(
                level=2,
                hint_type="procedural",
                content=(
                    f"Write one sentence for the observation, one for the claim it supports, and one for an "
                    f"alternative explanation. Use the task boundary: {scope}."
                ),
            ),
            HintRung(
                level=3,
                hint_type="worked_analogy",
                content=(
                    "A map can show that a road connects two places, but it cannot alone prove why the road was built. "
                    "Apply that distinction between what the source shows and what you infer."
                ),
            ),
            HintRung(
                level=4,
                hint_type="bottom_out",
                content="Bottom-out full solution: locked by default and available only to an educator.",
                is_locked=True,
            ),
        ]
        rubric_rules = [
            {
                "criterion_id": "rule_claim_precision",
                "label": "Bounded claim",
                "description": "Makes a defensible claim that remains within the task's stated scope.",
                "target_kc": target_label,
                "nli_threshold": 0.80,
                "weight": 2.0,
            },
            {
                "criterion_id": "rule_evidence_reasoning",
                "label": "Evidence and inference",
                "description": f"Uses {evidence} and distinguishes direct support from a broader inference.",
                "target_kc": target_kcs[min(1, len(target_kcs) - 1)],
                "nli_threshold": 0.80,
                "weight": 2.0,
            },
            {
                "criterion_id": "rule_alternative_explanation",
                "label": "Reasoning under uncertainty",
                "description": f"Addresses the risk of {cognitive_trap} by testing an alternative explanation.",
                "target_kc": target_label,
                "nli_threshold": 0.80,
                "weight": 1.0,
            },
        ]
        distractors = await distractor_engine.get_distractors_for_kcs(
            target_kcs,
            domain=req.domain.lower(),
            limit=3,
        )
        return ScaffoldingPlan(
            clarified_prompt=clarified_prompt,
            domain=req.domain,
            target_kcs=target_kcs,
            hint_ladder=hint_ladder,
            rubric_rules=rubric_rules,
            distractor_traps=distractors,
            grounding_mode="course_grounded" if grounding_sources else "generic",
            grounding_sources=grounding_sources,
            generation_metadata=LLMGenerationMetadata.model_validate(generation.metadata.as_dict()),
        )

    @classmethod
    async def draft_question(cls, req: QuestionDraftRequest) -> QuestionSpec:
        """Persist an assignment while retaining reference solutions only in the Answer Vault."""
        assignment_id = str(uuid.uuid4())
        question_id = f"Q_{uuid.uuid4().hex[:8].upper()}"

        fallback_plan: ScaffoldingPlan | None = None
        generation_metadata = req.generation_metadata
        if req.clarified_prompt:
            prompt = req.clarified_prompt
            target_kcs = req.target_kcs or []
            hint_ladder = req.hint_ladder
            rubric_criteria = req.rubric_rules
            grounding_mode = req.grounding_mode
            grounding_sources = req.grounding_sources
            if not target_kcs or not hint_ladder or not rubric_criteria:
                fallback_plan = await cls.generate_scaffolding_plan(
                    ClarifyAndScaffoldRequest(
                        raw_prompt=req.raw_prompt or req.clarified_prompt,
                        domain=req.domain,
                        answers=req.answers or {},
                        target_kcs=target_kcs,
                        course_id=req.course_id,
                        module_id=req.module_id,
                    )
                )
                target_kcs = target_kcs or fallback_plan.target_kcs
                hint_ladder = hint_ladder or fallback_plan.hint_ladder
                rubric_criteria = rubric_criteria or fallback_plan.rubric_rules
                if not grounding_sources:
                    grounding_sources = fallback_plan.grounding_sources
                    grounding_mode = fallback_plan.grounding_mode
                generation_metadata = generation_metadata or fallback_plan.generation_metadata
        else:
            fallback_plan = await cls.generate_scaffolding_plan(
                ClarifyAndScaffoldRequest(
                    raw_prompt=req.raw_prompt or f"Develop an evidence-based response about {req.topic}.",
                    domain=req.domain,
                    answers=req.answers or {},
                    target_kcs=req.target_kcs or [],
                    course_id=req.course_id,
                    module_id=req.module_id,
                )
            )
            prompt = fallback_plan.clarified_prompt
            target_kcs = fallback_plan.target_kcs
            hint_ladder = fallback_plan.hint_ladder
            rubric_criteria = fallback_plan.rubric_rules
            grounding_mode = fallback_plan.grounding_mode
            grounding_sources = fallback_plan.grounding_sources
            generation_metadata = fallback_plan.generation_metadata

        subproblems = [
            ScaffoldingStep(
                step_id="step_1",
                step_prompt="Identify the source observation or course evidence that bears most directly on your claim.",
                target_kc=target_kcs[0],
            ),
            ScaffoldingStep(
                step_id="step_2",
                step_prompt="Explain the inference your evidence supports and name a limit or alternative explanation.",
                target_kc=target_kcs[min(1, len(target_kcs) - 1)],
            ),
        ]
        reference_solution = req.reference_solution or {
            "thesis": "A defensible response makes a bounded claim and explains how assigned evidence supports it.",
            "key_evidence": "Specific details from the teacher-selected source corpus",
            "model_argument": "The response distinguishes direct observation from inference and tests a plausible alternative.",
        }
        vault_token = answer_vault.lock_solution(
            assignment_id=assignment_id,
            question_id=question_id,
            reference_solution=reference_solution,
        )
        spec = QuestionSpec(
            question_id=question_id,
            assignment_id=assignment_id,
            prompt=prompt,
            domain=req.domain,
            target_kcs=target_kcs,
            subproblems=subproblems,
            hint_ladder=hint_ladder,
            rubric_criteria=rubric_criteria,
            vault_token=vault_token,
            status="draft",
            grounding_mode=grounding_mode,
            grounding_sources=grounding_sources,
            generation_metadata=generation_metadata,
            canvas_sections=req.canvas_sections,
        )
        insert_sql = text("""
            INSERT INTO assignments (assignment_id, module_id, title, created_by, spec, created_at)
            VALUES (CAST(:assignment_id AS UUID), CAST(:module_id AS UUID), :title, :created_by, CAST(:spec AS JSONB), NOW());
        """)
        async with AsyncSessionLocal() as session:
            await session.execute(
                insert_sql,
                {
                    "assignment_id": assignment_id,
                    "module_id": str(req.module_id) if req.module_id else None,
                    "title": req.topic,
                    "created_by": req.created_by,
                    "spec": json.dumps(spec.model_dump()),
                },
            )
            await session.commit()
        logger.info("Persisted assignment %s to database in draft state.", assignment_id)
        return spec

    @staticmethod
    def _to_public_spec(spec: dict[str, Any]) -> PublicQuestionSpec:
        safe_spec = dict(spec)
        safe_spec.pop("vault_token", None)
        return PublicQuestionSpec.model_validate(safe_spec)

    @classmethod
    async def get_public_assignment(cls, assignment_id: UUID | str) -> PublicQuestionSpec | None:
        sql = text("SELECT spec FROM assignments WHERE assignment_id = CAST(:assignment_id AS UUID);")
        async with AsyncSessionLocal() as session:
            result = await session.execute(sql, {"assignment_id": str(assignment_id)})
            spec = result.scalar()
        if not spec:
            return None
        return cls._to_public_spec(spec if isinstance(spec, dict) else json.loads(spec))

    @classmethod
    async def list_public_assignments(
        cls,
        course_id: UUID | str | None = None,
        module_id: UUID | str | None = None,
        status: str | None = None,
    ) -> list[PublicQuestionSpec]:
        sql = text("""
            SELECT a.spec
            FROM assignments a
            LEFT JOIN modules m ON a.module_id = m.module_id
            WHERE (CAST(:course_id AS UUID) IS NULL OR m.course_id = CAST(:course_id AS UUID))
              AND (CAST(:module_id AS UUID) IS NULL OR a.module_id = CAST(:module_id AS UUID))
              AND (CAST(:status AS VARCHAR) IS NULL OR a.spec ->> 'status' = CAST(:status AS VARCHAR))
            ORDER BY a.created_at DESC;
        """)
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                sql,
                {
                    "course_id": str(course_id) if course_id else None,
                    "module_id": str(module_id) if module_id else None,
                    "status": status,
                },
            )
            specs = result.scalars().all()
        valid: list[PublicQuestionSpec] = []
        for spec in specs:
            try:
                data = spec if isinstance(spec, dict) else json.loads(spec)
                if isinstance(data, dict) and "question_id" in data:
                    valid.append(cls._to_public_spec(data))
            except Exception as e:
                logger.warning("Skipping invalid assignment spec: %s", e)
        return valid

    @classmethod
    async def publish_assignment(
        cls,
        assignment_id: UUID | str,
        module_id: UUID | str | None = None,
    ) -> dict[str, Any]:
        """Publish an assignment only when its same student-safe projection is retrievable."""
        readiness_sql = text("""
            SELECT module_id, spec
            FROM assignments
            WHERE assignment_id = CAST(:assignment_id AS UUID);
        """)
        async with AsyncSessionLocal() as session:
            readiness_result = await session.execute(
                readiness_sql,
                {"assignment_id": str(assignment_id)},
            )
            readiness_row = readiness_result.mappings().first()
        if not readiness_row:
            raise ValueError(f"Assignment '{assignment_id}' not found.")

        active_module_id = module_id or readiness_row["module_id"]
        private_spec = readiness_row["spec"]
        private_spec = private_spec if isinstance(private_spec, dict) else json.loads(private_spec)
        if active_module_id and (
            private_spec.get("grounding_mode") != "course_grounded"
            or not private_spec.get("grounding_sources")
        ):
            raise RuntimeError(
                "Attach and ground at least one course source before publishing a module assignment."
            )

        update_sql = text("""
            UPDATE assignments
            SET module_id = COALESCE(CAST(:module_id AS UUID), module_id),
                spec = jsonb_set(spec, '{status}', '"published"')
            WHERE assignment_id = CAST(:assignment_id AS UUID)
            RETURNING assignment_id, module_id, title;
        """)
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                update_sql,
                {
                    "assignment_id": str(assignment_id),
                    "module_id": str(module_id) if module_id else None,
                },
            )
            row = result.mappings().first()
            if not row:
                raise ValueError(f"Assignment '{assignment_id}' not found.")
            await session.commit()

        public_spec = await cls.get_public_assignment(assignment_id)
        if not public_spec or public_spec.status != "published":
            raise RuntimeError("The assignment could not be verified through the student-safe publication contract.")
        return {
            "assignment_id": str(row["assignment_id"]),
            "module_id": str(row["module_id"]) if row["module_id"] else None,
            "title": row["title"],
            "status": "published",
        }


assignment_generator = AssignmentGenerator()
