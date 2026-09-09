import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile, status

from fiosra.mvp.courses.ingestion import syllabus_parser
from fiosra.mvp.courses.schemas import (
    CohortRosterResponse,
    CourseCreate,
    CourseResponse,
    ModuleCreate,
    ModuleResponse,
    ResourceCreateRequest,
    SyllabusChunkResponse,
    SyllabusIngestRequest,
)
from fiosra.mvp.courses.service import course_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/courses", tags=["Courses & Modules Grounding"])



@router.post("", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
async def create_course(payload: CourseCreate) -> CourseResponse:
    """
    Creates a new institutional course workspace and optionally parses and vectors
    the introductory syllabus context into pgvector.
    """
    try:
        return await course_service.create_course(payload)
    except Exception as e:
        logger.exception("Error creating course")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create course: {e!s}",
        ) from e


@router.get("", response_model=list[CourseResponse])
async def list_courses() -> list[CourseResponse]:
    """
    Lists all course workspaces along with module counts and nested metadata.
    """
    try:
        return await course_service.list_courses()
    except Exception as e:
        logger.exception("Error listing courses")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list courses: {e!s}",
        ) from e


@router.get("/{course_id}", response_model=CourseResponse)
async def get_course(course_id: UUID) -> CourseResponse:
    """
    Fetches full course details including nested sequential curriculum modules and assignments.
    """
    course = await course_service.get_course(course_id)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with ID '{course_id}' not found.",
        )
    return course


@router.post("/{course_id}/modules", response_model=ModuleResponse, status_code=status.HTTP_201_CREATED)
async def add_module(course_id: UUID, payload: ModuleCreate) -> ModuleResponse:
    """
    Adds a sequential curriculum module with learning objectives to a course sequencer.
    """
    try:
        return await course_service.add_module(course_id, payload)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve)) from ve
    except Exception as e:
        logger.exception("Error adding module")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create module: {e!s}",
        ) from e


@router.get("/{course_id}/modules/{module_id}", response_model=ModuleResponse)
async def get_module(course_id: UUID, module_id: UUID) -> ModuleResponse:
    """
    Fetches module details, learning objectives, lock status, and active assignments.
    """
    module = await course_service.get_module(course_id, module_id)
    if not module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Module '{module_id}' not found in course '{course_id}'.",
        )
    return module


@router.post("/{course_id}/syllabus", response_model=list[SyllabusChunkResponse])
async def ingest_syllabus(course_id: UUID, payload: SyllabusIngestRequest) -> list[SyllabusChunkResponse]:
    """
    Ingests syllabus reading corpus, segments into semantic chunks, generates 1536-dim
    embeddings, links Neo4j Knowledge Components, and saves to pgvector.
    """
    course = await course_service.get_course(course_id)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with ID '{course_id}' not found.",
        )

    try:
        return await syllabus_parser.ingest_syllabus(
            course_id=course_id,
            content=payload.content,
            title=payload.title or "Syllabus",
            module_id=payload.module_id,
            domain=course.domain,
        )
    except Exception as e:
        logger.exception("Error ingesting syllabus")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest syllabus: {e!s}",
        ) from e


@router.get("/{course_id}/syllabus", response_model=list[SyllabusChunkResponse])
async def list_course_syllabus(
    course_id: UUID,
    module_id: Annotated[UUID | None, Query()] = None,
) -> list[SyllabusChunkResponse]:
    """
    Lists all ingested syllabus reading resources and primary sources for a course,
    optionally filtered by module_id.
    """
    course = await course_service.get_course(course_id)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with ID '{course_id}' not found.",
        )
    return await syllabus_parser.list_chunks(course_id=course_id, module_id=module_id)


@router.post(
    "/{course_id}/modules/{module_id}/resources",
    response_model=list[SyllabusChunkResponse],
    status_code=status.HTTP_201_CREATED,
)
async def add_module_resource(
    course_id: UUID,
    module_id: UUID,
    payload: ResourceCreateRequest,
) -> list[SyllabusChunkResponse]:
    """
    Adds text, markdown excerpts, or external link reading material directly attached
    to a specific course module. Embeds into pgvector and grounds to Neo4j KCs.
    """
    course = await course_service.get_course(course_id)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with ID '{course_id}' not found.",
        )
    module = await course_service.get_module(course_id, module_id)
    if not module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Module '{module_id}' not found in course '{course_id}'.",
        )

    try:
        return await syllabus_parser.ingest_syllabus(
            course_id=course_id,
            content=payload.content,
            title=payload.title,
            module_id=module_id,
            domain=course.domain,
            resource_type=payload.resource_type,
            source_url=payload.source_url,
        )
    except Exception as e:
        logger.exception("Error ingesting module resource")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add module resource: {e!s}",
        ) from e


@router.post(
    "/{course_id}/modules/{module_id}/resources/upload",
    response_model=list[SyllabusChunkResponse],
    status_code=status.HTTP_201_CREATED,
)
async def upload_module_resource_file(
    course_id: UUID,
    module_id: UUID,
    file: Annotated[UploadFile, File(...)],
    title: Annotated[str | None, Form()] = None,
) -> list[SyllabusChunkResponse]:
    """
    Uploads a PDF, Markdown, or text document for a module.
    Extracts text using pypdf / UTF-8 decode, generates vector embeddings, and stores in pgvector.
    """
    course = await course_service.get_course(course_id)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with ID '{course_id}' not found.",
        )
    module = await course_service.get_module(course_id, module_id)
    if not module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Module '{module_id}' not found in course '{course_id}'.",
        )

    try:
        raw_bytes = await file.read()
        is_pdf = bool(file.filename and file.filename.lower().endswith(".pdf")) or (
            file.content_type == "application/pdf"
        )
        extracted_text = syllabus_parser.extract_text(raw_bytes, is_pdf=is_pdf)
        if not extracted_text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No readable text could be extracted from uploaded file.",
            )

        doc_title = title or file.filename or "Uploaded Resource"
        resource_type = "pdf" if is_pdf else "document"

        return await syllabus_parser.ingest_syllabus(
            course_id=course_id,
            content=extracted_text,
            title=doc_title,
            module_id=module_id,
            domain=course.domain,
            resource_type=resource_type,
            source_url=None,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error uploading module resource file")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process uploaded file: {e!s}",
        ) from e


@router.delete("/{course_id}/resources/{chunk_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resource_chunk(course_id: UUID, chunk_id: UUID) -> None:
    """
    Deletes an attached reading or primary source chunk from pgvector.
    """
    course = await course_service.get_course(course_id)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with ID '{course_id}' not found.",
        )
    deleted = await syllabus_parser.delete_chunk(chunk_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resource chunk '{chunk_id}' not found.",
        )


@router.get("/{course_id}/syllabus/search", response_model=list[SyllabusChunkResponse])

async def search_syllabus(
    course_id: UUID,
    query: Annotated[str, Query(min_length=2, description="Semantic search query")],
    top_k: Annotated[int, Query(ge=1, le=20)] = 5,
    module_id: Annotated[UUID | None, Query()] = None,
) -> list[SyllabusChunkResponse]:
    """
    Performs cosine vector similarity search over syllabus corpus chunks using pgvector.
    """
    course = await course_service.get_course(course_id)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with ID '{course_id}' not found.",
        )

    return await syllabus_parser.search_syllabus(
        course_id=course_id,
        query=query,
        top_k=top_k,
        module_id=module_id,
    )


@router.get("/{course_id}/roster", response_model=CohortRosterResponse)
async def get_cohort_roster(course_id: UUID) -> CohortRosterResponse:
    """
    Returns the enrolled cohort roster with aggregate Autonomy Scores (A_s),
    hint consumption telemetry, and active struggle alerts.
    """
    try:
        return await course_service.get_cohort_roster(course_id)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve)) from ve
    except Exception as e:
        logger.exception("Error generating cohort roster")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate cohort roster: {e!s}",
        ) from e
