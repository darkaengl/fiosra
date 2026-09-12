"""Capability-protected HTTP routes for proactive Socratic evidence questions."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Header, HTTPException, status

from fiosra.mvp.socratic_probe_schemas import (
    DialecticalTurnRequest,
    DialecticalTurnResponse,
    EpistemicClassifyRequest,
    EpistemicClassifyResponse,
    ProbeDispositionResponse,
    ProbeEvaluationRequest,
    ProbeEvaluationResponse,
    ProbeListResponse,
    SentenceInquireRequest,
    SentenceInquireResponse,
    SubmitProbeResponseRequest,
)
from fiosra.mvp.socratic_probe_service import (
    SocraticProbeAccessError,
    SocraticProbeConflictError,
    SocraticProbeValidationError,
    socratic_probe_service,
)

router = APIRouter(prefix="/learning-documents/sessions/{session_id}/probes", tags=["Proactive Socratic Probes"])
SessionToken = Annotated[str | None, Header(alias="X-Fiosra-Session-Token")]


def _raise_probe_error(error: Exception) -> None:
    if isinstance(error, SocraticProbeAccessError):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(error)) from error
    if isinstance(error, SocraticProbeConflictError):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
    if isinstance(error, SocraticProbeValidationError):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error)) from error
    raise error


@router.post("/evaluate", response_model=ProbeEvaluationResponse)
async def evaluate_proactive_probes(
    session_id: UUID,
    request: ProbeEvaluationRequest,
    session_token: SessionToken = None,
) -> ProbeEvaluationResponse:
    """Evaluate stable saved learner blocks and return only server-authorized questions."""
    try:
        return await socratic_probe_service.evaluate(session_id, session_token, request)
    except (SocraticProbeAccessError, SocraticProbeConflictError, SocraticProbeValidationError) as error:
        _raise_probe_error(error)


@router.get("", response_model=ProbeListResponse)
async def list_proactive_probes(
    session_id: UUID,
    session_token: SessionToken = None,
) -> ProbeListResponse:
    """Restore pending or deferred questions for one authorized learner session."""
    try:
        return await socratic_probe_service.list_probes(session_id, session_token)
    except (SocraticProbeAccessError, SocraticProbeConflictError, SocraticProbeValidationError) as error:
        _raise_probe_error(error)


@router.post("/{probe_id}/responses", response_model=ProbeDispositionResponse)
async def submit_proactive_probe_response(
    session_id: UUID,
    probe_id: UUID,
    request: SubmitProbeResponseRequest,
    session_token: SessionToken = None,
) -> ProbeDispositionResponse:
    """Store a learner-authored answer as evidence submitted for later human review."""
    try:
        return await socratic_probe_service.submit_response(session_id, session_token, probe_id, request)
    except (SocraticProbeAccessError, SocraticProbeConflictError, SocraticProbeValidationError) as error:
        _raise_probe_error(error)


@router.post("/{probe_id}/defer", response_model=ProbeDispositionResponse)
async def defer_proactive_probe(
    session_id: UUID,
    probe_id: UUID,
    session_token: SessionToken = None,
) -> ProbeDispositionResponse:
    """Record a transparent non-blocking question deferral."""
    try:
        return await socratic_probe_service.defer_probe(session_id, session_token, probe_id)
    except (SocraticProbeAccessError, SocraticProbeConflictError, SocraticProbeValidationError) as error:
        _raise_probe_error(error)


@router.post("/{probe_id}/dismiss", response_model=ProbeDispositionResponse)
async def dismiss_proactive_probe(
    session_id: UUID,
    probe_id: UUID,
    session_token: SessionToken = None,
) -> ProbeDispositionResponse:
    """Record an explicit question dismissal without assigning an automated penalty."""
    try:
        return await socratic_probe_service.dismiss_probe(session_id, session_token, probe_id)
    except (SocraticProbeAccessError, SocraticProbeConflictError, SocraticProbeValidationError) as error:
        _raise_probe_error(error)


@router.post("/epistemic-classify", response_model=EpistemicClassifyResponse)
async def classify_epistemic_structure(
    session_id: UUID,
    request: EpistemicClassifyRequest,
    session_token: SessionToken = None,
) -> EpistemicClassifyResponse:
    """Classify each sentence's epistemic role with LLM-backed evaluation and targeted Socratic probes."""
    try:
        return await socratic_probe_service.classify_sentences(session_id, session_token, request)
    except (SocraticProbeAccessError, SocraticProbeConflictError, SocraticProbeValidationError) as error:
        _raise_probe_error(error)


@router.post("/sentence-inquire", response_model=SentenceInquireResponse)
async def inquire_sentence_dialectics(
    session_id: UUID,
    request: SentenceInquireRequest,
    session_token: SessionToken = None,
) -> SentenceInquireResponse:
    """Execute an on-demand bespoke Socratic Agent inquiry examining an individual sentence."""
    try:
        return await socratic_probe_service.inquire_sentence(session_id, session_token, request)
    except (SocraticProbeAccessError, SocraticProbeConflictError, SocraticProbeValidationError) as error:
        _raise_probe_error(error)


@router.post("/dialectical-turn", response_model=DialecticalTurnResponse)
async def process_dialectical_turn(
    session_id: UUID,
    request: DialecticalTurnRequest,
    session_token: SessionToken = None,
) -> DialecticalTurnResponse:
    """Evaluate student reasoning in an active multi-turn dialectical exchange until satisfied."""
    try:
        return await socratic_probe_service.dialectical_turn(session_id, session_token, request)
    except (SocraticProbeAccessError, SocraticProbeConflictError, SocraticProbeValidationError) as error:
        _raise_probe_error(error)



