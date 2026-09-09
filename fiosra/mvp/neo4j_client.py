import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Self

from neo4j import AsyncDriver, AsyncGraphDatabase, AsyncSession
from neo4j.exceptions import Neo4jError, ServiceUnavailable, SessionExpired

from fiosra.mvp.config import settings

logger = logging.getLogger(__name__)

class Neo4jClient:
    """
    Singleton client manager for asynchronous Neo4j graph database operations.
    Maintains a persistent connection pool using the Bolt protocol.
    """
    _instance: Self | None = None
    _driver: AsyncDriver | None = None

    def __new__(cls) -> Self:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @property
    def driver(self) -> AsyncDriver:
        if self._driver is None:
            self._driver = AsyncGraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
            )
        return self._driver

    @asynccontextmanager
    async def get_session(self, database: str = "neo4j") -> AsyncGenerator[AsyncSession, None]:
        """
        Async context manager providing a safe, scoped Neo4j session.
        """
        session = self.driver.session(database=database)
        try:
            yield session
        finally:
            await session.close()

    async def health_check(self) -> bool:
        """
        Verifies Bolt protocol connectivity with the Neo4j cluster.
        Returns True if a heartbeat query succeeds, False otherwise.
        """
        try:
            async with self.get_session() as session:
                result = await session.run("RETURN 1 AS alive")
                record = await result.single()
                return record is not None and record["alive"] == 1
        except (Neo4jError, ServiceUnavailable, SessionExpired, OSError, ConnectionError) as e:
            logger.warning(f"Neo4j health check failed: {e}")
            return False

    async def close(self) -> None:
        """Gracefully closes the driver connection pool."""
        if self._driver is not None:
            await self._driver.close()
            self._driver = None


# Module-level singleton instance
neo4j_client = Neo4jClient()

async def get_neo4j_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for injecting Neo4j async sessions."""
    async with neo4j_client.get_session() as session:
        yield session
