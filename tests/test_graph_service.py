import time

import pytest
from httpx import ASGITransport, AsyncClient

from fiosra.mvp.graph_service import graph_service
from fiosra.mvp.main import app
from fiosra.mvp.seed_pipeline import search_nearest_misconceptions


@pytest.mark.asyncio
async def test_knowledge_graph_acyclicity():
    """Verify that the seeded curriculum in Neo4j contains zero cycles."""
    is_acyclic = await graph_service.check_acyclicity()
    assert is_acyclic is True, "Curriculum graph contains cycles!"


@pytest.mark.asyncio
async def test_prerequisite_transitive_traversal():
    """Verify that multi-hop prerequisite traversal returns all upstream dependencies."""
    prereqs = await graph_service.get_prerequisites("KC_HIST_DECL_RIGHTS_MAN")
    assert isinstance(prereqs, list)
    assert len(prereqs) >= 5

    # Foundational prerequisites must be present in the transitive closure
    assert "KC_HIST_ANCIEN_REGIME" in prereqs
    assert "KC_HIST_TENNIS_COURT_OATH" in prereqs
    assert "KC_HIST_POPULAR_SOV" in prereqs
    assert "KC_HIST_ESTATES_GENERAL" in prereqs


@pytest.mark.asyncio
async def test_learning_frontier_calculation():
    """
    Verify learning frontier discovery:
    - Initially, root nodes (0 prerequisites) are on the frontier.
    - When prerequisites are mastered, downstream concepts appear.
    """
    # 1. Base frontier for history with nothing mastered
    base_frontier = await graph_service.get_learning_frontier([], domain="history")
    base_ids = [kc["kc_id"] for kc in base_frontier]
    assert "KC_HIST_ANCIEN_REGIME" in base_ids
    assert "KC_HIST_TIMELINE_SEQUENCING" in base_ids
    assert "KC_HIST_ESTATES_GENERAL" not in base_ids  # Requires prerequisites

    # 2. Frontier after mastering ANCIEN_REGIME
    next_frontier = await graph_service.get_learning_frontier(
        ["KC_HIST_ANCIEN_REGIME"],
        domain="history",
    )
    next_ids = [kc["kc_id"] for kc in next_frontier]
    assert "KC_HIST_ANCIEN_REGIME" not in next_ids  # Already mastered
    assert "KC_HIST_THREE_ESTATES" in next_ids      # Unlocked
    assert "KC_HIST_FRENCH_DEBT" in next_ids        # Unlocked
    assert "KC_HIST_POPULAR_SOV" in next_ids        # Unlocked
    assert "KC_HIST_ESTATES_GENERAL" not in next_ids  # Needs both THREE_ESTATES and FRENCH_DEBT


@pytest.mark.asyncio
async def test_graph_traversal_latency_sla():
    """Verify that prerequisite traversal achieves < 15ms latency SLA."""
    # Warmup
    await graph_service.get_prerequisites("KC_HIST_DECL_RIGHTS_MAN")

    latencies_ms = []
    for _ in range(10):
        t0 = time.perf_counter()
        await graph_service.get_prerequisites("KC_HIST_DECL_RIGHTS_MAN")
        latencies_ms.append((time.perf_counter() - t0) * 1000)

    avg_latency = sum(latencies_ms) / len(latencies_ms)
    assert avg_latency < 15.0, f"Average latency ({avg_latency:.2f}ms) exceeded 15ms SLA"


@pytest.mark.asyncio
async def test_pgvector_misconception_similarity():
    """Verify that pgvector cosine similarity search retrieves relevant traps."""
    query = "The Third Estate was made up solely of uneducated peasants with no money"
    results = await search_nearest_misconceptions(query, limit=3, domain="history")

    assert len(results) > 0
    assert "misconception_id" in results[0]
    assert "name" in results[0]
    assert "similarity" in results[0]
    assert results[0]["domain"] == "history"

    # Verify that results are sorted in descending order of similarity
    similarities = [r["similarity"] for r in results]
    assert similarities == sorted(similarities, reverse=True)


@pytest.mark.asyncio
async def test_fastapi_knowledge_endpoints():
    """Verify that FastAPI knowledge router endpoints function correctly."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Health check
        res = await client.get("/healthz")
        assert res.status_code == 200
        assert res.json()["status"] == "ok"

        # 2. Graph integrity
        res = await client.get("/knowledge/integrity")
        assert res.status_code == 200
        assert res.json()["is_acyclic"] is True

        # 3. KC details
        res = await client.get("/knowledge/kcs/KC_HIST_ANCIEN_REGIME")
        assert res.status_code == 200
        data = res.json()
        assert data["kc_id"] == "KC_HIST_ANCIEN_REGIME"
        assert len(data["direct_dependents"]) > 0

        # 4. Prerequisites endpoint
        res = await client.get("/knowledge/kcs/KC_HIST_DECL_RIGHTS_MAN/prerequisites")
        assert res.status_code == 200
        assert len(res.json()["prerequisites"]) >= 5

        # 5. Frontier endpoint
        res = await client.post(
            "/knowledge/frontier",
            json={"mastered_kc_ids": ["KC_HIST_ANCIEN_REGIME"], "domain": "history"},
        )
        assert res.status_code == 200
        frontier = res.json()
        frontier_ids = [k["kc_id"] for k in frontier]
        assert "KC_HIST_THREE_ESTATES" in frontier_ids

        # 6. Misconception search endpoint
        res = await client.post(
            "/knowledge/misconceptions/search",
            json={
                "query": "Marie Antoinette bankrupted France by spending money on dresses",
                "limit": 3,
                "domain": "history",
            },
        )
        assert res.status_code == 200
        matches = res.json()
        assert len(matches) == 3
        assert matches[0]["domain"] == "history"
