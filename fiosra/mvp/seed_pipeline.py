import asyncio
import hashlib
import json
import logging
import math
from pathlib import Path
from typing import Any

from sqlalchemy import text

from fiosra.mvp.database import AsyncSessionLocal
from fiosra.mvp.graph_service import graph_service

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

SEEDS_DIR = Path(__file__).parent.parent / "knowledge" / "seeds"


def generate_deterministic_embedding(text_content: str, dimensions: int = 1536) -> list[float]:
    """
    Generates a deterministic, unit-normalized floating-point vector embedding
    from text content. Ensures vector operations in pgvector work deterministically
    in offline development and CI environments.
    """
    raw_values = []
    for i in range(dimensions):
        token = f"{text_content}:{i}".encode()
        hash_digest = hashlib.sha256(token).hexdigest()
        val = (int(hash_digest[:8], 16) / 0xFFFFFFFF) * 2.0 - 1.0
        raw_values.append(val)

    # L2 normalize
    norm = math.sqrt(sum(x * x for x in raw_values)) or 1.0
    return [round(x / norm, 6) for x in raw_values]


async def seed_neo4j_curriculum() -> dict[str, int]:
    """
    Reads knowledge_components_curriculum.seed.json and hydrates Neo4j.
    """
    seed_file = SEEDS_DIR / "knowledge_components_curriculum.seed.json"
    if not seed_file.exists():
        raise FileNotFoundError(f"Missing curriculum seed file at {seed_file}")

    kcs: list[dict[str, Any]] = json.loads(seed_file.read_text(encoding="utf-8"))
    stats = await graph_service.seed_curriculum(kcs)
    is_acyclic = await graph_service.check_acyclicity()

    logger.info(
        f"Neo4j Hydration complete: {stats['nodes_seeded']} KCs, "
        f"{stats['edges_seeded']} prerequisite edges. Strict DAG Acyclic: {is_acyclic}"
    )
    if not is_acyclic:
        raise ValueError("Curriculum graph contains cycles! Violates DAG invariant.")

    return stats


async def seed_postgres_misconceptions() -> int:
    """
    Reads misconception seed JSONs and hydrates the PostgreSQL misconceptions table with pgvector embeddings.
    """
    seed_files = [
        SEEDS_DIR / "misconceptions_language_history.seed.json",
        SEEDS_DIR / "misconceptions_algebra_geometry.seed.json",
    ]

    all_misconceptions: list[dict[str, Any]] = []
    for sf in seed_files:
        if sf.exists():
            records = json.loads(sf.read_text(encoding="utf-8"))
            all_misconceptions.extend(records)

    logger.info(f"Loaded {len(all_misconceptions)} misconceptions from seed files.")

    upsert_sql = text("""
        INSERT INTO misconceptions (
            misconception_id,
            kc_id,
            domain,
            name,
            flawed_rule,
            remediation_hint,
            embedding
        ) VALUES (
            :misconception_id,
            :kc_id,
            :domain,
            :name,
            :flawed_rule,
            :remediation_hint,
            :embedding
        )
        ON CONFLICT (misconception_id) DO UPDATE SET
            kc_id = EXCLUDED.kc_id,
            domain = EXCLUDED.domain,
            name = EXCLUDED.name,
            flawed_rule = EXCLUDED.flawed_rule,
            remediation_hint = EXCLUDED.remediation_hint,
            embedding = EXCLUDED.embedding;
    """)

    count = 0
    async with AsyncSessionLocal() as session:
        for item in all_misconceptions:
            hints = item.get("remediation_hints", [])
            ladder_text = "\n".join(f"[Rung {h.get('level', 0)}]: {h.get('hint_text', '')}" for h in hints)
            flawed_rule = (
                item.get("flawed_rule")
                or item.get("remediation_strategy")
                or item.get("description", "")
            )
            combined_text = f"{item['label']} {item.get('description', '')} {flawed_rule}"
            embedding_vector = generate_deterministic_embedding(combined_text)

            embedding_str = f"[{','.join(str(v) for v in embedding_vector)}]"

            await session.execute(
                upsert_sql,
                {
                    "misconception_id": item["misconception_id"],
                    "kc_id": item["knowledge_component"],
                    "domain": item["domain"],
                    "name": item["label"],
                    "flawed_rule": flawed_rule,
                    "remediation_hint": ladder_text,
                    "embedding": embedding_str,
                },
            )
            count += 1

        await session.commit()

    logger.info(f"PostgreSQL Hydration complete: {count} misconceptions seeded with vector embeddings.")
    return count


async def search_nearest_misconceptions(
    query_text: str,
    limit: int = 3,
    domain: str | None = None,
) -> list[dict[str, Any]]:
    """
    Searches the nearest misconception traps using pgvector cosine distance.
    """
    query_vector = generate_deterministic_embedding(query_text)
    vector_str = f"[{','.join(str(v) for v in query_vector)}]"

    query_sql = text("""
        SELECT
            misconception_id,
            kc_id,
            domain,
            name,
            flawed_rule,
            remediation_hint,
            1 - (embedding <=> CAST(:query_vec AS vector)) AS similarity
        FROM misconceptions
        WHERE (CAST(:domain AS VARCHAR) IS NULL OR domain = CAST(:domain AS VARCHAR))
        ORDER BY embedding <=> CAST(:query_vec AS vector) ASC
        LIMIT :limit;
    """)

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            query_sql,
            {
                "query_vec": vector_str,
                "domain": domain,
                "limit": limit,
            },
        )
        rows = result.mappings().all()
        return [dict(r) for r in rows]


async def run_seed_pipeline() -> None:
    """Executes the complete dual-database seeding pipeline."""
    logger.info("Starting Dual-Database Hydration Pipeline...")
    neo4j_stats = await seed_neo4j_curriculum()
    pg_count = await seed_postgres_misconceptions()
    logger.info(
        f"Seeding completed successfully! Neo4j: {neo4j_stats['nodes_seeded']} KCs, "
        f"Postgres: {pg_count} Misconceptions."
    )


if __name__ == "__main__":
    asyncio.run(run_seed_pipeline())
