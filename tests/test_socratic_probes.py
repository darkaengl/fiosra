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


@pytest.mark.asyncio
async def test_epistemic_classify_sentences():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        _assignment, session, _document = await create_document_session(client)
        headers = {"X-Fiosra-Session-Token": session["access_token"]}
        classify_url = f"/learning-documents/sessions/{session['session_id']}/probes/epistemic-classify"

        sentences = [
            "Remote work inherently maximizes organizational efficiency.",
            "This assumes all team members possess high autonomy.",
            "According to the 2023 remote productivity dataset, output rose by 12%.",
            "Because asynchronous communication reduces meeting fragmentation, deep work intervals increase.",
            "Therefore, physical offices will become completely obsolete.",
        ]

        text_corpus = " ".join(sentences)
        response = await client.post(
            classify_url,
            headers=headers,
            json={"text": text_corpus, "oracle_pressure": "socratic"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["sentences"]) >= 4
        types = [item["epistemic_type"] for item in data["sentences"]]
        assert "claim" in types or "assumption" in types
        assert "evidence" in types
        # Verify sentences returned are typed
        for item in data["sentences"]:
            assert item["sentence"]
            assert item["epistemic_type"] in ["claim", "evidence", "reasoning", "assumption", "premature_closure"]


@pytest.mark.asyncio
async def test_sentence_inquire_socratic_agent():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        _assignment, session, _document = await create_document_session(client)
        headers = {"X-Fiosra-Session-Token": session["access_token"]}
        inquire_url = f"/learning-documents/sessions/{session['session_id']}/probes/sentence-inquire"

        # Challenge inquiry
        response = await client.post(
            inquire_url,
            headers=headers,
            json={
                "sentence": "Therefore, physical offices will become completely obsolete.",
                "epistemic_type": "premature_closure",
                "surrounding_context": "Remote work increases deep focus. Therefore, physical offices will become completely obsolete.",
                "move_type": "challenge",
                "oracle_pressure": "socratic",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["oracle_probe"].endswith("?")
        assert len(data["socratic_moves"]) >= 2
        assert data["move_type"] == "challenge"
        assert data["targeted_vulnerability"]

        # Why ladder inquiry
        why_response = await client.post(
            inquire_url,
            headers=headers,
            json={
                "sentence": "Because asynchronous communication reduces meeting fragmentation, deep work intervals increase.",
                "epistemic_type": "reasoning",
                "move_type": "why_ladder",
            },
        )
        assert why_response.status_code == 200
        why_data = why_response.json()
        assert why_data["oracle_probe"].endswith("?")
        assert why_data["move_type"] == "why_ladder"


@pytest.mark.asyncio
async def test_dialectical_turn_socratic_oracle(monkeypatch):
    monkeypatch.setattr(settings, "FIOSRA_LLM_PROVIDER", "deterministic")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        _assignment, session, _document = await create_document_session(client)
        headers = {"X-Fiosra-Session-Token": session["access_token"]}
        turn_url = f"/learning-documents/sessions/{session['session_id']}/probes/dialectical-turn"

        # Turn 1: Incomplete / ungrounded defense -> Oracle remains unsatisfied and asks follow-up
        response_incomplete = await client.post(
            turn_url,
            headers=headers,
            json={
                "sentence": "Therefore, physical offices will become completely obsolete.",
                "epistemic_type": "premature_closure",
                "history": [
                    {
                        "role": "oracle",
                        "content": "What empirical evidence supports your claim that physical offices will become completely obsolete?",
                    }
                ],
                "student_reply": "I just think everyone likes working from home more.",
                "move_type": "challenge",
            },
        )
        assert response_incomplete.status_code == 200
        data1 = response_incomplete.json()
        assert "oracle_reply" in data1
        assert not data1["is_satisfied"]
        assert data1["suggested_revision"] is None
        assert data1["epistemic_progress"] < 1.0

        # Turn 2: Rigorous empirical defense -> Oracle is satisfied and provides suggested revision
        response_rigorous = await client.post(
            turn_url,
            headers=headers,
            json={
                "sentence": "Therefore, physical offices will become completely obsolete.",
                "epistemic_type": "premature_closure",
                "history": [
                    {
                        "role": "oracle",
                        "content": "What empirical evidence supports your claim that physical offices will become completely obsolete?",
                    },
                    {
                        "role": "student",
                        "content": "I just think everyone likes working from home more.",
                    },
                    {
                        "role": "oracle",
                        "content": "What verifiable source excerpt demonstrates that preference eliminates commercial office need?",
                    },
                ],
                "student_reply": (
                    "According to Source 1 on the 1881 Land Act agrarian reforms, structural economic displacement "
                    "does not happen purely by preference; rather, as demonstrated by the economic dataset, "
                    "hybrid occupancy models persist specifically because collaborative legal synthesis requires co-location."
                ),
                "move_type": "source",
            },
        )
        assert response_rigorous.status_code == 200
        data2 = response_rigorous.json()
        assert data2["is_satisfied"] is True
        assert data2["satisfaction_reason"]
        assert data2["suggested_revision"] is not None
        assert data2["epistemic_progress"] >= 0.9

