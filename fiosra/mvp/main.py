from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from fiosra.mvp.config import settings
from fiosra.mvp.dialogue_router import router as dialogue_router
from fiosra.mvp.events_router import router as events_router
from fiosra.mvp.knowledge_router import router as knowledge_router
from fiosra.mvp.neo4j_client import neo4j_client


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan context manager for startup and shutdown hooks."""
    # Startup
    yield
    # Shutdown: gracefully close Neo4j connection pool
    await neo4j_client.close()


app = FastAPI(
    title=settings.APP_NAME,
    description="Fiosra AI MVP API: Socratic Dialogue & Knowledge Tracing System",
    version="0.1.0",
    lifespan=lifespan,
)

# Enable CORS for Next.js frontend dev servers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(knowledge_router)
app.include_router(events_router)
app.include_router(dialogue_router)


@app.get("/healthz", tags=["System"])
async def health_check() -> dict[str, str]:
    """Basic health check endpoint."""
    return {"status": "ok", "app": settings.APP_NAME}
