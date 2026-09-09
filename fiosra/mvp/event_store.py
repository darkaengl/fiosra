import json
import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import text

from fiosra.mvp.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


class EventStore:
    """
    High-performance append-only JSON event store for student learning sessions.
    Writes immutable events to PostgreSQL with microsecond resolution and supports
    instantaneous chronological flight-recorder trace replays.
    """

    async def create_session(
        self,
        student_id: str,
        assignment_id: UUID | str | None = None,
        current_question_id: str = "q1",
    ) -> str:
        """
        Initializes a new student learning session.
        """
        insert_sql = text("""
            INSERT INTO student_sessions (
                student_id,
                assignment_id,
                current_question_id,
                status,
                started_at,
                last_activity_at
            ) VALUES (
                :student_id,
                :assignment_id,
                :current_question_id,
                'active',
                NOW(),
                NOW()
            )
            RETURNING session_id;
        """)

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                insert_sql,
                {
                    "student_id": student_id,
                    "assignment_id": str(assignment_id) if assignment_id else None,
                    "current_question_id": current_question_id,
                },
            )
            session_id = result.scalar()
            await session.commit()
            return str(session_id)

    async def log_event(
        self,
        session_id: UUID | str,
        student_id: str,
        question_id: str,
        event_type: str,
        payload: dict[str, Any],
        assignment_id: UUID | str | None = None,
    ) -> int:
        """
        Appends an immutable JSON event record with sub-millisecond execution.
        """
        single_cte_sql = text("""
            WITH ins AS (
                INSERT INTO session_events (
                    session_id,
                    student_id,
                    assignment_id,
                    question_id,
                    event_type,
                    created_at,
                    payload
                ) VALUES (
                    :session_id,
                    :student_id,
                    :assignment_id,
                    :question_id,
                    :event_type,
                    NOW(),
                    CAST(:payload AS JSONB)
                )
                RETURNING event_id
            ),
            upd AS (
                UPDATE student_sessions
                SET last_activity_at = NOW(),
                    current_question_id = :question_id
                WHERE session_id = :session_id
            )
            SELECT event_id FROM ins;
        """)

        payload_json = json.dumps(payload)

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                single_cte_sql,
                {
                    "session_id": str(session_id),
                    "student_id": student_id,
                    "assignment_id": str(assignment_id) if assignment_id else None,
                    "question_id": question_id,
                    "event_type": event_type,
                    "payload": payload_json,
                },
            )
            event_id = result.scalar()
            await session.commit()
            return int(event_id)

    async def get_session_events(
        self,
        session_id: UUID | str,
        limit: int = 1000,
    ) -> list[dict[str, Any]]:
        """
        Replays the exact chronological flight-recorder trace of all events in a session.
        """
        query_sql = text("""
            SELECT
                event_id,
                session_id,
                student_id,
                assignment_id,
                question_id,
                event_type,
                created_at,
                payload
            FROM session_events
            WHERE session_id = :session_id
            ORDER BY created_at ASC, event_id ASC
            LIMIT :limit;
        """)

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                query_sql,
                {"session_id": str(session_id), "limit": limit},
            )
            rows = result.mappings().all()
            events = []
            for r in rows:
                event_dict = dict(r)
                if isinstance(event_dict["created_at"], datetime):
                    event_dict["created_at"] = event_dict["created_at"].isoformat()
                event_dict["session_id"] = str(event_dict["session_id"])
                if event_dict["assignment_id"]:
                    event_dict["assignment_id"] = str(event_dict["assignment_id"])
                events.append(event_dict)
            return events

    async def get_session_details(self, session_id: UUID | str) -> dict[str, Any] | None:
        """
        Retrieves the current metadata and state of a student session.
        """
        query_sql = text("""
            SELECT
                session_id,
                student_id,
                assignment_id,
                current_question_id,
                status,
                started_at,
                last_activity_at,
                completed_at
            FROM student_sessions
            WHERE session_id = :session_id;
        """)

        async with AsyncSessionLocal() as session:
            result = await session.execute(query_sql, {"session_id": str(session_id)})
            row = result.mappings().first()
            if not row:
                return None
            session_dict = dict(row)
            session_dict["session_id"] = str(session_dict["session_id"])
            if session_dict["assignment_id"]:
                session_dict["assignment_id"] = str(session_dict["assignment_id"])
            for key in ("started_at", "last_activity_at", "completed_at"):
                if isinstance(session_dict[key], datetime):
                    session_dict[key] = session_dict[key].isoformat()
            return session_dict

    async def get_session(self, session_id: UUID | str) -> dict[str, Any] | None:
        """Alias for get_session_details."""
        return await self.get_session_details(session_id)

    async def complete_session(self, session_id: UUID | str) -> None:
        """Marks a session as completed with timestamp."""
        update_sql = text("""
            UPDATE student_sessions
            SET status = 'completed',
                completed_at = NOW(),
                last_activity_at = NOW()
            WHERE session_id = :session_id;
        """)
        async with AsyncSessionLocal() as session:
            await session.execute(update_sql, {"session_id": str(session_id)})
            await session.commit()


event_store = EventStore()

