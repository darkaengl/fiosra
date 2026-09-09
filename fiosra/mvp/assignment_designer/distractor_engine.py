import logging
from typing import Any

from sqlalchemy import text

from fiosra.mvp.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


class DistractorEngine:
    """
    Seeds assignments with authentic cognitive traps and diagnostic distractors
    derived directly from the Neo4j/PostgreSQL misconception taxonomy.
    """

    @staticmethod
    async def get_distractors_for_kcs(
        target_kcs: list[str],
        domain: str = "history",
        limit: int = 3,
    ) -> list[dict[str, Any]]:
        """
        Fetches misconceptions associated with the target KCs from the database
        to construct diagnostic distractors and cognitive traps.
        """
        query_sql = text("""
            SELECT
                misconception_id,
                kc_id,
                name,
                flawed_rule,
                remediation_hint
            FROM misconceptions
            WHERE domain = :domain
              AND (:kc_count = 0 OR kc_id = ANY(:target_kcs))
            LIMIT :limit;
        """)

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                query_sql,
                {
                    "domain": domain,
                    "target_kcs": target_kcs,
                    "kc_count": len(target_kcs),
                    "limit": limit,
                },
            )
            rows = result.mappings().all()

        distractors = []
        for r in rows:
            distractors.append({
                "misconception_id": r["misconception_id"],
                "target_kc": r["kc_id"],
                "trap_label": r["name"],
                "flawed_rule": r["flawed_rule"],
                "diagnostic_probe": (
                    f"Distractor: Asserting that '{r['flawed_rule']}' will diagnose "
                    f"misconception {r['misconception_id']}."
                ),
            })
        return distractors


distractor_engine = DistractorEngine()
