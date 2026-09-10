import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from fiosra.mvp.main import app


@pytest.mark.asyncio
async def test_session_capability_binds_dialogue_events_and_lifecycle():
    """A session capability authorizes one learner/session and blocks untyped or stale writes."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        student_id = f"capability_student_{uuid.uuid4().hex[:8]}"
        created = await client.post(
            "/events/session",
            json={"student_id": student_id, "current_question_id": "Q1"},
        )
        assert created.status_code == 200
        session = created.json()
        session_id = session["session_id"]
        headers = {"X-Fiosra-Session-Token": session["access_token"]}

        denied_dialogue = await client.post(
            "/dialogue/message",
            json={
                "session_id": session_id,
                "student_id": student_id,
                "question_id": "Q1",
                "question_prompt": "Explain the evidence for a historical claim.",
                "student_input": "I think I should separate observations from inferences.",
            },
        )
        assert denied_dialogue.status_code == 403

        denied_other_student = await client.post(
            "/dialogue/message",
            headers=headers,
            json={
                "session_id": session_id,
                "student_id": "another_student",
                "question_id": "Q1",
                "question_prompt": "Explain the evidence for a historical claim.",
                "student_input": "I think I should separate observations from inferences.",
            },
        )
        assert denied_other_student.status_code == 403

        denied_question_change = await client.post(
            "/dialogue/message",
            headers=headers,
            json={
                "session_id": session_id,
                "student_id": student_id,
                "question_id": "Q2",
                "question_prompt": "Explain the evidence for a historical claim.",
                "student_input": "I think I should separate observations from inferences.",
            },
        )
        assert denied_question_change.status_code == 409

        rejected_event = await client.post(
            "/events/log",
            headers=headers,
            json={
                "session_id": session_id,
                "student_id": student_id,
                "question_id": "Q1",
                "event_type": "misconception_flagged",
                "payload": {"kc_id": "forged"},
            },
        )
        assert rejected_event.status_code == 422

        recorded_reflection = await client.post(
            "/events/log",
            headers=headers,
            json={
                "session_id": session_id,
                "student_id": student_id,
                "question_id": "Q1",
                "event_type": "speech_to_thought_crystallized",
                "payload": {"transcript": "I will identify source observations before I infer a conclusion."},
            },
        )
        assert recorded_reflection.status_code == 200

        submitted = await client.post(f"/events/session/{session_id}/submit", headers=headers)
        assert submitted.status_code == 200
        stale_event = await client.post(
            "/events/log",
            headers=headers,
            json={
                "session_id": session_id,
                "student_id": student_id,
                "question_id": "Q1",
                "event_type": "speech_to_thought_crystallized",
                "payload": {"transcript": "A post-submission mutation attempt."},
            },
        )
        assert stale_event.status_code == 409


@pytest.mark.asyncio
async def test_assignment_bound_session_requires_published_matching_question():
    """A browser cannot start a student session for a draft or substitute its own question identity."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        draft = await client.post(
            "/assignments/draft",
            json={
                "topic": "Draft only",
                "domain": "history",
                "raw_prompt": "Analyze an evidence-based historical claim.",
                "answers": {
                    "Q1_TEMPORAL": "a bounded historical period",
                    "Q2_MISCONCEPTIONS": "single-cause explanation",
                    "Q3_EVIDENCE": "a course source",
                },
            },
        )
        assert draft.status_code == 200
        draft_spec = draft.json()
        draft_session = await client.post(
            "/events/session",
            json={
                "student_id": "draft_session_student",
                "assignment_id": draft_spec["assignment_id"],
                "current_question_id": draft_spec["question_id"],
            },
        )
        assert draft_session.status_code == 422

        published = await client.post(f"/assignments/{draft_spec['assignment_id']}/publish")
        assert published.status_code == 200
        mismatched_question = await client.post(
            "/events/session",
            json={
                "student_id": "published_session_student",
                "assignment_id": draft_spec["assignment_id"],
                "current_question_id": "browser_supplied_other_question",
            },
        )
        assert mismatched_question.status_code == 409

        started = await client.post(
            "/events/session",
            json={
                "student_id": "published_session_student",
                "assignment_id": draft_spec["assignment_id"],
                "current_question_id": draft_spec["question_id"],
            },
        )
        assert started.status_code == 200
        invalid_section = await client.post(
            "/dialogue/message",
            headers={"X-Fiosra-Session-Token": started.json()["access_token"]},
            json={
                "session_id": started.json()["session_id"],
                "student_id": "published_session_student",
                "assignment_id": draft_spec["assignment_id"],
                "question_id": draft_spec["question_id"],
                "active_section_id": "not_declared_by_assignment",
                "question_prompt": "A browser-supplied prompt that must not become authoritative.",
                "student_input": "I want to distinguish direct observations from an inference.",
            },
        )
        assert invalid_section.status_code == 409
