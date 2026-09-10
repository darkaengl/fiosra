import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from fiosra.mvp.config import settings
from fiosra.mvp.main import app
from tests.test_learning_canvas import create_published_grounded_assignment
from tests.test_learning_documents import paragraph_block


async def create_document_session(client: AsyncClient) -> tuple[dict, dict, dict]:
    assignment, _source_chunk_id = await create_published_grounded_assignment(client)
    session_response = await client.post(
        "/events/session",
        json={
            "student_id": f"probe_student_{uuid.uuid4().hex[:8]}",
            "assignment_id": assignment["assignment_id"],
            "current_question_id": assignment["question_id"],
        },
    )
    session = session_response.json()
    headers = {"X-Fiosra-Session-Token": session["access_token"]}
    document_response = await client.get(
        f"/learning-documents/sessions/{session['session_id']}", headers=headers
    )
    assert document_response.status_code == 200
    return assignment, session, document_response.json()


async def save_meaningful_paragraph(
    client: AsyncClient,
    session: dict,
    document: dict,
    headers: dict[str, str],
    suffix: str = "",
) -> tuple[dict, dict]:
    paragraph = next(block for block in document["blocks"] if block["block_type"] == "paragraph")
    prose = (
        "The drainage channels indicate deliberate coordination across connected homes because "
        "their repeated alignment requires shared construction decisions, although the surviving "
        "evidence does not identify which institution organized the labour. "
        f"{suffix}"
    )
    changed = paragraph_block(
        paragraph["block_id"], paragraph["position"], prose, paragraph["section_id"]
    )
    saved_response = await client.put(
        f"/learning-documents/sessions/{session['session_id']}",
        headers=headers,
        json={
            "base_revision": document["document_revision"],
            "upserts": [changed],
            "deleted_block_ids": [],
        },
    )
    assert saved_response.status_code == 200
    return saved_response.json(), changed


@pytest.mark.asyncio
async def test_proactive_probe_is_authorized_idempotent_and_records_response(monkeypatch):
    monkeypatch.setattr(settings, "FIOSRA_PROBE_QUIET_SECONDS", 0)
    monkeypatch.setattr(settings, "FIOSRA_PROBE_COOLDOWN_SECONDS", 0)
    monkeypatch.setattr(settings, "FIOSRA_LLM_PROVIDER", "deterministic")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        _assignment, session, document = await create_document_session(client)
        headers = {"X-Fiosra-Session-Token": session["access_token"]}
        saved, changed = await save_meaningful_paragraph(client, session, document, headers)
        evaluate_url = f"/learning-documents/sessions/{session['session_id']}/probes/evaluate"

        forbidden = await client.post(
            evaluate_url,
            json={"document_revision": saved["document_revision"], "changed_block_ids": [changed["block_id"]]},
        )
        assert forbidden.status_code == 403

        stale = await client.post(
            evaluate_url,
            headers=headers,
            json={"document_revision": 0, "changed_block_ids": [changed["block_id"]]},
        )
        assert stale.status_code == 409

        evaluated = await client.post(
            evaluate_url,
            headers=headers,
            json={
                "document_revision": saved["document_revision"],
                "changed_block_ids": [changed["block_id"]],
            },
        )
        assert evaluated.status_code == 200
        result = evaluated.json()
        assert len(result["created"]) == 1
        probe = result["created"][0]
        assert probe["block_id"] == changed["block_id"]
        assert probe["status"] == "offered"
        assert probe["evidence_state"] == "unverified"
        assert probe["question"].endswith("?")
        assert "answer" not in probe["question"].lower()
        assert probe["generation_metadata"]["used_live_provider"] is False

        duplicate = await client.post(
            evaluate_url,
            headers=headers,
            json={
                "document_revision": saved["document_revision"],
                "changed_block_ids": [changed["block_id"]],
            },
        )
        assert duplicate.status_code == 200
        assert duplicate.json()["created"] == []
        assert len(duplicate.json()["pending"]) == 1

        invalid_response = await client.post(
            f"/learning-documents/sessions/{session['session_id']}/probes/{probe['probe_id']}/responses",
            headers=headers,
            json={"response_text": "Too short"},
        )
        assert invalid_response.status_code == 422

        response_text = (
            "The repeated alignment matters because a single household could not independently "
            "maintain the connected channels across the neighbourhood."
        )
        response = await client.post(
            f"/learning-documents/sessions/{session['session_id']}/probes/{probe['probe_id']}/responses",
            headers=headers,
            json={"response_text": response_text},
        )
        assert response.status_code == 200
        submitted_probe = response.json()["probe"]
        assert submitted_probe["status"] == "responded"
        assert submitted_probe["evidence_state"] == "evidence_submitted"
        assert submitted_probe["response_text"] == response_text
        assert "not an automatic grade" in response.json()["message"].lower()

        dossier = await client.get(f"/evidence/dossier/{session['session_id']}")
        assert dossier.status_code == 200
        proactive_evidence = dossier.json()["proactive_socratic_evidence"]
        assert len(proactive_evidence) == 1
        assert proactive_evidence[0]["question"] == probe["question"]
        assert proactive_evidence[0]["response_text"] == response_text
        assert proactive_evidence[0]["evidence_state"] == "evidence_submitted"

        listed = await client.get(
            f"/learning-documents/sessions/{session['session_id']}/probes", headers=headers
        )
        assert listed.status_code == 200
        assert listed.json()["probes"] == []
        assert listed.json()["evidence_summary"]["evidence_submitted"] == 1

        replay = await client.get(f"/events/session/{session['session_id']}", headers=headers)
        event_payloads = [event["payload"] for event in replay.json()["events"]]
        assert any(event["event_type"] == "socratic_probe_offered" for event in replay.json()["events"])
        assert any(event["event_type"] == "socratic_probe_response_submitted" for event in replay.json()["events"])
        assert all(response_text not in str(payload) for payload in event_payloads)


@pytest.mark.asyncio
async def test_probe_defer_and_material_document_revision_supersede_prior_question(monkeypatch):
    monkeypatch.setattr(settings, "FIOSRA_PROBE_QUIET_SECONDS", 0)
    monkeypatch.setattr(settings, "FIOSRA_PROBE_COOLDOWN_SECONDS", 0)
    monkeypatch.setattr(settings, "FIOSRA_LLM_PROVIDER", "deterministic")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        _assignment, session, document = await create_document_session(client)
        headers = {"X-Fiosra-Session-Token": session["access_token"]}
        first_saved, first_changed = await save_meaningful_paragraph(client, session, document, headers)
        evaluate_url = f"/learning-documents/sessions/{session['session_id']}/probes/evaluate"
        first_evaluation = await client.post(
            evaluate_url,
            headers=headers,
            json={
                "document_revision": first_saved["document_revision"],
                "changed_block_ids": [first_changed["block_id"]],
            },
        )
        first_probe = first_evaluation.json()["created"][0]

        deferred = await client.post(
            f"/learning-documents/sessions/{session['session_id']}/probes/{first_probe['probe_id']}/defer",
            headers=headers,
        )
        assert deferred.status_code == 200
        assert deferred.json()["probe"]["status"] == "deferred"
        assert "fully editable" in deferred.json()["message"].lower()

        current_document = await client.get(
            f"/learning-documents/sessions/{session['session_id']}", headers=headers
        )
        assert current_document.status_code == 200
        revised, revised_changed = await save_meaningful_paragraph(
            client,
            session,
            current_document.json(),
            headers,
            suffix="This revised qualification makes the causal inference appropriately cautious.",
        )
        reevaluated = await client.post(
            evaluate_url,
            headers=headers,
            json={
                "document_revision": revised["document_revision"],
                "changed_block_ids": [revised_changed["block_id"]],
            },
        )
        assert reevaluated.status_code == 200
        next_probe = reevaluated.json()["created"]
        assert len(next_probe) == 1
        assert next_probe[0]["probe_id"] != first_probe["probe_id"]
        assert next_probe[0]["source_block_revision"] == 3

        dismissed = await client.post(
            f"/learning-documents/sessions/{session['session_id']}/probes/{next_probe[0]['probe_id']}/dismiss",
            headers=headers,
        )
        assert dismissed.status_code == 200
        assert dismissed.json()["probe"]["status"] == "dismissed"
        assert "automatic penalty" in dismissed.json()["message"].lower()


@pytest.mark.asyncio
async def test_probes_reject_nonmember_blocks_and_submitted_sessions(monkeypatch):
    monkeypatch.setattr(settings, "FIOSRA_PROBE_QUIET_SECONDS", 0)
    monkeypatch.setattr(settings, "FIOSRA_LLM_PROVIDER", "deterministic")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        _assignment, session, document = await create_document_session(client)
        headers = {"X-Fiosra-Session-Token": session["access_token"]}
        evaluate_url = f"/learning-documents/sessions/{session['session_id']}/probes/evaluate"
        unknown_block = await client.post(
            evaluate_url,
            headers=headers,
            json={"document_revision": document["document_revision"], "changed_block_ids": [str(uuid.uuid4())]},
        )
        assert unknown_block.status_code == 422

        submitted = await client.post(f"/events/session/{session['session_id']}/submit", headers=headers)
        assert submitted.status_code == 200
        blocked = await client.get(
            f"/learning-documents/sessions/{session['session_id']}/probes", headers=headers
        )
        assert blocked.status_code == 409
