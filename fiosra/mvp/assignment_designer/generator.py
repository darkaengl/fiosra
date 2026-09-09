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
    QuestionDraftRequest,
    QuestionSpec,
    ScaffoldingPlan,
    ScaffoldingStep,
)
from fiosra.mvp.assignment_designer.vault import answer_vault
from fiosra.mvp.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


class AssignmentGenerator:
    """
    RAG-grounded and Socratic alignment assignment generator.
    Transforms raw or de-ambiguated prompts into machine-verifiable assignments,
    4-rung hint ladders, and locks reference solutions into the Answer Vault.
    """

    @classmethod
    async def generate_scaffolding_plan(
        cls,
        req: ClarifyAndScaffoldRequest,
    ) -> ScaffoldingPlan:
        """
        Generates a 4-rung Socratic hint ladder and verifiable NLI rubric rules
        incorporating educator alignment interview choices.
        """
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

        # 4-Rung Socratic Hint Ladder
        hint_ladder = [
            HintRung(
                level=0,
                hint_type="metacognitive",
                content="Take a look at your explanation: did you focus on individual court personalities, or the broader national financial commitments of the French state?",
                is_locked=False,
            ),
            HintRung(
                level=1,
                hint_type="conceptual",
                content="Remember: by 1788, over 50% of royal state revenue was spent solely on debt interest from foreign military conflicts (such as the Seven Years' War and American Revolution).",
                is_locked=False,
            ),
            HintRung(
                level=2,
                hint_type="procedural",
                content=f"Examine {evidence_choice}. Compare the expenditures on war debt against palace expenses, and explain the tax immunities held by the nobility.",
                is_locked=False,
            ),
            HintRung(
                level=3,
                hint_type="worked_analogy",
                content="Consider a municipal government that takes out massive infrastructure loans: even if its council cuts luxury spending, the loan interest alone will cause insolvency without broad tax reform.",
                is_locked=False,
            ),
            HintRung(
                level=4,
                hint_type="bottom_out",
                content="Bottom-out full solution: Locked by default. Requires educator override in teacher dashboard.",
                is_locked=True,
            ),
        ]

        # Verifiable NLI Rubric Rules
        rubric_rules = [
            {
                "criterion_id": "rule_structural_debt",
                "label": "Structural War Debt Identification",
                "description": "Explains that sovereign debt from foreign wars (American Revolution, Seven Years' War) consumed over half the royal budget.",
                "target_kc": "KC_HIST_FRENCH_DEBT",
                "nli_threshold": 0.85,
                "weight": 2.0,
            },
            {
                "criterion_id": "rule_tax_immunity",
                "label": "Fiscal Privilege & Noble Exemption",
                "description": "Identifies that the tax system placed burdens on the Third Estate while the nobility and clergy held exemptions.",
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

        # Generate cognitive traps / distractors
        distractors = await distractor_engine.get_distractors_for_kcs(target_kcs, domain=req.domain, limit=3)

        return ScaffoldingPlan(
            clarified_prompt=clarified_prompt,
            domain=req.domain,
            target_kcs=target_kcs,
            hint_ladder=hint_ladder,
            rubric_rules=rubric_rules,
            distractor_traps=distractors,
        )

    @classmethod
    async def draft_question(
        cls,
        req: QuestionDraftRequest,
    ) -> QuestionSpec:
        """
        Drafts an assignment, isolates reference solutions in the Answer Vault,
        and saves the specification to the PostgreSQL assignments table.
        """
        assignment_id = str(uuid.uuid4())
        question_id = f"Q_{uuid.uuid4().hex[:8].upper()}"

        if req.raw_prompt and req.answers:
            scaffold_req = ClarifyAndScaffoldRequest(
                raw_prompt=req.raw_prompt,
                domain=req.domain,
                answers=req.answers,
            )
            plan = await cls.generate_scaffolding_plan(scaffold_req)
            prompt = plan.clarified_prompt
            target_kcs = plan.target_kcs
            hint_ladder = plan.hint_ladder
            rubric_criteria = plan.rubric_rules
        else:
            prompt = f"Analyze the key factors of {req.topic} in {req.domain}."
            target_kcs = ["KC_HIST_FRENCH_DEBT", "KC_HIST_ESTATES_GENERAL"]
            scaffold_req = ClarifyAndScaffoldRequest(raw_prompt=prompt, domain=req.domain, answers={})
            plan = await cls.generate_scaffolding_plan(scaffold_req)
            hint_ladder = plan.hint_ladder
            rubric_criteria = plan.rubric_rules

        subproblems = [
            ScaffoldingStep(
                step_id="step_1",
                step_prompt="Identify the financial origins of the crown debt.",
                target_kc="KC_HIST_FRENCH_DEBT",
            ),
            ScaffoldingStep(
                step_id="step_2",
                step_prompt="Explain why the Parlement of Paris blocked tax reform.",
                target_kc="KC_HIST_ANCIEN_REGIME",
            ),
        ]

        reference_solution = {
            "thesis": "France's bankruptcy was structural, driven by war debt interest exceeding 50% of revenue and noble tax exemptions.",
            "key_evidence": "Necker's Compte Rendu and war expenditure records",
            "model_argument": "The crown could not service debt without taxing privileged orders, forcing convocation of Estates-General.",
        }

        # Lock reference solution into Answer Vault
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

        # Persist assignment into PostgreSQL
        insert_sql = text("""
            INSERT INTO assignments (
                assignment_id,
                module_id,
                title,
                created_by,
                spec,
                created_at
            ) VALUES (
                :assignment_id,
                :module_id,
                :title,
                :created_by,
                CAST(:spec AS JSONB),
                NOW()
            );
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

        logger.info(f"Persisted assignment {assignment_id} to database in draft state.")
        return spec

    @classmethod
    async def publish_assignment(
        cls,
        assignment_id: UUID | str,
        module_id: UUID | str | None = None,
    ) -> dict[str, Any]:
        """
        Publishes an assignment and optionally binds it to a curriculum module.
        """
        update_sql = text("""
            UPDATE assignments
            SET module_id = COALESCE(:module_id, module_id),
                spec = jsonb_set(spec, '{status}', '"published"')
            WHERE assignment_id = :assignment_id
            RETURNING assignment_id, module_id, title, spec;
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
