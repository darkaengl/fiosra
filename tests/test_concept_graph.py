import pytest
from httpx import ASGITransport, AsyncClient

from fiosra.mvp.config import settings
from fiosra.mvp.main import app


@pytest.mark.asyncio
async def test_teacher_can_build_course_concept_hierarchy_and_module_roles():
    """A course gets an editable, acyclic high-to-low concept structure."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        course_response = await client.post(
            "/courses",
            json={
                "title": "HIST-330: Institutions, Evidence, and Revolution",
                "domain": "History",
                "created_by": "prof_graph",
            },
        )
        assert course_response.status_code == 201
        course_id = course_response.json()["course_id"]

        module_response = await client.post(
            f"/courses/{course_id}/modules",
            json={
                "title": "Unit 1: Fiscal institutions",
                "description": "Institutional constraints and state revenue.",
                "learning_objectives": ["Explain a causal institutional relationship"],
                "position": 1,
            },
        )
        assert module_response.status_code == 201
        module_id = module_response.json()["module_id"]

        root_response = await client.post(
            f"/courses/{course_id}/concept-graph/concepts",
            json={
                "label": "State formation and institutional power",
                "definition": "How institutions organize authority, resources, and political constraint.",
                "concept_type": "domain",
                "level": "course_theme",
            },
        )
        assert root_response.status_code == 201
        root = root_response.json()

        child_response = await client.post(
            f"/courses/{course_id}/concept-graph/concepts",
            json={
                "label": "Fiscal capacity and institutional constraint",
                "definition": "Revenue institutions shape the state capacity available for political action.",
                "concept_type": "relationship",
                "level": "topic",
                "parent_concept_id": root["concept_id"],
                "module_id": module_id,
                "module_role": "introduces",
            },
        )
        assert child_response.status_code == 201
        child = child_response.json()

        prerequisite_response = await client.post(
            f"/courses/{course_id}/concept-graph/concepts/{child['concept_id']}/prerequisites",
            json={"target_concept_id": root["concept_id"]},
        )
        assert prerequisite_response.status_code == 204

        source_response = await client.post(
            f"/courses/{course_id}/modules/{module_id}/resources",
            json={
                "title": "Fiscal institutions source excerpt",
                "content": (
                    "Fiscal capacity and institutional constraint shaped how the crown could collect "
                    "revenue from different estates during the eighteenth century."
                ),
                "resource_type": "primary_source",
            },
        )
        assert source_response.status_code == 201
        source_chunk_id = source_response.json()[0]["chunk_id"]

        cycle_response = await client.post(
            f"/courses/{course_id}/concept-graph/concepts/{child['concept_id']}/children",
            json={"target_concept_id": root["concept_id"]},
        )
        assert cycle_response.status_code == 409
        assert "cycle" in cycle_response.json()["detail"].lower()

        graph_response = await client.get(f"/courses/{course_id}/concept-graph")
        assert graph_response.status_code == 200
        graph = graph_response.json()
        assert graph["stats"]["concepts"] == 2
        assert {node["concept_id"] for node in graph["nodes"]} == {
            root["concept_id"],
            child["concept_id"],
        }
        assert {edge["relation"] for edge in graph["edges"]} == {"CONTAINS", "PREREQUISITE_OF"}
        assert graph["module_links"] == [
            {"module_id": module_id, "concept_id": child["concept_id"], "role": "introduces"}
        ]
        assert any(
            link["chunk_id"] == source_chunk_id and link["concept_id"] == child["concept_id"]
            for link in graph["source_links"]
        )


@pytest.mark.asyncio
async def test_course_concept_graph_is_generated_then_teacher_activates_it(monkeypatch):
    """The educator validates an automatic graph proposal instead of hand-building it."""
    monkeypatch.setattr(settings, "FIOSRA_LLM_PROVIDER", "deterministic")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        course_response = await client.post(
            "/courses",
            json={
                "title": "BIO-210: Cellular Energy and Evidence",
                "domain": "Biology",
                "created_by": "prof_auto_graph",
                "syllabus_context": "Students investigate cellular energy conversion using experimental evidence.",
            },
        )
        course_id = course_response.json()["course_id"]
        for position, title in [(1, "Energy transfer foundations"), (2, "ATP and respiratory systems")]:
            module_response = await client.post(
                f"/courses/{course_id}/modules",
                json={"title": title, "position": position, "learning_objectives": ["Explain evidence"]},
            )
            assert module_response.status_code == 201

        generated_response = await client.post(
            f"/courses/{course_id}/concept-graph/proposals/generate"
        )
        assert generated_response.status_code == 200
        generated = generated_response.json()
        assert generated["needs_teacher_validation"] is True
        assert generated["generated_by"] == "deterministic course structure"
        assert len(generated["proposal"]["concepts"]) >= 3

        inactive_graph = await client.get(f"/courses/{course_id}/concept-graph")
        assert inactive_graph.json()["stats"]["concepts"] == 0

        approval_response = await client.post(
            f"/courses/{course_id}/concept-graph/proposals/approve",
            json={"proposal": generated["proposal"]},
        )
        assert approval_response.status_code == 200
        active_graph = approval_response.json()
        assert active_graph["stats"]["concepts"] == len(generated["proposal"]["concepts"])
        assert active_graph["stats"]["module_links"] >= 2
