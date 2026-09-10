import asyncio
import hashlib
import hmac
import json
import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import text

from fiosra.mvp.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


class EventStore:
    """Append-only learning-event store with server-authoritative session state."""

    def __init__(self) -> None:
        self._pool_primed = False
        self._priming_lock = asyncio.Lock()

    async def _ensure_pool_primed(self) -> None:
        """Open a small set of reusable asyncpg connections before the first learner write.

        This keeps the first concurrent classroom interaction from paying multiple
        independent TCP and authentication setup costs at once.
        """
        if self._pool_primed:
            return
        async with self._priming_lock:
            if self._pool_primed:
                return

            async def open_connection() -> None:
                async with AsyncSessionLocal() as session:
                    await session.execute(text("SELECT 1"))

            await asyncio.gather(*(open_connection() for _ in range(5)))
            self._pool_primed = True

    async def create_session(
        self,
        student_id: str,
        assignment_id: UUID | str | None = None,
        current_question_id: str = "q1",
        access_token: str | None = None,
    ) -> str:
        await self._ensure_pool_primed()
        insert_sql = text("""
            INSERT INTO student_sessions (
                student_id, assignment_id, current_question_id, access_token_hash, status, started_at, last_activity_at
            ) VALUES (
                :student_id, :assignment_id, :current_question_id, :access_token_hash, 'active', NOW(), NOW()
            ) RETURNING session_id;
        """)
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                insert_sql,
                {
                    "student_id": student_id,
                    "assignment_id": str(assignment_id) if assignment_id else None,
                    "current_question_id": current_question_id,
                    "access_token_hash": self._hash_access_token(access_token) if access_token else None,
                },
            )
            session_id = result.scalar()
            await session.commit()
        return str(session_id)

    @staticmethod
    def _hash_access_token(access_token: str) -> str:
        return hashlib.sha256(access_token.encode("utf-8")).hexdigest()

    async def has_session_access(self, session_id: UUID | str, access_token: str | None) -> bool:
        """Verify a browser-held capability without exposing its stored digest."""
        if not access_token:
            return False
        query_sql = text("""
            SELECT access_token_hash
            FROM student_sessions
            WHERE session_id = :session_id;
        """)
        async with AsyncSessionLocal() as session:
            result = await session.execute(query_sql, {"session_id": str(session_id)})
            token_hash = result.scalar()
        return bool(token_hash) and hmac.compare_digest(
            str(token_hash), self._hash_access_token(access_token)
        )

    async def log_event(
        self,
        session_id: UUID | str,
        student_id: str,
        question_id: str,
        event_type: str,
        payload: dict[str, Any],
        assignment_id: UUID | str | None = None,
    ) -> int:
        """Append an immutable event and atomically refresh the active session marker."""
        single_cte_sql = text("""
            WITH ins AS (
                INSERT INTO session_events (
                    session_id, student_id, assignment_id, question_id, event_type, created_at, payload
                ) VALUES (
                    :session_id, :student_id, :assignment_id, :question_id, :event_type, NOW(),
                    CAST(:payload AS JSONB)
                ) RETURNING event_id
            ), upd AS (
                UPDATE student_sessions
                SET last_activity_at = NOW(), current_question_id = :question_id
                WHERE session_id = :session_id
            ) SELECT event_id FROM ins;
        """)
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                single_cte_sql,
                {
                    "session_id": str(session_id),
                    "student_id": student_id,
                    "assignment_id": str(assignment_id) if assignment_id else None,
                    "question_id": question_id,
                    "event_type": event_type,
                    "payload": json.dumps(payload),
                },
            )
            event_id = result.scalar()
            await session.commit()
        return int(event_id)

    async def get_current_hint_rung(self, session_id: UUID | str) -> int:
        """Read the maximum hint rung already delivered from the immutable event stream.

        The client may render this value, but cannot authoritatively advance it.
        """
        sql = text("""
            SELECT COALESCE(MAX(COALESCE((payload ->> 'hint_rung')::int, 0)), 0)
            FROM session_events
            WHERE session_id = :session_id
              AND event_type IN ('hint_delivered', 'tutor_turn_completed', 'adversarial_probe_defended');
        """)
        async with AsyncSessionLocal() as session:
            result = await session.execute(sql, {"session_id": str(session_id)})
            rung = result.scalar()
        return int(rung or 0)

    async def get_session_events(
        self,
        session_id: UUID | str,
        limit: int = 1000,
    ) -> list[dict[str, Any]]:
        query_sql = text("""
            SELECT event_id, session_id, student_id, assignment_id, question_id, event_type, created_at, payload
            FROM session_events
            WHERE session_id = :session_id
            ORDER BY created_at ASC, event_id ASC
            LIMIT :limit;
        """)
        async with AsyncSessionLocal() as session:
            result = await session.execute(query_sql, {"session_id": str(session_id), "limit": limit})
            rows = result.mappings().all()
        events = []
        for row in rows:
            event = dict(row)
            if isinstance(event["created_at"], datetime):
                event["created_at"] = event["created_at"].isoformat()
            event["session_id"] = str(event["session_id"])
            if event["assignment_id"]:
                event["assignment_id"] = str(event["assignment_id"])
            events.append(event)
        return events

    async def get_session_details(self, session_id: UUID | str) -> dict[str, Any] | None:
        query_sql = text("""
            SELECT session_id, student_id, assignment_id, current_question_id, status,
                   started_at, last_activity_at, completed_at
            FROM student_sessions WHERE session_id = :session_id;
        """)
        async with AsyncSessionLocal() as session:
            result = await session.execute(query_sql, {"session_id": str(session_id)})
            row = result.mappings().first()
        if not row:
            return None
        session_data = dict(row)
        session_data["session_id"] = str(session_data["session_id"])
        if session_data["assignment_id"]:
            session_data["assignment_id"] = str(session_data["assignment_id"])
        for key in ("started_at", "last_activity_at", "completed_at"):
            if isinstance(session_data[key], datetime):
                session_data[key] = session_data[key].isoformat()
        return session_data

    async def get_session(self, session_id: UUID | str) -> dict[str, Any] | None:
        """Compatibility alias for session detail lookup."""
        return await self.get_session_details(session_id)

    async def submit_session(self, session_id: UUID | str) -> dict[str, Any] | None:
        """Mark active work ready for educator review without allowing student grading."""
        update_sql = text("""
            UPDATE student_sessions
            SET status = 'submitted', last_activity_at = NOW()
            WHERE session_id = :session_id AND status = 'active'
            RETURNING session_id, student_id, assignment_id, current_question_id, status;
        """)
        async with AsyncSessionLocal() as session:
            result = await session.execute(update_sql, {"session_id": str(session_id)})
            row = result.mappings().first()
            await session.commit()
        return dict(row) if row else None

    async def complete_session(self, session_id: UUID | str) -> None:
        update_sql = text("""
            UPDATE student_sessions
            SET status = 'completed', completed_at = NOW(), last_activity_at = NOW()
            WHERE session_id = :session_id;
        """)
        async with AsyncSessionLocal() as session:
            await session.execute(update_sql, {"session_id": str(session_id)})
            await session.commit()


event_store = EventStore()
