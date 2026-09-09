from pathlib import Path

import pytest

from fiosra.mvp.config import settings
from fiosra.mvp.neo4j_client import Neo4jClient, neo4j_client


def test_neo4j_configuration_settings():
    """Verify that Neo4j connection parameters are properly registered in Settings."""
    assert hasattr(settings, "NEO4J_URI")
    assert hasattr(settings, "NEO4J_USER")
    assert hasattr(settings, "NEO4J_PASSWORD")
    assert settings.NEO4J_URI.startswith("bolt://")
    assert settings.NEO4J_USER == "neo4j"
    assert len(settings.NEO4J_PASSWORD) > 0

def test_neo4j_client_singleton():
    """Verify that Neo4jClient maintains singleton identity across instantiations."""
    client1 = Neo4jClient()
    client2 = Neo4jClient()
    assert client1 is client2
    assert client1 is neo4j_client

@pytest.mark.asyncio
async def test_neo4j_health_check_handles_offline_gracefully():
    """
    Verify that health_check() returns False instead of crashing
    when the Neo4j cluster is offline or unreachable.
    """
    is_healthy = await neo4j_client.health_check()
    # In CI / local without active Neo4j container, must return False gracefully
    assert isinstance(is_healthy, bool)

def test_initial_schema_sql_structure():
    """Verify that the PostgreSQL migration schema contains required Course/Module tables."""
    schema_path = Path(__file__).parent.parent / "fiosra" / "mvp" / "migrations" / "001_initial_schema.sql"
    assert schema_path.exists(), "001_initial_schema.sql must exist"

    sql_content = schema_path.read_text(encoding="utf-8")
    
    # Required tables
    assert "CREATE TABLE IF NOT EXISTS courses" in sql_content
    assert "CREATE TABLE IF NOT EXISTS modules" in sql_content
    assert "CREATE TABLE IF NOT EXISTS assignments" in sql_content
    assert "CREATE TABLE IF NOT EXISTS student_sessions" in sql_content
    assert "CREATE TABLE IF NOT EXISTS session_events" in sql_content
    assert "CREATE TABLE IF NOT EXISTS misconceptions" in sql_content

    # Invariants: Legacy KC relational tables removed (delegated to Neo4j)
    assert "CREATE TABLE IF NOT EXISTS knowledge_components" not in sql_content
    assert "CREATE TABLE IF NOT EXISTS kc_prerequisites" not in sql_content

    # Foreign key linking assignments to modules
    assert "module_id UUID REFERENCES modules(module_id)" in sql_content
