import json
import logging
import uuid
from typing import Any
from uuid import UUID

from sqlalchemy import text

from fiosra.mvp.assignment_designer.distractor_engine import distractor_engine
from fiosra.mvp.assignment_designer.schemas import (
    ClarifyAndScaffoldRequest,
    HintRung,
    PublicQuestionSpec,
    QuestionDraftRequest,
    QuestionSpec,
    ScaffoldingPlan,
    ScaffoldingStep,
)
from fiosra.mvp.assignment_designer.vault import answer_vault
from fiosra.mvp.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


class AssignmentGenerator:
    """Builds, persists, and publishes answer-isolated assignment specifications."""

    @classmethod
    async def generate_scaffolding_plan(cls, req: ClarifyAndScaffoldRequest) -> ScaffoldingPlan:
        """Generate a four-rung Socratic ladder and NLI-style rubric criteria."""
        temporal = req.answers.get("Q1_TEMPORAL", "Pre-revolutionary fiscal crisis (1787–1789)")
        misconception_choice = req.answers.get(
            "Q2_MISCONCEPTIONS",
            "Attributing bankruptcy to royal personal luxury rather than sovereign war debt",
        )
        evidence_choice = req.answers.get("Q3_EVIDENCE", "Necker's Compte Rendu and sovereign debt tables")

        clarified_prompt = (
            f"Focusing on {temporal}, analyze the primary structural causes of France's fiscal bankruptcy. "
            f"Using evidence from {evidence_choice}, evaluate why the crown's debt crisis required "
            f"convening the Estates-General, and refute the notion that {misconception_choice}."
        )
        target_kcs = req.target_kcs or [
            "KC_HIST_FRENCH_DEBT",
            "KC_HIST_ANCIEN_REGIME",
            "KC_HIST_ESTATES_GENERAL",
        ]
        hint_ladder = [
            HintRung(
                level=0,
                hint_type="metacognitive",
                content=(
                    "Take a look at your explanation: did you focus on individual court personalities, "
                    "or the broader national financial commitments of the French state?"
                ),
            ),
            HintRung(
                level=1,
                hint_type="conceptual",
                content=(
                    "By 1788, over half of royal state revenue was spent on debt interest from foreign "
                    "military conflicts. What does that tell you about the scale of the problem?"
                ),
            ),
            HintRung(
                level=2,
                hint_type="procedural",
                content=(
                    f"Examine {evidence_choice}. Compare expenditures on war debt against palace expenses, "
                    "then explain the tax immunities held by privileged orders."
                ),
            ),
            HintRung(
                level=3,
                hint_type="worked_analogy",
                content=(
                    "Consider a municipality with large infrastructure loans. Even after cutting luxuries, "
                    "loan interest can cause insolvency unless tax revenue changes. How is that comparable?"
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
                "criterion_id": "rule_structural_debt",
                "label": "Structural War Debt Identification",
                "description": (
                    "Explains that sovereign debt from foreign wars consumed a substantial share "
                    "of the royal budget."
                ),
                "target_kc": "KC_HIST_FRENCH_DEBT",
                "nli_threshold": 0.85,
                "weight": 2.0,
            },
            {
                "criterion_id": "rule_tax_immunity",
                "label": "Fiscal Privilege & Noble Exemption",
                "description": (
                    "Identifies that tax burdens fell on the Third Estate while privileged orders "
                    "held substantial exemptions."
                ),
                "target_kc": "KC_HIST_THREE_ESTATES",
                "nli_threshold": 0.85,
                "weight": 2.0,
            },
            {
                "criterion_id": "rule_source_citation",
                "label": "Primary Evidence Citation",
                "description": f"Grounds claims in references to {evidence_choice}.",
                "target_kc": "KC_HIST_HISTORICAL_ARGUMENT",
                "nli_threshold": 0.80,
                "weight": 1.0,
            },
        ]
        distractors = await distractor_engine.get_distractors_for_kcs(
            target_kcs,
            domain=req.domain,
            limit=3,
        )
        return ScaffoldingPlan(
            clarified_prompt=clarified_prompt,
            domain=req.domain,
            target_kcs=target_kcs,
            hint_ladder=hint_ladder,
            rubric_rules=rubric_rules,
            distractor_traps=distractors,
        )

    @classmethod
    async def draft_question(cls, req: QuestionDraftRequest) -> QuestionSpec:
        """Draft an assignment, lock its reference solution, and persist its public specification."""
        assignment_id = str(uuid.uuid4())
        question_id = f"Q_{uuid.uuid4().hex[:8].upper()}"

        if req.clarified_prompt:
            prompt = req.clarified_prompt
            target_kcs = req.target_kcs or ["KC_HIST_FRENCH_DEBT", "KC_HIST_ESTATES_GENERAL"]
            hint_ladder = req.hint_ladder
            rubric_criteria = req.rubric_rules
            if not hint_ladder or not rubric_criteria:
                fallback_plan = await cls.generate_scaffolding_plan(
                    ClarifyAndScaffoldRequest(
                        raw_prompt=req.raw_prompt or req.clarified_prompt,
                        domain=req.domain,
                        answers=req.answers or {},
                        target_kcs=target_kcs,
                    )
                )
                hint_ladder = hint_ladder or fallback_plan.hint_ladder
                rubric_criteria = rubric_criteria or fallback_plan.rubric_rules
        elif req.raw_prompt and req.answers:
            plan = await cls.generate_scaffolding_plan(
                ClarifyAndScaffoldRequest(raw_prompt=req.raw_prompt, domain=req.domain, answers=req.answers)
            )
            prompt = plan.clarified_prompt
            target_kcs = plan.target_kcs
            hint_ladder = plan.hint_ladder
            rubric_criteria = plan.rubric_rules
        else:
            prompt = req.raw_prompt or f"Analyze the key factors of {req.topic} in {req.domain}."
            plan = await cls.generate_scaffolding_plan(
                ClarifyAndScaffoldRequest(raw_prompt=prompt, domain=req.domain, answers={})
            )
            target_kcs = req.target_kcs or plan.target_kcs
            hint_ladder = plan.hint_ladder
            rubric_criteria = plan.rubric_rules

        subproblems = [
            ScaffoldingStep(
                step_id="step_1",
                step_prompt="Identify the financial origins of the crown debt.",
                target_kc=target_kcs[0],
            ),
            ScaffoldingStep(
                step_id="step_2",
                step_prompt="Explain how institutional arrangements shaped the response to the crisis.",
                target_kc=target_kcs[min(1, len(target_kcs) - 1)],
            ),
        ]
        reference_solution = req.reference_solution or {
            "thesis": "France's bankruptcy was structural, driven by war debt interest and noble tax exemptions.",
            "key_evidence": "Necker's Compte Rendu and war expenditure records",
            "model_argument": "The crown could not service debt without taxing privileged orders.",
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
        )
        insert_sql = text("""
            INSERT INTO assignments (assignment_id, module_id, title, created_by, spec, created_at)
            VALUES (:assignment_id, :module_id, :title, :created_by, CAST(:spec AS JSONB), NOW());
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
        sql = text("SELECT spec FROM assignments WHERE assignment_id = :assignment_id;")
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
            WHERE (:course_id IS NULL OR m.course_id = CAST(:course_id AS UUID))
              AND (:module_id IS NULL OR a.module_id = CAST(:module_id AS UUID))
              AND (:status IS NULL OR a.spec ->> 'status' = :status)
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
        return [cls._to_public_spec(spec if isinstance(spec, dict) else json.loads(spec)) for spec in specs]

    @classmethod
    async def publish_assignment(
        cls,
        assignment_id: UUID | str,
        module_id: UUID | str | None = None,
    ) -> dict[str, Any]:
        """Publish an assignment and optionally bind it to a curriculum module."""
        update_sql = text("""
            UPDATE assignments
            SET module_id = COALESCE(:module_id, module_id),
                spec = jsonb_set(spec, '{status}', '"published"')
            WHERE assignment_id = :assignment_id
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
        return {
            "assignment_id": str(row["assignment_id"]),
            "module_id": str(row["module_id"]) if row["module_id"] else None,
            "title": row["title"],
            "status": "published",
        }


assignment_generator = AssignmentGenerator()
