import pytest
from httpx import ASGITransport, AsyncClient

from fiosra.mvp.event_store import event_store
from fiosra.mvp.evidence_dossier.synthesizer import evidence_dossier_synthesizer
from fiosra.mvp.main import app
from fiosra.mvp.verifiers.text_claim import NLILabel, text_claim_verifier


def test_text_claim_verifier_entailment():
    """Verify that student text supporting rubric requirement yields ENTAILED."""
    premise = (
        "The French fiscal collapse was driven by massive foreign war debt from the American "
        "Revolution and regressive tax exemptions for the nobility and clergy."
    )
    hypothesis = "Explains underlying institutional or fiscal causes rather than sole personal or bread triggers."

    result = text_claim_verifier.verify_claim(premise=premise, hypothesis=hypothesis)
    assert result.label == NLILabel.ENTAILED
    assert result.confidence >= 0.70
    assert result.latency_ms < 50.0


def test_text_claim_verifier_contradiction():
    """Verify that contradictory or negated student claims yield CONTRADICTION."""
    premise = "There was no debt from foreign wars and the clergy paid all taxes."
    hypothesis = "Explains foreign war debt and tax exemptions."

    result = text_claim_verifier.verify_claim(premise=premise, hypothesis=hypothesis)
    assert result.label == NLILabel.CONTRADICTION
    assert result.confidence >= 0.65


def test_text_claim_verifier_neutral():
    """Verify that unrelated student text yields NEUTRAL."""
    premise = "I had pizza for lunch and the weather was sunny outside."
    hypothesis = "Explains the structural tax structure of the Ancien Regime."

    result = text_claim_verifier.verify_claim(premise=premise, hypothesis=hypothesis)
    assert result.label == NLILabel.NEUTRAL


def test_text_claim_verifier_latency_sla():
    """Verify sub-50ms inference latency SLA across 25 evaluations."""
    premise = "The Third Estate demanded vote by head because voting by order guaranteed a 2 to 1 loss."
    hypothesis = "Demands voting by head to counteract voting by order."

    latencies = []
    for _ in range(25):
        res = text_claim_verifier.verify_claim(premise=premise, hypothesis=hypothesis)
        latencies.append(res.latency_ms)

    avg_latency = sum(latencies) / len(latencies)
    assert avg_latency < 50.0, f"Average latency ({avg_latency:.2f}ms) exceeded 50ms SLA"


@pytest.mark.asyncio
async def test_dossier_synthesis_pipeline():
    """
    Verify AutoSCORE Two-Stage Evidence Packet Z generation from raw events:
    - Stage 1: Extracts reasoning traces and verbatim quotes with event IDs.
    - Stage 2: Pre-scores quotes against rubric dimensions and computes metrics.
    """
    session_id = await event_store.create_session(
        student_id="student_clara_10",
        current_question_id="q1",
    )

    # 1. First attempt: student triggers misconception
    await event_store.log_event(
        session_id=session_id,
        student_id="student_clara_10",
        question_id="q1",
        event_type="student_prompt_submitted",
        payload={"student_input": "France went broke because the King bought too many dresses."},
    )

    # 2. Tutor delivers Socratic hint
    await event_store.log_event(
        session_id=session_id,
        student_id="student_clara_10",
        question_id="q1",
        event_type="hint_delivered",
        payload={
            "hint_rung": 1,
            "response_text": "Look at where royal tax revenue actually went: war debt interest.",
            "matched_misconception_id": "MISC_HIST_006",
        },
    )

    # 3. Second attempt: student provides evidence-backed explanation
    await event_store.log_event(
        session_id=session_id,
        student_id="student_clara_10",
        question_id="q1",
        event_type="student_prompt_submitted",
        payload={
            "student_input": (
                "France had massive sovereign debt from financing the Seven Years' War and American "
                "Revolution, while the nobility paid no direct taxes."
            ),
        },
    )

    session_info = await event_store.get_session_details(session_id)
    events = await event_store.get_session_events(session_id)

    # Synthesize dossier
    dossier = evidence_dossier_synthesizer.synthesize_dossier(
        session_info=session_info,
        events=events,
    )

    assert "packet_id" in dossier
    assert dossier["student_id"] == "student_clara_10"
    assert "executive_summary" in dossier
    assert "per_question_evidence" in dossier

    q1_evidence = dossier["per_question_evidence"][0]
    assert q1_evidence["question_id"] == "q1"
    assert q1_evidence["process_trace"]["total_attempts"] == 2
    assert q1_evidence["process_trace"]["hints_consumed"] == 1
    assert "MISC_HIST_006" in q1_evidence["process_trace"]["misconceptions_triggered"]

    # Verbatim citations must link back to event IDs
    rubric_ev = q1_evidence["rubric_evidence"]
    assert len(rubric_ev) >= 2
    for crit_data in rubric_ev.values():
        assert "Verbatim quote:" in crit_data["evidence"]
        assert "Event #" in crit_data["evidence"]


@pytest.mark.asyncio
async def test_evidence_router_endpoints():
    """Verify HTTP API contracts for /evidence endpoints including 1-click grade approval."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create session and add interaction
        session_id = await event_store.create_session(student_id="student_julian_22")
        await event_store.log_event(
            session_id=session_id,
            student_id="student_julian_22",
            question_id="q1",
            event_type="student_prompt_submitted",
            payload={"student_input": "The Estates-General voting by order blocked Third Estate reforms."},
        )

        # 1. Fetch executive review dossier
        dossier_res = await client.get(f"/evidence/dossier/{session_id}")
        assert dossier_res.status_code == 200
        dossier_data = dossier_res.json()
        assert dossier_data["student_id"] == "student_julian_22"
        assert "suggested_grade" in dossier_data["executive_summary"]

        # 2. Fetch reasoning trace for student canvas
        trace_res = await client.get(f"/evidence/trace/{session_id}")
        assert trace_res.status_code == 200
        trace_data = trace_res.json()
        assert trace_data["total_nodes"] >= 1
        assert "trace_nodes" in trace_data

        # 3. 1-Click Sovereign Educator Grade Approval with override
        finalise_res = await client.post(
            f"/evidence/dossier/{session_id}/finalise-grade",
            json={
                "approved_grade": "A",
                "teacher_id": "prof_archambault",
                "teacher_override": True,
                "feedback_comments": "Clear analysis of the procedural deadlock at Versailles.",
            },
        )
        assert finalise_res.status_code == 200
        finalise_data = finalise_res.json()
        assert finalise_data["status"] == "completed"
        assert finalise_data["final_grade"] == "A"
        assert finalise_data["teacher_override"] is True

        # 4. Verify session state updated in database
        updated_session = await event_store.get_session_details(session_id)
        assert updated_session["status"] == "completed"
        assert updated_session["completed_at"] is not None

        # 5. Verify sovereign grade event recorded in flight recorder
        events = await event_store.get_session_events(session_id)
        event_types = [e["event_type"] for e in events]
        assert "grade_finalised_by_educator" in event_types
