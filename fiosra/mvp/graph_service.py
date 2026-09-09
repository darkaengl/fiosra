import logging
from typing import Any

from fiosra.mvp.neo4j_client import Neo4jClient, neo4j_client

logger = logging.getLogger(__name__)


class GraphService:
    """
    Curriculum Knowledge Graph service operating directly on Neo4j 5.
    Provides async prerequisite traversal, learning frontier discovery,
    schema constraints management, and acyclicity validation.
    """

    def __init__(self, client: Neo4jClient | None = None) -> None:
        self.client = client or neo4j_client

    async def init_schema(self) -> None:
        """
        Initializes uniqueness constraints and performance indices in Neo4j.
        """
        queries = [
            """
            CREATE CONSTRAINT kc_id_unique IF NOT EXISTS
            FOR (k:KnowledgeComponent) REQUIRE k.kc_id IS UNIQUE
            """,
            """
            CREATE CONSTRAINT misconception_id_unique IF NOT EXISTS
            FOR (m:Misconception) REQUIRE m.misconception_id IS UNIQUE
            """,
            """
            CREATE INDEX kc_domain_idx IF NOT EXISTS
            FOR (k:KnowledgeComponent) ON (k.domain)
            """,
        ]
        async with self.client.get_session() as session:
            for q in queries:
                await session.run(q)
        logger.info("Neo4j schema constraints and indices initialized.")

    async def seed_curriculum(self, kcs: list[dict[str, Any]]) -> dict[str, int]:
        """
        Upserts Knowledge Components and their prerequisite DAG edges into Neo4j.
        Returns counts of seeded nodes and edges.
        """
        await self.init_schema()

        # 1. Upsert nodes
        upsert_nodes_cypher = """
        UNWIND $kcs AS item
        MERGE (k:KnowledgeComponent {kc_id: item.kc_id})
        SET k.label = item.label,
            k.domain = item.domain,
            k.bloom_level = item.bloom_level,
            k.description = item.description,
            k.estimated_difficulty = item.estimated_difficulty
        RETURN count(k) AS total_nodes
        """

        # 2. Extract edge list: (target_kc_id, prerequisite_id)
        edges = []
        for item in kcs:
            target_id = item["kc_id"]
            for prereq_id in item.get("prerequisite_ids", []):
                edges.append({"target_id": target_id, "prereq_id": prereq_id})

        upsert_edges_cypher = """
        UNWIND $edges AS edge
        MATCH (target:KnowledgeComponent {kc_id: edge.target_id})
        MATCH (prereq:KnowledgeComponent {kc_id: edge.prereq_id})
        MERGE (target)-[r:REQUIRES]->(prereq)
        RETURN count(r) AS total_edges
        """

        async with self.client.get_session() as session:
            await session.run(upsert_nodes_cypher, {"kcs": kcs})
            if edges:
                await session.run(upsert_edges_cypher, {"edges": edges})

        return {"nodes_seeded": len(kcs), "edges_seeded": len(edges)}

    async def get_prerequisites(self, kc_id: str, depth: int = 10) -> list[str]:
        """
        Returns all prerequisite KC IDs (transitive dependencies) required before kc_id.
        """
        cypher = f"""
        MATCH (target:KnowledgeComponent {{kc_id: $kc_id}})-[:REQUIRES*1..{depth}]->(prereq:KnowledgeComponent)
        RETURN DISTINCT prereq.kc_id AS prereq_id
        """
        async with self.client.get_session() as session:
            result = await session.run(cypher, {"kc_id": kc_id})
            records = await result.data()
            return [r["prereq_id"] for r in records]

    async def get_learning_frontier(
        self,
        mastered_kc_ids: list[str],
        domain: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Calculates the student's optimal Learning Frontier.
        Returns all unmastered KCs whose prerequisites are completely satisfied
        by the set of mastered_kc_ids.
        """
        cypher = """
        MATCH (k:KnowledgeComponent)
        WHERE NOT k.kc_id IN $mastered_kc_ids
          AND ($domain IS NULL OR k.domain = $domain)
        OPTIONAL MATCH (k)-[:REQUIRES]->(p:KnowledgeComponent)
        WITH k, collect(p.kc_id) AS required_prereqs
        WHERE all(p_id IN required_prereqs WHERE p_id IN $mastered_kc_ids)
        RETURN k.kc_id AS kc_id,
               k.label AS label,
               k.domain AS domain,
               k.bloom_level AS bloom_level,
               k.description AS description,
               k.estimated_difficulty AS estimated_difficulty,
               required_prereqs
        ORDER BY k.estimated_difficulty ASC, k.bloom_level ASC
        """
        async with self.client.get_session() as session:
            result = await session.run(
                cypher,
                {"mastered_kc_ids": mastered_kc_ids, "domain": domain},
            )
            return await result.data()

    async def check_acyclicity(self) -> bool:
        """
        Validates that the prerequisite graph contains zero directed cycles.
        Returns True if the graph is a strict DAG, False if cycles exist.
        """
        cypher = """
        MATCH path = (k:KnowledgeComponent)-[:REQUIRES*1..20]->(k)
        RETURN count(path) = 0 AS is_acyclic
        """
        async with self.client.get_session() as session:
            result = await session.run(cypher)
            record = await result.single()
            return bool(record["is_acyclic"]) if record else True

    async def get_kc_details(self, kc_id: str) -> dict[str, Any] | None:
        """
        Fetches a single KC node with its direct prerequisites and direct dependents.
        """
        cypher = """
        MATCH (k:KnowledgeComponent {kc_id: $kc_id})
        OPTIONAL MATCH (k)-[:REQUIRES]->(prereq:KnowledgeComponent)
        OPTIONAL MATCH (dependent:KnowledgeComponent)-[:REQUIRES]->(k)
        RETURN k.kc_id AS kc_id,
               k.label AS label,
               k.domain AS domain,
               k.bloom_level AS bloom_level,
               k.description AS description,
               k.estimated_difficulty AS estimated_difficulty,
               collect(DISTINCT prereq.kc_id) AS direct_prerequisites,
               collect(DISTINCT dependent.kc_id) AS direct_dependents
        """
        async with self.client.get_session() as session:
            result = await session.run(cypher, {"kc_id": kc_id})
            record = await result.single()
            if not record or record["kc_id"] is None:
                return None
            return dict(record)


graph_service = GraphService()
