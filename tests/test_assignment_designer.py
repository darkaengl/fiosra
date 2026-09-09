from uuid import UUID

import pytest
from httpx import ASGITransport, AsyncClient

from fiosra.mvp.assignment_designer.deambiguator import scope_deambiguator
from fiosra.mvp.assignment_designer.generator import assignment_generator
from fiosra.mvp.assignment_designer.schemas import ClarifyAndScaffoldRequest
from fiosra.mvp.assignment_designer.vault import answer_vault
from fiosra.mvp.main import app


def test_ambiguity_evaluator_triggers_interview():
    """Verify that a vague, open-ended prompt triggers ambiguity > 30% and an interview."""
    raw_prompt = "Tell me about the French revolution."
    diagnosis = scope_deambiguator.evaluate_prompt_ambiguity(raw_prompt, domain="history")

    assert diagnosis.is_ambiguous is True
    assert diagnosis.ambiguity_index > 0.30
    assert len(diagnosis.interview_questions) == 3

    question_ids = [q.question_id for q in diagnosis.interview_questions]
    assert "Q1_TEMPORAL" in question_ids
    assert "Q2_MISCONCEPTIONS" in question_ids
    assert "Q3_EVIDENCE" in question_ids


def test_ambiguity_evaluator_accepts_precise_prompt():
    """Verify that a well-calibrated prompt with temporal and causal anchors is not ambiguous."""
    precise_prompt = (
        "Analyze why France's crown debt crisis between 1787 and 1789 forced Louis XVI to convene "
        "the Estates-General, explaining the tax exemptions held by the nobility."
    )
    diagnosis = scope_deambiguator.evaluate_prompt_ambiguity(precise_prompt, domain="history")

    assert diagnosis.is_ambiguous is False
    assert diagnosis.ambiguity_index <= 0.30
    assert len(diagnosis.interview_questions) == 0


@pytest.mark.asyncio
async def test_scaffolding_and_rubric_generator():
    """Verify generation of 4-rung Socratic hint ladder, NLI rubric rules, and distractors."""
    req = ClarifyAndScaffoldRequest(
        raw_prompt="Write about the 1789 financial crisis.",
        domain="history",
        answers={
            "Q1_TEMPORAL": "Pre-revolutionary fiscal crisis and structural royal debt (1787–May 1789)",
            "Q2_MISCONCEPTIONS": "Attributing the fiscal collapse solely to Marie Antoinette's dresses rather than war debt (MISC_HIST_006)",
            "Q3_EVIDENCE": "Necker's Compte Rendu au Roi and sovereign debt interest tables",
        },
    )
    plan = await assignment_generator.generate_scaffolding_plan(req)

    assert "1787" in plan.clarified_prompt and "1789" in plan.clarified_prompt
    assert len(plan.hint_ladder) == 5  # Rungs 0-3 active + Rung 4 locked bottom-out
    assert plan.hint_ladder[0].level == 0
    assert plan.hint_ladder[1].level == 1
    assert plan.hint_ladder[4].is_locked is True

    # NLI Rubric rules
    assert len(plan.rubric_rules) >= 2
    for rule in plan.rubric_rules:
        assert "criterion_id" in rule
        assert "description" in rule
        assert rule["nli_threshold"] >= 0.80

    # Distractor traps
    assert len(plan.distractor_traps) > 0
    assert "misconception_id" in plan.distractor_traps[0]


def test_answer_vault_isolation():
    """Verify that reference solutions are cryptographically isolated in the Answer Vault."""
    solution = {
        "model_thesis": "France's debt crisis was structural and driven by foreign wars.",
        "points": ["American Revolution debt", "noble exemptions", "50% interest burden"],
    }
    vault_token = answer_vault.lock_solution(
        assignment_id="asgn_test_001",
        question_id="Q_TEST_01",
        reference_solution=solution,
    )

    assert vault_token.startswith("vlt_")
    assert answer_vault.is_locked(vault_token) is True

    # Teacher access retrieves solution
    retrieved = answer_vault.unlock_solution_for_educator(vault_token, teacher_id="prof_mora")
    assert retrieved == solution

    # Invalid token returns None
    assert answer_vault.unlock_solution_for_educator("vlt_invalid", teacher_id="prof_mora") is None


@pytest.mark.asyncio
async def test_assignment_designer_http_endpoints():
    """Verify HTTP API contracts for /assignments router."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Analyze scope of ambiguous prompt
        res = await client.post(
            "/assignments/analyze-scope",
            json={"raw_prompt": "Explain the revolution"},
        )
        assert res.status_code == 200
        diag = res.json()
        assert diag["is_ambiguous"] is True
        assert len(diag["interview_questions"]) == 3

        # 2. Clarify and generate scaffolding plan
        scaffold_res = await client.post(
            "/assignments/clarify-and-scaffold",
            json={
                "raw_prompt": "Explain the revolution",
                "domain": "history",
                "answers": {
                    "Q1_TEMPORAL": "Pre-revolutionary fiscal crisis (1787–1789)",
                    "Q2_MISCONCEPTIONS": "Attributing bankruptcy to royal luxury rather than war debt",
                    "Q3_EVIDENCE": "Necker's Compte Rendu and sovereign debt tables",
                },
            },
        )
        assert scaffold_res.status_code == 200
        plan = scaffold_res.json()
        assert len(plan["hint_ladder"]) == 5

        # 3. Draft assignment (persisting into database with Answer Vault token)
        draft_res = await client.post(
            "/assignments/draft",
            json={
                "topic": "French Revolution Fiscal Crisis",
                "domain": "history",
                "raw_prompt": "Explain the revolution",
                "answers": {
                    "Q1_TEMPORAL": "Pre-revolutionary fiscal crisis (1787–1789)",
                    "Q2_MISCONCEPTIONS": "Attributing bankruptcy to royal luxury rather than war debt",
                    "Q3_EVIDENCE": "Necker's Compte Rendu and sovereign debt tables",
                },
            },
        )
        assert draft_res.status_code == 200
        spec = draft_res.json()
        assignment_id = spec["assignment_id"]
        assert UUID(assignment_id)
        assert spec["vault_token"].startswith("vlt_")
        assert spec["status"] == "draft"

        # 4. Publish assignment
        pub_res = await client.post(f"/assignments/{assignment_id}/publish")
        assert pub_res.status_code == 200
        assert pub_res.json()["status"] == "published"
