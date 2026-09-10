from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from fiosra.mvp.assignment_designer.router import router as assignment_router
from fiosra.mvp.config import settings
from fiosra.mvp.courses.router import router as courses_router
from fiosra.mvp.dialogue_router import router as dialogue_router
from fiosra.mvp.events_router import router as events_router
from fiosra.mvp.evidence_dossier.router import router as evidence_router
from fiosra.mvp.knowledge_router import router as knowledge_router
from fiosra.mvp.learning_canvas_router import router as learning_canvas_router
from fiosra.mvp.learning_document_router import router as learning_document_router
from fiosra.mvp.neo4j_client import neo4j_client
from fiosra.mvp.socratic_probe_router import router as socratic_probe_router


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

# Enable CORS only for configured local frontend development origins.
cors_origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include Routers
app.include_router(knowledge_router)
app.include_router(events_router)
app.include_router(learning_canvas_router)
app.include_router(learning_document_router)
app.include_router(socratic_probe_router)
app.include_router(dialogue_router)
app.include_router(evidence_router)
app.include_router(assignment_router)
app.include_router(courses_router)

# Mount Static UI Frontend (Svelte production build or legacy fallback)
DIST_DIR = Path(__file__).resolve().parent.parent.parent / "ui-ux" / "frontend-dist"
LEGACY_DIR = Path(__file__).resolve().parent.parent.parent / "ui-ux" / "frontend"
STATIC_DIR = DIST_DIR if DIST_DIR.exists() else LEGACY_DIR
if STATIC_DIR.exists():
    app.mount("/ui", StaticFiles(directory=str(STATIC_DIR), html=True), name="ui")


@app.get("/", include_in_schema=False)
async def root_redirect() -> RedirectResponse:
    """Redirect root to UI landing page."""
    return RedirectResponse(url="/ui/")


@app.get("/healthz", tags=["System"])
async def health_check() -> dict[str, str]:
    """Basic health check endpoint."""
    return {"status": "ok", "app": settings.APP_NAME}
