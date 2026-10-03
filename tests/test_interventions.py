import uuid
import pytest
from httpx import ASGITransport, AsyncClient

from fiosra.mvp.main import app, lifespan
from tests.test_socratic_probes import create_document_session, save_meaningful_paragraph


@pytest.mark.asyncio
async def test_intervention_lifecycle():
    async with lifespan(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            assignment, session, document = await create_document_session(client)
            headers = {"X-Fiosra-Session-Token": session["access_token"]}
            saved_doc, paragraph = await save_meaningful_paragraph(
                client, session, document, headers
            )

            session_id = session["session_id"]
            student_id = session["student_id"]
            block_id = paragraph["block_id"]

            # 1. Dispatch an intervention
            dispatch_payload = {
                "session_id": session_id,
                "student_id": student_id,
                "teacher_id": "test_educator",
                "document_id": saved_doc["document_id"],
                "block_id": block_id,
                "concept_id": "concept_urban_coordination",
                "concept_label": "Urban Infrastructure Coordination",
                "misconception_id": "misc_labor_attribution",
                "evidence_quote": "their repeated alignment requires shared construction decisions",
                "activity_type": "socratic_nudge",
                "activity_prompt": "What physical evidence distinguishes municipal planning from organic household coordination?",
                "activity_guidance": "Examine the shared brick bonding patterns in exhibit 3.",
            }

            dispatch_res = await client.post("/interventions/dispatch", json=dispatch_payload)
            assert dispatch_res.status_code == 200, dispatch_res.text
            intervention = dispatch_res.json()
            intervention_id = intervention["intervention_id"]

            assert intervention["status"] == "dispatched"
            assert intervention["session_id"] == session_id
            assert intervention["student_id"] == student_id
            assert intervention["activity_prompt"] == dispatch_payload["activity_prompt"]
            assert intervention["block_id"] == block_id

            # 2. List interventions for session
            list_res = await client.get(f"/interventions/session/{session_id}")
            assert list_res.status_code == 200
            session_interventions = list_res.json()
            assert len(session_interventions) >= 1
            assert any(i["intervention_id"] == intervention_id for i in session_interventions)

            # 3. List interventions for student across courses
            student_list_res = await client.get(f"/interventions/student/{student_id}")
            assert student_list_res.status_code == 200
            student_interventions = student_list_res.json()
            assert any(i["intervention_id"] == intervention_id for i in student_interventions)

            # 4. Student responds to intervention
            respond_res = await client.post(
                f"/interventions/{intervention_id}/respond",
                json={"student_response": "The uniformity in brick dimensions and shared boundary drainage suggests standardization beyond individual homeowners."},
            )
            assert respond_res.status_code == 200
            responded_data = respond_res.json()
            assert responded_data["status"] == "responded"
            assert responded_data["student_response"] is not None
            assert responded_data["responded_at"] is not None

            # 5. Teacher acknowledges intervention
            ack_res = await client.post(f"/interventions/{intervention_id}/acknowledge")
            assert ack_res.status_code == 200
            ack_data = ack_res.json()
            assert ack_data["status"] == "acknowledged"
            assert ack_data["acknowledged_at"] is not None
