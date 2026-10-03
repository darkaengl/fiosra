import uuid
import pytest
from httpx import ASGITransport, AsyncClient

from fiosra.mvp.main import app, lifespan


@pytest.mark.asyncio
async def test_course_concept_mastery_endpoint():
    async with lifespan(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 1. Create Course
            res = await client.post(
                "/courses",
                json={
                    "title": "MKT-101: Principles of Marketing Diagnostics",
                    "domain": "Business",
                    "created_by": "prof_ross",
                    "syllabus_context": "Core marketing strategy, segmentation, targeting, positioning.",
                },
            )
            assert res.status_code == 201
            course_data = res.json()
            course_id = course_data["course_id"]

            # 2. Add Module
            mod_res = await client.post(
                f"/courses/{course_id}/modules",
                json={
                    "title": "Module 1: Market Segmentation & Research",
                    "description": "Understanding customer segments and behavioral attributes.",
                    "learning_objectives": ["Identify customer segments", "Distinguish demographic from behavioral"],
                    "position": 1,
                },
            )
            assert mod_res.status_code == 201

            # 3. Query Concept Mastery Endpoint
            mastery_res = await client.get(f"/courses/{course_id}/concept-mastery")
            assert mastery_res.status_code == 200
            data = mastery_res.json()

            assert data["course_id"] == course_id
            assert "graph" in data
            assert "nodes" in data["graph"]
            assert "edges" in data["graph"]
            assert "students" in data
            assert "bottlenecks" in data
            assert isinstance(data["students"], list)
            assert isinstance(data["bottlenecks"], list)
