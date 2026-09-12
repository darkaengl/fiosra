"""Manual end-to-end demo of the course concept graph + student mastery overlay.

Seeds a small Neural Network Learning course (derivative -> chain_rule -> backprop,
sigmoid -> backprop), an assignment whose rubric criteria are tagged to two of those
concepts, grades one session with mixed outcomes, and prints the resulting mastery
overlay + cohort view. See docs/knowledge-graph-mastery-plan.md for the design.

Usage:
    1. Start Postgres + Neo4j:      docker compose up -d postgres neo4j
    2. Run migrations (see below if this is a fresh volume)
    3. Run the app with your changes live (NOT the `app` docker service, which is a
       stale prebuilt image unless you rebuild it):
           uv run uvicorn fiosra.mvp.main:app --reload --port 8000
       (If something is already bound to :8000 - e.g. a leftover `docker compose up -d`
       that started the `app` service too - either `docker compose stop app` or run
       this script's server on another port with `--port 8010` and set BASE_URL below.)
    4. In another shell:  uv run python scripts/demo_concept_mastery.py
    5. Optionally clean up the seeded course afterward - printed at the end.

This intentionally talks to the API over HTTP, the same way the frontend or a teacher's
browser would, rather than importing services directly - it's exercising the real
request/response contracts, not just the internal functions.
"""

import asyncio
import os

import httpx

BASE_URL = os.environ.get("FIOSRA_DEMO_BASE_URL", "http://127.0.0.1:8000")
STUDENT_ID = "student_demo_01"


async def main() -> None:
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        print(f"--- Using {BASE_URL} ---")

        course = (
            await client.post(
                "/courses",
                json={
                    "title": "Neural Network Learning (demo)",
                    "domain": "machine_learning",
                    "created_by": "teacher_demo",
                    "syllabus_context": "Backprop, chain rule, sigmoid, derivatives.",
                },
            )
        ).json()
        course_id = course["course_id"]
        print(f"Course: {course_id}")

        module = (
            await client.post(
                f"/courses/{course_id}/modules",
                json={"title": "Backpropagation", "description": "How gradients flow backward.", "position": 1},
            )
        ).json()
        module_id = module["module_id"]
        print(f"Module: {module_id}")

        async def make_concept(label: str, definition: str, concept_type: str, level: str) -> str:
            resp = await client.post(
                f"/courses/{course_id}/concept-graph/concepts",
                json={"label": label, "definition": definition, "concept_type": concept_type, "level": level},
            )
            return resp.json()["concept_id"]

        derivatives = await make_concept("Derivatives", "Rate of change of a function.", "method", "atomic_concept")
        chain_rule = await make_concept("Chain Rule", "Differentiating composed functions.", "method", "subtopic")
        sigmoid = await make_concept(
            "Sigmoid Activation", "Sigmoid activation function and its derivative.", "entity", "subtopic"
        )
        backprop = await make_concept(
            "Backpropagation", "Computing gradients via the chain rule through a network.", "process", "topic"
        )
        print(f"Concepts: derivatives={derivatives} chain_rule={chain_rule} sigmoid={sigmoid} backprop={backprop}")

        async def prereq(dependent: str, prerequisite: str) -> None:
            resp = await client.post(
                f"/courses/{course_id}/concept-graph/concepts/{dependent}/prerequisites",
                json={"target_concept_id": prerequisite},
            )
            resp.raise_for_status()

        await prereq(chain_rule, derivatives)
        await prereq(backprop, chain_rule)
        await prereq(backprop, sigmoid)
        print("Prerequisite edges: derivative->chain_rule->backprop, sigmoid->backprop")

        # Seed the assignment directly against the DB-backed generator contract so this
        # demo doesn't burn a live LLM call just to get a rubric shape. In the product,
        # a teacher would author this through /assignments/draft + the Studio UI.
        from uuid import uuid4

        from sqlalchemy import text

        import sys
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from fiosra.mvp.assignment_designer.schemas import (  # noqa: E402
            AssignmentTask,
            AutoScoreEvaluationPlan,
            EvaluationCriterionMap,
            PublicRubricCriterion,
            PublishedAssignmentSpec,
            RubricLevel,
        )
        from fiosra.mvp.database import AsyncSessionLocal  # noqa: E402

        assignment_id = str(uuid4())
        published = PublishedAssignmentSpec(
            title="Derive the Backpropagation Update Rule",
            purpose="Show you can apply the chain rule through a sigmoid activation.",
            task=AssignmentTask(
                prompt="Derive dL/dw for a single sigmoid neuron using the chain rule.",
                scope="One hidden unit, mean-squared error loss.",
                deliverable="A worked derivation with each chain-rule step labeled.",
            ),
            learning_goals=["Apply the chain rule to a composed function.", "Differentiate the sigmoid activation."],
            public_rubric=[
                PublicRubricCriterion(
                    criterion_id="chain_rule_application",
                    title="Chain rule application",
                    description="Correctly applies the chain rule across each composed function.",
                    weight=60.0,
                    levels=[RubricLevel(level_id="met", label="Met", description="Every step is chained correctly.")],
                ),
                PublicRubricCriterion(
                    criterion_id="sigmoid_derivative",
                    title="Sigmoid derivative",
                    description="Correctly computes and uses the sigmoid derivative.",
                    weight=40.0,
                    levels=[RubricLevel(level_id="met", label="Met", description="Derivative is correct and used.")],
                ),
            ],
        )
        evaluation_plan = AutoScoreEvaluationPlan(
            public_rubric_map=[
                EvaluationCriterionMap(
                    public_criterion_id="chain_rule_application",
                    concept_ids=[chain_rule],
                    evidence_expectation="Each derivative step follows from the prior via the chain rule.",
                ),
                EvaluationCriterionMap(
                    public_criterion_id="sigmoid_derivative",
                    concept_ids=[sigmoid],
                    evidence_expectation="Sigmoid derivative is correctly derived and applied.",
                ),
            ],
        )
        import json as _json

        spec = {
            "assignment_id": assignment_id,
            "question_id": "q1",
            "status": "published",
            "published": published.model_dump(),
            "evaluation_plan": evaluation_plan.model_dump(),
            "target_kcs": [chain_rule, sigmoid],
            "canvas_sections": [],
        }
        async with AsyncSessionLocal() as db_session:
            await db_session.execute(
                text(
                    "INSERT INTO assignments (assignment_id, module_id, title, created_by, spec, created_at) "
                    "VALUES (CAST(:assignment_id AS UUID), CAST(:module_id AS UUID), :title, :created_by, "
                    "CAST(:spec AS JSONB), NOW());"
                ),
                {
                    "assignment_id": assignment_id,
                    "module_id": module_id,
                    "title": published.title,
                    "created_by": "teacher_demo",
                    "spec": _json.dumps(spec),
                },
            )
            await db_session.commit()
        print(f"Assignment: {assignment_id} (rubric: chain_rule_application -> {chain_rule}, sigmoid_derivative -> {sigmoid})")

        session = (
            await client.post("/events/session", json={"student_id": STUDENT_ID, "assignment_id": assignment_id})
        ).json()
        session_id = session["session_id"]
        print(f"Student session: {session_id}")

        grade = (
            await client.post(
                f"/evidence/dossier/{session_id}/finalise-grade",
                json={
                    "approved_grade": "B",
                    "teacher_id": "teacher_demo",
                    "criterion_grades": [
                        {"criterion_id": "chain_rule_application", "outcome": "met"},
                        {"criterion_id": "sigmoid_derivative", "outcome": "not_met"},
                    ],
                },
            )
        ).json()
        print(f"Grade finalised: {grade}")

        overlay = (await client.get(f"/courses/{course_id}/concept-graph/mastery/students/{STUDENT_ID}")).json()
        print("\n=== Student mastery overlay ===")
        for node in overlay["nodes"]:
            print(f"  {node['label']:22} state={node['state']:11} score={node['score']:.2f} evidence={node['evidence_count']}")

        cohort = (await client.get(f"/courses/{course_id}/concept-graph/mastery/cohort")).json()
        print("\n=== Cohort distribution (enroll a student first for a real cohort_size) ===")
        for node in cohort["nodes"]:
            print(
                f"  {node['label']:22} strong={node['strong']} developing={node['developing']} "
                f"weak={node['weak']} unassessed={node['unassessed']}"
            )

        print(f"\nOpen the topology + overlay yourself at: {BASE_URL}/docs (Concept Mastery + Curriculum Concept Graph tags)")
        print(f"\nTo clean this demo course up:\n  DELETE FROM courses WHERE course_id = '{course_id}';  -- cascades modules/enrollments/concept_mastery")
        print(f"  (in Neo4j) MATCH (n {{course_id: '{course_id}'}}) DETACH DELETE n;")


if __name__ == "__main__":
    asyncio.run(main())
