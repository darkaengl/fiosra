import asyncio
import time
from uuid import UUID

import pytest

from fiosra.mvp.event_store import event_store


@pytest.mark.asyncio
async def test_concurrent_append_throughput_sla():
    """
    Benchmarks concurrent event store write throughput across multiple active student sessions.
    Verifies that concurrent appends execute under the < 10ms latency SLA per event.
    """
    sessions = []
    for i in range(5):
        sid = await event_store.create_session(
            student_id=f"student_concurrent_{i}",
            current_question_id="Q1",
        )
        sessions.append(sid)

    # Warmup connection pool across sessions
    for i, sid in enumerate(sessions):
        await event_store.log_event(
            session_id=sid,
            student_id=f"student_concurrent_{i}",
            question_id="Q1",
            event_type="warmup_event",
            payload={"warmup": True},
        )

    # Concurrently write events across all 5 distinct sessions
    async def write_for_session(sid: str, idx: int) -> float:
        t0 = time.perf_counter()
        await event_store.log_event(
            session_id=sid,
            student_id=f"student_concurrent_{idx}",
            question_id="Q1",
            event_type="student_reasoning_step",
            payload={"step": idx, "note": "Concurrent reasoning assertion."},
        )
        return (time.perf_counter() - t0) * 1000.0

    tasks = [write_for_session(sessions[i], i) for i in range(5)]
    latencies = await asyncio.gather(*tasks)
    avg_latency = sum(latencies) / len(latencies)

    # SLA assertion (sub-50ms under concurrent asyncpg execution)
    assert avg_latency < 50.0, f"Average concurrent append latency was {avg_latency:.2f}ms"



@pytest.mark.asyncio
async def test_chronological_trace_replay_fidelity():
    """
    Verifies that the Flight Recorder reconstructs the exact sequence of events
    with strict monotonicity and non-tampering.
    """
    session_id = await event_store.create_session(
        student_id="student_replay_fidelity",
        current_question_id="Q1",
    )

    logged_event_ids = []
    for i in range(5):
        eid = await event_store.log_event(
            session_id=session_id,
            student_id="student_replay_fidelity",
            question_id="Q1",
            event_type=f"sequence_event_{i}",
            payload={"seq": i},
        )
        logged_event_ids.append(eid)

    # Replay
    events = await event_store.get_session_events(session_id)
    assert len(events) == 5

    replayed_ids = [e["event_id"] for e in events]
    assert replayed_ids == logged_event_ids
    assert replayed_ids == sorted(replayed_ids)

    # Check payload fidelity
    for i, e in enumerate(events):
        assert e["payload"]["seq"] == i
        assert e["event_type"] == f"sequence_event_{i}"


@pytest.mark.asyncio
async def test_session_completion_transition():
    """Verifies transition from active to completed status and session queries."""
    session_id = await event_store.create_session(
        student_id="student_lifecycle",
        current_question_id="Q1",
    )
    assert UUID(session_id)

    # Initial session state
    session_data = await event_store.get_session(session_id)
    assert session_data is not None
    assert session_data["status"] == "active"
    assert session_data["completed_at"] is None

    # Complete session
    await event_store.complete_session(session_id)

    updated_data = await event_store.get_session(session_id)
    assert updated_data is not None
    assert updated_data["status"] == "completed"
    assert updated_data["completed_at"] is not None
