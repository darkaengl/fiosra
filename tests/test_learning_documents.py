import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from fiosra.mvp.main import app
from tests.test_learning_canvas import create_published_grounded_assignment


def paragraph_block(block_id: str, position: int, text: str, section_id: str = "reasoning") -> dict:
    return {
        "block_id": block_id,
        "block_type": "paragraph",
        "position": position,
        "section_id": section_id,
        "author_type": "student",
        "content": {
            "type": "paragraph",
            "attrs": {"blockId": block_id, "sectionId": section_id, "authorType": "student"},
            "content": [{"type": "text", "text": text}],
        },
    }


@pytest.mark.asyncio
async def test_long_form_document_imports_canvas_and_requires_session_capability():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        assignment, _source_chunk_id = await create_published_grounded_assignment(client)
        session_response = await client.post(
            "/events/session",
            json={
                "student_id": f"document_student_{uuid.uuid4().hex[:8]}",
                "assignment_id": assignment["assignment_id"],
                "current_question_id": assignment["question_id"],
            },
        )
        session = session_response.json()
        session_id = session["session_id"]
        headers = {"X-Fiosra-Session-Token": session["access_token"]}

        forbidden = await client.get(f"/learning-documents/sessions/{session_id}")
        assert forbidden.status_code == 403

        state_response = await client.get(f"/learning-documents/sessions/{session_id}", headers=headers)
        assert state_response.status_code == 200
        state = state_response.json()
        assert state["session_id"] == session_id
        assert state["document_revision"] == 0
        assert len(state["blocks"]) == 10
        assert [block["block_type"] for block in state["blocks"]] == ["heading", "paragraph"] * 5
        assert all(block["content"]["attrs"]["blockId"] == block["block_id"] for block in state["blocks"])

        paragraph = next(block for block in state["blocks"] if block["block_type"] == "paragraph")
        changed = paragraph_block(
            paragraph["block_id"],
            paragraph["position"],
            "The drainage pattern supports an inference about coordination but not its institution.",
            paragraph["section_id"],
        )
        sync_response = await client.put(
            f"/learning-documents/sessions/{session_id}",
            headers=headers,
            json={"base_revision": 0, "upserts": [changed], "deleted_block_ids": []},
        )
        assert sync_response.status_code == 200
        synced = sync_response.json()
        assert synced["document_revision"] == 1
        restored = next(block for block in synced["blocks"] if block["block_id"] == paragraph["block_id"])
        assert restored["plaintext"] == changed["content"]["content"][0]["text"]
        assert restored["revision"] == 2

        stale_response = await client.put(
            f"/learning-documents/sessions/{session_id}",
            headers=headers,
            json={"base_revision": 0, "upserts": [changed], "deleted_block_ids": []},
        )
        assert stale_response.status_code == 409

        invalid_block = paragraph_block(str(uuid.uuid4()), 99, "Untrusted identity.")
        invalid_block["content"]["attrs"]["blockId"] = str(uuid.uuid4())
        invalid_response = await client.put(
            f"/learning-documents/sessions/{session_id}",
            headers=headers,
            json={"base_revision": 1, "upserts": [invalid_block], "deleted_block_ids": []},
        )
        assert invalid_response.status_code == 422


@pytest.mark.asyncio
async def test_long_document_accepts_many_incremental_blocks_without_document_wide_cap():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        assignment, _source_chunk_id = await create_published_grounded_assignment(client)
        session_response = await client.post(
            "/events/session",
            json={
                "student_id": f"long_document_student_{uuid.uuid4().hex[:8]}",
                "assignment_id": assignment["assignment_id"],
                "current_question_id": assignment["question_id"],
            },
        )
        session = session_response.json()
        session_id = session["session_id"]
        headers = {"X-Fiosra-Session-Token": session["access_token"]}
        initial = (await client.get(f"/learning-documents/sessions/{session_id}", headers=headers)).json()

        # 125 independently addressable paragraphs at 240 words each approximate a
        # 100-page double-spaced essay without one giant request field or an 8K cap.
        paragraph_text = "evidence " * 240
        blocks = [
            paragraph_block(str(uuid.uuid4()), position, paragraph_text)
            for position in range(11, 136)
        ]
        sync_response = await client.put(
            f"/learning-documents/sessions/{session_id}",
            headers=headers,
            json={"base_revision": initial["document_revision"], "upserts": blocks, "deleted_block_ids": []},
        )
        assert sync_response.status_code == 200
        synced = sync_response.json()
        assert synced["document_revision"] == 1
        assert len(synced["blocks"]) == 135
        assert sum(len(block["plaintext"]) for block in synced["blocks"]) > 200_000

        replay = await client.get(f"/events/session/{session_id}", headers=headers)
        event_types = [event["event_type"] for event in replay.json()["events"]]
        assert "learning_document_initialized" in event_types
        assert "learning_document_synced" in event_types

        submitted = await client.post(f"/events/session/{session_id}/submit", headers=headers)
        assert submitted.status_code == 200
        blocked_update = await client.put(
            f"/learning-documents/sessions/{session_id}",
            headers=headers,
            json={"base_revision": 1, "upserts": [blocks[0]], "deleted_block_ids": []},
        )
        assert blocked_update.status_code == 409
