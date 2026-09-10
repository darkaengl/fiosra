import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from fiosra.mvp.main import app


@pytest.mark.asyncio
async def test_module_grounded_assignment_publishes_and_opens_student_projection():
    """A teacher can publish only a source-grounded module task and students can load the same record."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        course_response = await client.post(
            "/courses",
            json={
                "title": "HIST-275: Cities, Evidence, and Historical Argument",
                "domain": "History",
                "created_by": "prof_teacher",
            },
        )
        assert course_response.status_code == 201
        course_id = course_response.json()["course_id"]

        module_response = await client.post(
            f"/courses/{course_id}/modules",
            json={
                "title": "Mohenjo-daro urban infrastructure",
                "description": "Read drainage systems as archaeological evidence.",
                "learning_objectives": ["Distinguish observation from inference."],
                "position": 1,
            },
        )
        assert module_response.status_code == 201
        module_id = module_response.json()["module_id"]

        source_response = await client.post(
            f"/courses/{course_id}/modules/{module_id}/resources",
            json={
                "title": "Mohenjo-daro excavation report",
                "content": (
                    "The excavation report describes covered drains constructed from baked brick. "
                    "The drainage network connected houses to wider municipal channels, but the report "
                    "does not by itself identify the civic institutions responsible for its construction."
                ),
                "resource_type": "primary_source",
            },
        )
        assert source_response.status_code == 201
        source_chunk_id = source_response.json()[0]["chunk_id"]

        scaffold_response = await client.post(
            "/assignments/clarify-and-scaffold",
            json={
                "raw_prompt": "What can Mohenjo-daro's drainage infrastructure reveal about urban planning?",
                "domain": "history",
                "course_id": course_id,
                "module_id": module_id,
                "answers": {
                    "Q1_TEMPORAL": "Mohenjo-daro during the Mature Harappan period",
                    "Q2_MISCONCEPTIONS": "treating a single observation as proof of civic administration",
                    "Q3_EVIDENCE": "the Mohenjo-daro excavation report",
                },
            },
        )
        assert scaffold_response.status_code == 200
        scaffold = scaffold_response.json()
        assert scaffold["grounding_mode"] == "course_grounded"
        assert scaffold["grounding_sources"][0]["title"] == "Mohenjo-daro excavation report"
        assert "french" not in scaffold["clarified_prompt"].lower()
        assert "marie antoinette" not in str(scaffold).lower()

        draft_response = await client.post(
            "/assignments/draft",
            json={
                "topic": "Reading Mohenjo-daro drainage as evidence",
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
        private_spec = draft_response.json()

        publish_response = await client.post(f"/assignments/{private_spec['assignment_id']}/publish")
        assert publish_response.status_code == 200
        assert publish_response.json()["status"] == "published"

        student_projection = await client.get(f"/assignments/{private_spec['assignment_id']}")
        assert student_projection.status_code == 200
        public_spec = student_projection.json()
        assert public_spec["status"] == "published"
        assert public_spec["grounding_sources"][0]["title"] == "Mohenjo-daro excavation report"
        assert "vault_token" not in public_spec

        dependency_response = await client.get(
            f"/courses/{course_id}/resources/{source_chunk_id}/dependencies"
        )
        assert dependency_response.status_code == 200
        assert dependency_response.json()[0]["assignment_id"] == private_spec["assignment_id"]

        protected_delete_response = await client.delete(
            f"/courses/{course_id}/resources/{source_chunk_id}"
        )
        assert protected_delete_response.status_code == 409
        assert "published assignments" in protected_delete_response.json()["detail"]

        session_response = await client.post(
            "/events/session",
            json={
                "student_id": f"student_{uuid.uuid4().hex[:8]}",
                "assignment_id": private_spec["assignment_id"],
                "current_question_id": public_spec["question_id"],
            },
        )
        assert session_response.status_code == 200
        session_headers = {"X-Fiosra-Session-Token": session_response.json()["access_token"]}

        tutor_response = await client.post(
            "/dialogue/message",
            headers=session_headers,
            json={
                "session_id": session_response.json()["session_id"],
                "student_id": session_response.json()["student_id"],
                "question_id": public_spec["question_id"],
                "assignment_id": private_spec["assignment_id"],
                # This stale client text must not override the public assignment context.
                "question_prompt": "Explain the French crown's financial crisis.",
                "student_input": "The covered drains are evidence of coordinated infrastructure.",
            },
        )
        assert tutor_response.status_code == 200
        response_text = tutor_response.json()["response_text"].lower()
        assert "french" not in response_text
        assert "provisional claim" in response_text


@pytest.mark.asyncio
async def test_module_assignment_without_grounding_cannot_be_published():
    """The teacher receives a clear pre-publish guardrail rather than a broken student link."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        course_response = await client.post(
            "/courses",
            json={"title": "HIST-276: Evidence", "domain": "History", "created_by": "prof_teacher"},
        )
        course_id = course_response.json()["course_id"]
        module_response = await client.post(
            f"/courses/{course_id}/modules",
            json={"title": "Evidence module", "position": 1},
        )
        module_id = module_response.json()["module_id"]
        draft_response = await client.post(
            "/assignments/draft",
            json={
                "topic": "Ungrounded module task",
                "domain": "history",
                "course_id": course_id,
                "module_id": module_id,
                "raw_prompt": "Make a claim using evidence.",
            },
        )
        assert draft_response.status_code == 200

        publish_response = await client.post(f"/assignments/{draft_response.json()['assignment_id']}/publish")
        assert publish_response.status_code == 422
        assert "ground" in publish_response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_filtered_review_queue_returns_a_truthful_successful_response():
    """A filtered course queue returns 200, including when no submitted work is present."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        course_response = await client.post(
            "/courses",
            json={"title": "HIST-277: Review workflow", "domain": "History", "created_by": "prof_teacher"},
        )
        course_id = course_response.json()["course_id"]
        queue_response = await client.get(f"/evidence/review-queue?course_id={course_id}")
        assert queue_response.status_code == 200
        assert queue_response.json() == []
