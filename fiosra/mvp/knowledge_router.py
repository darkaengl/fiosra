from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from fiosra.mvp.graph_service import graph_service
from fiosra.mvp.seed_pipeline import search_nearest_misconceptions

router = APIRouter(prefix="/knowledge", tags=["Knowledge Layer"])


class LearningFrontierRequest(BaseModel):
    mastered_kc_ids: list[str] = Field(default_factory=list, description="List of mastered KC IDs")
    domain: str | None = Field(default=None, description="Optional curriculum domain filter (e.g. history, language)")


class MisconceptionSearchRequest(BaseModel):
    query: str = Field(..., description="Student input text or reasoning step")
    limit: int = Field(default=3, ge=1, le=10, description="Max nearest traps to return")
    domain: str | None = Field(default=None, description="Optional domain filter")


class MisconceptionResponse(BaseModel):
    misconception_id: str
    kc_id: str
    domain: str
    name: str
    flawed_rule: str
    remediation_hint: str
    similarity: float


@router.get("/integrity")
async def check_knowledge_graph_integrity() -> dict[str, Any]:
    """Validates that the Knowledge Component DAG contains zero directed cycles."""
    is_acyclic = await graph_service.check_acyclicity()
    return {"is_acyclic": is_acyclic, "status": "healthy" if is_acyclic else "degraded"}


@router.get("/kcs/{kc_id}")
async def get_knowledge_component_details(kc_id: str) -> dict[str, Any]:
    """Fetches details for a specific Knowledge Component node."""
    kc = await graph_service.get_kc_details(kc_id)
    if not kc:
        raise HTTPException(status_code=404, detail=f"Knowledge Component '{kc_id}' not found")
    return kc


@router.get("/kcs/{kc_id}/prerequisites")
async def get_kc_prerequisites(
    kc_id: str,
    depth: int = Query(default=10, ge=1, le=20),
) -> dict[str, Any]:
    """Returns all transitive prerequisite KCs required before this concept."""
    prereqs = await graph_service.get_prerequisites(kc_id, depth=depth)
    return {"kc_id": kc_id, "prerequisites": prereqs, "count": len(prereqs)}


@router.post("/frontier")
async def get_curriculum_frontier(request: LearningFrontierRequest) -> list[dict[str, Any]]:
    """
    Returns the student's current learning frontier based on satisfied prerequisites.
    """
    return await graph_service.get_learning_frontier(
        mastered_kc_ids=request.mastered_kc_ids,
        domain=request.domain,
    )


@router.post("/misconceptions/search", response_model=list[MisconceptionResponse])
async def search_misconception_traps(request: MisconceptionSearchRequest) -> list[dict[str, Any]]:
    """
    Performs cosine vector search across indexed misconception traps in PostgreSQL.
    """
    return await search_nearest_misconceptions(
        query_text=request.query,
        limit=request.limit,
        domain=request.domain,
    )
