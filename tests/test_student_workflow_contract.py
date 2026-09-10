import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from fiosra.mvp.main import app


@pytest.mark.asyncio
async def test_public_assignment_projection_excludes_answer_vault_token():
    """Students can retrieve a published task but never receive its vault token."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        draft_response = await client.post(
            "/assignments/draft",
            json={
                "topic": "French fiscal crisis",
                "domain": "history",
                "raw_prompt": "Analyze structural causes of the French fiscal crisis in 1789.",
                "answers": {
                    "Q1_TEMPORAL": "1787–1789",
                    "Q2_MISCONCEPTIONS": "A single personal spending explanation",
                    "Q3_EVIDENCE": "A course primary source",
                },
            },
        )
        assert draft_response.status_code == 200
        private_spec = draft_response.json()
        assert private_spec["vault_token"].startswith("vlt_")

        publish_response = await client.post(f"/assignments/{private_spec['assignment_id']}/publish")
        assert publish_response.status_code == 200

        public_response = await client.get(f"/assignments/{private_spec['assignment_id']}")
        assert public_response.status_code == 200
        public_spec = public_response.json()
        assert public_spec["assignment_id"] == private_spec["assignment_id"]
        assert "vault_token" not in public_spec
        assert "reference_solution" not in public_spec


@pytest.mark.asyncio
async def test_submitted_session_blocks_further_student_dialogue():
    """A submitted reasoning trace cannot be silently altered before educator review."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        session_response = await client.post(
            "/events/session",
            json={
                "student_id": f"student_contract_{uuid.uuid4().hex[:8]}",
                "current_question_id": "Q1",
            },
        )
        assert session_response.status_code == 200
        session_id = session_response.json()["session_id"]
        student_id = session_response.json()["student_id"]

        message_response = await client.post(
            "/dialogue/message",
            json={
                "session_id": session_id,
                "student_id": student_id,
                "question_id": "Q1",
                "question_prompt": "Explain the structural causes of French fiscal crisis.",
                "student_input": "War debt and inequitable tax exemptions created a structural crisis.",
            },
        )
        assert message_response.status_code == 200

        submit_response = await client.post(f"/events/session/{session_id}/submit")
        assert submit_response.status_code == 200
        assert submit_response.json()["status"] == "submitted"

        blocked_response = await client.post(
            "/dialogue/message",
            json={
                "session_id": session_id,
                "student_id": student_id,
                "question_id": "Q1",
                "question_prompt": "Explain the structural causes of French fiscal crisis.",
                "student_input": "Attempt to change the submitted trace.",
            },
        )
        assert blocked_response.status_code == 409
