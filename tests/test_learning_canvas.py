import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from fiosra.mvp.main import app


async def create_published_grounded_assignment(client: AsyncClient) -> tuple[dict, str]:
    course_response = await client.post(
        "/courses",
        json={
            "title": f"HIST Canvas {uuid.uuid4().hex[:8]}",
            "domain": "History",
            "created_by": "canvas_test_teacher",
        },
    )
    assert course_response.status_code == 201
    course_id = course_response.json()["course_id"]
    module_response = await client.post(
        f"/courses/{course_id}/modules",
        json={"title": "Source reasoning", "position": 1},
    )
    assert module_response.status_code == 201
    module_id = module_response.json()["module_id"]
    source_response = await client.post(
        f"/courses/{course_id}/modules/{module_id}/resources",
        json={
            "title": "Excavation report",
            "content": (
                "The report describes brick drains connecting houses with wider channels. "
                "It does not identify who organized the construction."
            ),
            "resource_type": "primary_source",
        },
    )
    assert source_response.status_code == 201
    source = source_response.json()[0]
    scaffold_response = await client.post(
        "/assignments/clarify-and-scaffold",
        json={
            "raw_prompt": "What can drainage infrastructure reveal about urban planning?",
            "domain": "history",
            "course_id": course_id,
            "module_id": module_id,
            "answers": {
                "Q1_TEMPORAL": "Mohenjo-daro during the Mature Harappan period",
                "Q2_MISCONCEPTIONS": "treating one observation as proof of civic administration",
                "Q3_EVIDENCE": "the excavation report",
            },
        },
    )
    assert scaffold_response.status_code == 200
    scaffold = scaffold_response.json()
    draft_response = await client.post(
        "/assignments/draft",
        json={
            "topic": "Canvas source reasoning",
            "domain": "history",
            "course_id": course_id,
            "module_id": module_id,
            "clarified_prompt": scaffold["clarified_prompt"],
            "target_kcs": scaffold["target_kcs"],
            "hint_ladder": scaffold["hint_ladder"],
            "rubric_rules": scaffold["rubric_rules"],
            "grounding_mode": scaffold["grounding_mode"],
            "grounding_sources": scaffold["grounding_sources"],
        },
    )
    assert draft_response.status_code == 200
    assignment = draft_response.json()
    publish_response = await client.post(f"/assignments/{assignment['assignment_id']}/publish")
    assert publish_response.status_code == 200
    return assignment, source["chunk_id"]


@pytest.mark.asyncio
async def test_canvas_is_student_owned_versioned_and_source_grounded():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        assignment, source_chunk_id = await create_published_grounded_assignment(client)
        session_response = await client.post(
            "/events/session",
            json={
                "student_id": f"canvas_student_{uuid.uuid4().hex[:8]}",
                "assignment_id": assignment["assignment_id"],
                "current_question_id": assignment["question_id"],
            },
        )
        assert session_response.status_code == 200
        session = session_response.json()
        assert session["access_token"]
        session_id = session["session_id"]
        headers = {"X-Fiosra-Session-Token": session["access_token"]}

        forbidden_state = await client.get(f"/learning-canvas/sessions/{session_id}")
        assert forbidden_state.status_code == 403
        state_response = await client.get(f"/learning-canvas/sessions/{session_id}", headers=headers)
        assert state_response.status_code == 200
        state = state_response.json()
        assert [section["section_id"] for section in state["sections"]] == [
            "working_claim",
            "source_observations",
            "reasoning",
            "alternative_explanation",
            "revision_reflection",
        ]
        assert all(draft["revision"] == 0 for draft in state["drafts"])

        invalid_source_save = await client.put(
            f"/learning-canvas/sessions/{session_id}/sections/working_claim",
            headers=headers,
            json={
                "text": "The drains suggest coordination, but not a certain form of government.",
                "base_revision": 0,
                "source_references": [{"chunk_id": str(uuid.uuid4()), "rationale": "not approved"}],
            },
        )
        assert invalid_source_save.status_code == 422

        invalid_quote_save = await client.put(
            f"/learning-canvas/sessions/{session_id}/sections/working_claim",
            headers=headers,
            json={
                "text": "A claim with a fabricated quotation.",
                "base_revision": 0,
                "source_references": [
                    {"chunk_id": source_chunk_id, "quote": "A claim absent from the excerpt."}
                ],
            },
        )
        assert invalid_quote_save.status_code == 422

        save_response = await client.put(
            f"/learning-canvas/sessions/{session_id}/sections/working_claim",
            headers=headers,
            json={
                "text": "The drains suggest coordination, but not a certain form of government.",
                "base_revision": 0,
                "source_references": [
                    {
                        "chunk_id": source_chunk_id,
                        "quote": "connecting houses with wider channels",
                        "rationale": "This is a direct observation from the report.",
                    }
                ],
            },
        )
        assert save_response.status_code == 200
        saved = save_response.json()
        assert saved["revision"] == 1
        assert saved["author_type"] == "student"

        stale_save = await client.put(
            f"/learning-canvas/sessions/{session_id}/sections/working_claim",
            headers=headers,
            json={"text": "A stale overwrite.", "base_revision": 0},
        )
        assert stale_save.status_code == 409

        suggestion_response = await client.post(
            f"/learning-canvas/sessions/{session_id}/suggestions",
            headers=headers,
            json={"section_id": "working_claim", "kind": "writing_frame", "base_revision": 1},
        )
        assert suggestion_response.status_code == 200
        suggestion = suggestion_response.json()
        assert suggestion["status"] == "offered"
        assert "Writing frame" in suggestion["content"]

        duplicate_suggestion = await client.post(
            f"/learning-canvas/sessions/{session_id}/suggestions",
            headers=headers,
            json={"section_id": "working_claim", "kind": "section_question", "base_revision": 1},
        )
        assert duplicate_suggestion.status_code == 409

        pre_accept_state = await client.get(f"/learning-canvas/sessions/{session_id}", headers=headers)
        claim_before_accept = next(
            draft for draft in pre_accept_state.json()["drafts"] if draft["section_id"] == "working_claim"
        )
        assert claim_before_accept["text"] == saved["text"]
        assert pre_accept_state.json()["suggestions"][0]["suggestion_id"] == suggestion["suggestion_id"]

        accepted_response = await client.post(
            f"/learning-canvas/sessions/{session_id}/suggestions/{suggestion['suggestion_id']}/accept",
            headers=headers,
            json={
                "text": "My provisional claim is that connected drains suggest coordinated urban planning, while the report leaves the governing institution uncertain.",
                "source_references": [{"chunk_id": source_chunk_id, "rationale": "Supports the claim."}],
            },
        )
        assert accepted_response.status_code == 200
        accepted = accepted_response.json()
        assert accepted["suggestion"]["status"] == "accepted"
        assert accepted["draft"]["revision"] == 2
        assert accepted["draft"]["author_type"] == "student_edited_assistance"
        assert "My provisional claim" in accepted["draft"]["text"]

        replay_response = await client.get(f"/events/session/{session_id}", headers=headers)
        event_types = [event["event_type"] for event in replay_response.json()["events"]]
        assert "canvas_section_saved" in event_types
        assert "canvas_suggestion_offered" in event_types
        assert "canvas_suggestion_accepted" in event_types

        submit_response = await client.post(f"/events/session/{session_id}/submit", headers=headers)
        assert submit_response.status_code == 200
        post_submission_save = await client.put(
            f"/learning-canvas/sessions/{session_id}/sections/working_claim",
            headers=headers,
            json={"text": "Cannot change this after submission.", "base_revision": 2},
        )
        assert post_submission_save.status_code == 409


@pytest.mark.asyncio
async def test_canvas_dismissal_is_explicit_and_session_scoped():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        assignment, _source_chunk_id = await create_published_grounded_assignment(client)
        session_response = await client.post(
            "/events/session",
            json={
                "student_id": f"canvas_student_{uuid.uuid4().hex[:8]}",
                "assignment_id": assignment["assignment_id"],
                "current_question_id": assignment["question_id"],
            },
        )
        session = session_response.json()
        session_id = session["session_id"]
        headers = {"X-Fiosra-Session-Token": session["access_token"]}
        suggestion_response = await client.post(
            f"/learning-canvas/sessions/{session_id}/suggestions",
            headers=headers,
            json={"section_id": "reasoning", "kind": "section_question", "base_revision": 0},
        )
        suggestion_id = suggestion_response.json()["suggestion_id"]

        dismissed_response = await client.post(
            f"/learning-canvas/sessions/{session_id}/suggestions/{suggestion_id}/dismiss",
            headers=headers,
            json={"reason": "I want to continue independently."},
        )
        assert dismissed_response.status_code == 200
        assert dismissed_response.json()["suggestion"]["status"] == "dismissed"

        state_response = await client.get(f"/learning-canvas/sessions/{session_id}", headers=headers)
        assert state_response.status_code == 200
        assert state_response.json()["suggestions"] == []
