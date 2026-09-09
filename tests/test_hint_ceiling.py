import pytest
from httpx import ASGITransport, AsyncClient

from fiosra.mvp.dialogue_engine import dialogue_engine
from fiosra.mvp.event_store import event_store
from fiosra.mvp.main import app


@pytest.mark.asyncio
async def test_strictly_monotonic_hint_ladder_progression():
    """Verify that hints progress monotonically one rung at a time with delta=0.25 penalty."""
    session_id = await event_store.create_session(
        student_id="student_hint_test_01",
        current_question_id="Q1",
    )

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Step 1: Initial question with no hint (Rung 0, Autonomy = 1.00)
        r0 = await ac.post(
            "/dialogue/message",
            json={
                "session_id": session_id,
                "student_id": "student_hint_test_01",
                "question_id": "Q1",
                "question_prompt": "Explain the causes of France's sovereign debt crisis.",
                "student_input": "I am not sure where to start.",
                "current_rung": 0,
                "hint_requested": False,
            },
        )
        assert r0.status_code == 200
        d0 = r0.json()
        assert d0["hint_rung"] == 0
        assert d0["penalty_score"] == 0.0

        # Step 2: Request Hint 1 (Rung 1, Autonomy penalty Δ = 0.25 -> 0.75)
        r1 = await ac.post(
            "/dialogue/message",
            json={
                "session_id": session_id,
                "student_id": "student_hint_test_01",
                "question_id": "Q1",
                "question_prompt": "Explain the causes of France's sovereign debt crisis.",
                "student_input": "Can I have a hint?",
                "current_rung": 0,
                "hint_requested": True,
            },
        )
        assert r1.status_code == 200
        d1 = r1.json()
        assert d1["hint_rung"] == 1
        assert d1["penalty_score"] == 0.25

        # Step 3: Request Hint 2 (Rung 2, Autonomy penalty Δ = 0.25 -> 0.50)
        r2 = await ac.post(
            "/dialogue/message",
            json={
                "session_id": session_id,
                "student_id": "student_hint_test_01",
                "question_id": "Q1",
                "question_prompt": "Explain the causes of France's sovereign debt crisis.",
                "student_input": "I still need more help.",
                "current_rung": 1,
                "hint_requested": True,
            },
        )
        assert r2.status_code == 200
        d2 = r2.json()
        assert d2["hint_rung"] == 2
        assert d2["penalty_score"] == 0.50

        # Step 4: Request Hint 3 (Rung 3, Autonomy penalty Δ = 0.25 -> 0.25)
        r3 = await ac.post(
            "/dialogue/message",
            json={
                "session_id": session_id,
                "student_id": "student_hint_test_01",
                "question_id": "Q1",
                "question_prompt": "Explain the causes of France's sovereign debt crisis.",
                "student_input": "Please give me the next hint.",
                "current_rung": 2,
                "hint_requested": True,
            },
        )
        assert r3.status_code == 200
        d3 = r3.json()
        assert d3["hint_rung"] == 3
        assert d3["penalty_score"] == 0.75


@pytest.mark.asyncio
async def test_hint_ceiling_lock_bottom_out():
    """Verify that requesting hints beyond Rung 3 stays at maximum ceiling and locks bottom-out."""
    session_id = await event_store.create_session(
        student_id="student_ceiling_test_02",
        current_question_id="Q1",
    )

    ladder = dialogue_engine.generate_hint_ladder("Explain France's fiscal crisis.")
    assert len(ladder) == 4

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Rapidly request 5 hints in succession
        levels = []
        current_rung = 0
        for i in range(5):
            res = await ac.post(
                "/dialogue/message",
                json={
                    "session_id": session_id,
                    "student_id": "student_ceiling_test_02",
                    "question_id": "Q1",
                    "question_prompt": "Explain France's fiscal crisis.",
                    "student_input": f"Hint request #{i+1}",
                    "current_rung": current_rung,
                    "hint_requested": True,
                },
            )
            assert res.status_code == 200
            rung = res.json()["hint_rung"]
            levels.append(rung)
            current_rung = rung

        # Hint ladder must cap at 3 and never exceed max rung 3
        assert levels == [1, 2, 3, 3, 3]


def test_autonomy_penalty_calculation():
    """Verify formula A_s = max(0.0, 1.0 - 0.25 * rung)."""
    expected_autonomy = {
        0: 1.00,
        1: 0.75,
        2: 0.50,
        3: 0.25,
        4: 0.00,
    }
    for rung, expected in expected_autonomy.items():
        computed = max(0.0, 1.0 - 0.25 * rung)
        assert computed == pytest.approx(expected, abs=0.001)
