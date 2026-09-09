import uuid
from uuid import UUID

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from fiosra.mvp.courses.schemas import CourseCreate, ModuleCreate
from fiosra.mvp.courses.service import course_service
from fiosra.mvp.database import AsyncSessionLocal
from fiosra.mvp.main import app


@pytest.mark.asyncio
async def test_course_crud_flow():
    """Verify creating, listing, and fetching a course workspace."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Create Course
        res = await ac.post(
            "/courses",
            json={
                "title": "HIST-301: The French Revolution & Global Crisis",
                "domain": "History",
                "created_by": "prof_somerville",
                "syllabus_context": "Introductory survey into 18th-century French fiscal crisis.",
            },
        )
        assert res.status_code == 201
        course_data = res.json()
        assert "course_id" in course_data
        course_id = course_data["course_id"]
        assert UUID(course_id)
        assert course_data["title"] == "HIST-301: The French Revolution & Global Crisis"
        assert course_data["domain"] == "History"
        assert course_data["created_by"] == "prof_somerville"

        # 2. List Courses
        list_res = await ac.get("/courses")
        assert list_res.status_code == 200
        courses = list_res.json()
        assert any(c["course_id"] == course_id for c in courses)

        # 3. Get Specific Course
        get_res = await ac.get(f"/courses/{course_id}")
        assert get_res.status_code == 200
        assert get_res.json()["course_id"] == course_id

        # 4. Non-existent Course
        fake_id = str(uuid.uuid4())
        bad_res = await ac.get(f"/courses/{fake_id}")
        assert bad_res.status_code == 404


@pytest.mark.asyncio
async def test_module_sequencer():
    """Verify adding sequential modules to a course and checking lock status."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Create parent course
        c_res = await ac.post(
            "/courses",
            json={
                "title": "PHYS-101: Classical Mechanics",
                "domain": "Physics",
                "created_by": "prof_galileo",
            },
        )
        course_id = c_res.json()["course_id"]

        # Add Module 1 (unlocked by default)
        m1_res = await ac.post(
            f"/courses/{course_id}/modules",
            json={
                "title": "Module 1: Kinematics & 1D Motion",
                "description": "Foundational vectors, displacement, and velocity.",
                "learning_objectives": ["Understand displacement vectors", "Calculate instantaneous velocity"],
                "position": 1,
            },
        )
        assert m1_res.status_code == 201
        m1 = m1_res.json()
        assert m1["position"] == 1
        assert m1["is_locked"] is False
        m1_id = m1["module_id"]

        # Add Module 2 (locked sequencer)
        m2_res = await ac.post(
            f"/courses/{course_id}/modules",
            json={
                "title": "Module 2: Newton's Laws of Motion",
                "description": "Dynamics, free body diagrams, and friction.",
                "learning_objectives": ["Construct free body diagrams", "Apply F = ma"],
                "position": 2,
            },
        )
        assert m2_res.status_code == 201
        m2 = m2_res.json()
        assert m2["position"] == 2
        assert m2["is_locked"] is True
        m2_id = m2["module_id"]

        # Verify Course now nests both modules in order
        course_res = await ac.get(f"/courses/{course_id}")
        assert course_res.status_code == 200
        modules = course_res.json()["modules"]
        assert len(modules) == 2
        assert modules[0]["module_id"] == m1_id
        assert modules[1]["module_id"] == m2_id

        # Verify fetching individual module
        fetch_m1 = await ac.get(f"/courses/{course_id}/modules/{m1_id}")
        assert fetch_m1.status_code == 200
        assert fetch_m1.json()["title"] == "Module 1: Kinematics & 1D Motion"


@pytest.mark.asyncio
async def test_syllabus_corpus_ingestion_and_vector_search():
    """Verify parsing markdown syllabus, generating 1536-dim embeddings, and pgvector cosine search."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        c_res = await ac.post(
            "/courses",
            json={
                "title": "HIST-401: French Revolutionary Origins",
                "domain": "History",
                "created_by": "prof_somerville",
            },
        )
        course_id = c_res.json()["course_id"]

        syllabus_markdown = """# Syllabus: Origins of the French Revolution

## Section 1: Structural Royal Sovereign Debt
By 1788, the French crown faced an acute fiscal emergency driven by sovereign war debts from the Seven Years' War and the American Revolutionary War. Over fifty percent of state revenue was consumed by interest service on royal debt.

## Section 2: Ancien Regime Social Privileges
The institutional structure of the Ancien Regime divided French society into Three Estates. The First Estate (Clergy) and Second Estate (Nobility) enjoyed extensive tax exemptions, while the tax burden fell disproportionately upon the Third Estate.

## Section 3: Convocation of the Estates-General
When the Assembly of Notables refused Calonne's proposed universal land tax, Louis XVI was forced to convene the Estates-General in May 1789, sparking the political crisis that led to the Tennis Court Oath.
"""

        # Ingest syllabus
        ingest_res = await ac.post(
            f"/courses/{course_id}/syllabus",
            json={
                "title": "HIST-401 Full Syllabus",
                "content": syllabus_markdown,
            },
        )
        assert ingest_res.status_code == 200
        chunks = ingest_res.json()
        assert len(chunks) >= 3

        # Verify KC Grounding associations
        kc_ids = [c["kc_id"] for c in chunks if c.get("kc_id")]
        assert "KC_HIST_FRENCH_DEBT" in kc_ids or "KC_HIST_ANCIEN_REGIME" in kc_ids

        # Perform pgvector cosine similarity search using exact text from chunk 0
        search_res = await ac.get(
            f"/courses/{course_id}/syllabus/search",
            params={
                "query": chunks[0]["content"],
                "top_k": 3,
            },
        )
        assert search_res.status_code == 200
        results = search_res.json()
        assert len(results) > 0
        top_hit = results[0]
        assert "Debt" in top_hit["title"] or "debt" in top_hit["content"].lower()
        assert top_hit["similarity"] is not None
        assert top_hit["similarity"] >= 0.99




@pytest.mark.asyncio
async def test_cohort_roster_diagnostics_and_telemetry():
    """Verify roster aggregation with telemetry-driven Autonomy Scores and struggle flags."""
    # 1. Create Course and Module
    course = await course_service.create_course(
        CourseCreate(
            title="HIST-205: Revolutionary France",
            domain="History",
            created_by="prof_somerville",
        )
    )
    course_id = course.course_id

    module = await course_service.add_module(
        course_id,
        ModuleCreate(
            title="Module 1: The Fiscal Breakdown",
            description="Deep dive into sovereign bankruptcy.",
            position=1,
        ),
    )
    module_id = module.module_id

    # 2. Insert Assignment linked to this module
    assignment_id = uuid.uuid4()
    session_id = uuid.uuid4()
    student_id = "student_struggling_telemetry_test"

    async with AsyncSessionLocal() as session:
        # Insert Assignment
        await session.execute(
            text("""
                INSERT INTO assignments (assignment_id, module_id, title, created_by, spec)
                VALUES (:aid, :mid, :title, :created_by, '{"status": "published"}'::jsonb);
            """),
            {"aid": assignment_id, "mid": module_id, "title": "Fiscal Crisis Essay", "created_by": "prof_somerville"},
        )

        # Insert Student Session
        await session.execute(
            text("""
                INSERT INTO student_sessions (session_id, student_id, assignment_id, current_question_id, status)
                VALUES (:sid, :student_id, :aid, 'Q1', 'active');
            """),
            {"sid": session_id, "student_id": student_id, "aid": assignment_id},
        )

        # Insert Events: hint served at Rung 3 (heavy scaffolding -> lower autonomy) and misconception flagged
        await session.execute(
            text("""
                INSERT INTO session_events (session_id, student_id, assignment_id, question_id, event_type, payload)
                VALUES 
                (:sid, :student_id, :aid, 'Q1', 'hint_served', '{"rung": 3, "target_kc": "KC_HIST_FRENCH_DEBT"}'::jsonb),
                (:sid, :student_id, :aid, 'Q1', 'misconception_flagged', '{"kc_id": "KC_HIST_FRENCH_DEBT", "code": "MISC_HIST_006"}'::jsonb),
                (:sid, :student_id, :aid, 'Q1', 'misconception_flagged', '{"kc_id": "KC_HIST_ESTATES_GENERAL", "code": "MISC_HIST_007"}'::jsonb);
            """),
            {"sid": session_id, "student_id": student_id, "aid": assignment_id},
        )
        await session.commit()

    # 3. Query Cohort Roster Endpoint
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        roster_res = await ac.get(f"/courses/{course_id}/roster")
        assert roster_res.status_code == 200
        data = roster_res.json()
        assert data["course_id"] == str(course_id)
        assert data["total_enrolled"] >= 1

        student_metric = next((s for s in data["students"] if s["student_id"] == student_id), None)
        assert student_metric is not None
        # Rung 3 hint: autonomy = 1.0 - 0.25 * 3 = 0.25
        assert student_metric["average_autonomy_score"] <= 0.50
        assert student_metric["active_struggle"] is True
        assert "KC_HIST_FRENCH_DEBT" in student_metric["struggling_kcs"]
