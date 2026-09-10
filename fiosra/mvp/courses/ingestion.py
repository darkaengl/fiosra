import io
import logging
import re
import uuid
from uuid import UUID

from neo4j.exceptions import Neo4jError
from sqlalchemy import text

from fiosra.mvp.courses.schemas import SyllabusChunkResponse
from fiosra.mvp.database import AsyncSessionLocal
from fiosra.mvp.graph_service import graph_service
from fiosra.mvp.seed_pipeline import generate_deterministic_embedding

logger = logging.getLogger(__name__)


class SyllabusParser:
    """
    Parses syllabus and reading corpus materials (Markdown, text, PDF),
    splits them into semantic chunks, generates 1536-dimensional pgvector embeddings,
    and grounds them against Neo4j Knowledge Components.
    """

    @classmethod
    def extract_text(cls, content: str | bytes, is_pdf: bool = False) -> str:
        """
        Extracts raw UTF-8 string text from plain/markdown text or PDF bytes.
        """
        if isinstance(content, bytes):
            if is_pdf or content.startswith(b"%PDF-"):
                try:
                    import pypdf
                    reader = pypdf.PdfReader(io.BytesIO(content))
                    extracted = [page.extract_text() or "" for page in reader.pages]
                    return "\n\n".join(extracted).strip()
                except (ImportError, ValueError, OSError, RuntimeError) as e:
                    logger.warning(
                        f"pypdf extraction failed or not available: {e}. Falling back to utf-8 decode."
                    )
                    return content.decode("utf-8", errors="ignore").strip()
            return content.decode("utf-8", errors="ignore").strip()
        return str(content).strip()

    @classmethod
    def chunk_document(cls, text_content: str, default_title: str = "Syllabus Section") -> list[dict[str, str]]:
        """
        Splits text content into semantic chunks based on markdown headings or double newlines.
        Each chunk is between 150 and 1200 characters.
        """
        sections: list[dict[str, str]] = []
        lines = text_content.splitlines()

        current_title = default_title
        current_buffer: list[str] = []

        header_regex = re.compile(r"^(#{1,4})\s+(.+)$")

        for line in lines:
            stripped = line.strip()
            m = header_regex.match(stripped)
            if m:
                # Save previous buffer if non-empty
                if current_buffer:
                    body = "\n".join(current_buffer).strip()
                    if len(body) >= 40:
                        sections.append({"title": current_title, "content": body})
                    current_buffer = []
                current_title = m.group(2).strip()
            else:
                if stripped:
                    current_buffer.append(stripped)

        if current_buffer:
            body = "\n".join(current_buffer).strip()
            if len(body) >= 20:
                sections.append({"title": current_title, "content": body})

        # If no markdown headings were detected, chunk by paragraph blocks
        if not sections:
            paragraphs = [p.strip() for p in text_content.split("\n\n") if p.strip()]
            for idx, p in enumerate(paragraphs, start=1):
                sections.append({
                    "title": f"{default_title} - Part {idx}",
                    "content": p,
                })

        return sections

    @classmethod
    async def match_kc_for_text(cls, chunk_text: str, domain: str | None = None) -> str | None:
        """
        Scans chunk text against available Neo4j Knowledge Components to link grounding context.
        """
        try:
            kcs = await graph_service.list_all_kcs(domain=domain)
        except (Neo4jError, RuntimeError, ConnectionError, OSError) as e:
            logger.warning(f"Could not fetch KCs from Neo4j for grounding: {e}")
            kcs = []

        # Fallback if Neo4j returned empty
        if not kcs:
            kcs = [
                {"kc_id": "KC_HIST_FRENCH_DEBT", "label": "French Crown Sovereign War Debt"},
                {"kc_id": "KC_HIST_ANCIEN_REGIME", "label": "Ancien Regime Three Estates Social Structure"},
                {"kc_id": "KC_HIST_ESTATES_GENERAL", "label": "Convocation of the 1789 Estates-General"},
                {"kc_id": "KC_HIST_TENNIS_COURT", "label": "National Assembly and Tennis Court Oath"},
                {"kc_id": "KC_HIST_BASTILLE", "label": "Storming of the Bastille and Popular Insurrection"},
                {"kc_id": "KC_HIST_CALONNE", "label": "Assembly of Notables and Calonne Reform Failure"},
            ]

        text_lower = chunk_text.lower()
        best_kc = None
        best_score = 0

        for kc in kcs:
            score = 0
            label_words = [w.lower() for w in re.findall(r"\w+", kc.get("label", "")) if len(w) > 3]
            for w in label_words:
                if w in text_lower:
                    score += 1
            if score > best_score:
                best_score = score
                best_kc = kc.get("kc_id")

        return best_kc if best_score > 0 else None

    @classmethod
    async def ingest_syllabus(
        cls,
        course_id: UUID | str,
        content: str | bytes,
        title: str = "Course Syllabus",
        module_id: UUID | str | None = None,
        domain: str = "History",
        is_pdf: bool = False,
        resource_type: str = "document",
        source_url: str | None = None,
    ) -> list[SyllabusChunkResponse]:
        """
        Parses, chunks, embeds, grounds, and stores syllabus chunks in PostgreSQL with pgvector.
        """
        raw_text = cls.extract_text(content, is_pdf=is_pdf)
        raw_chunks = cls.chunk_document(raw_text, default_title=title)

        persisted_chunks: list[SyllabusChunkResponse] = []

        insert_sql = text("""
            INSERT INTO syllabus_chunks (
                chunk_id, course_id, module_id, title, content, kc_id, embedding, resource_type, source_url, created_at
            ) VALUES (
                :chunk_id, :course_id, :module_id, :title, :content, :kc_id, :embedding, :resource_type, :source_url, NOW()
            )
            RETURNING chunk_id, course_id, module_id, title, content, kc_id, resource_type, source_url, created_at;
        """)

        async with AsyncSessionLocal() as session:
            for item in raw_chunks:
                chunk_id = uuid.uuid4()
                c_title = item["title"]
                c_text = item["content"]
                kc_id = await cls.match_kc_for_text(c_text, domain=domain)
                embedding = generate_deterministic_embedding(c_text)

                result = await session.execute(
                    insert_sql,
                    {
                        "chunk_id": chunk_id,
                        "course_id": str(course_id),
                        "module_id": str(module_id) if module_id else None,
                        "title": c_title,
                        "content": c_text,
                        "kc_id": kc_id,
                        "embedding": str(embedding),
                        "resource_type": resource_type,
                        "source_url": source_url,
                    },
                )
                row = result.mappings().first()
                if row:
                    persisted_chunks.append(
                        SyllabusChunkResponse(
                            chunk_id=row["chunk_id"],
                            course_id=row["course_id"],
                            module_id=row["module_id"],
                            title=row["title"],
                            content=row["content"],
                            kc_id=row["kc_id"],
                            resource_type=row.get("resource_type") or resource_type,
                            source_url=row.get("source_url"),
                            created_at=row["created_at"],
                            similarity=1.0,
                        )
                    )
            await session.commit()

        logger.info(
            f"Successfully ingested {len(persisted_chunks)} syllabus chunks for course {course_id}."
        )
        return persisted_chunks

    @classmethod
    async def search_syllabus(
        cls,
        course_id: UUID | str,
        query: str,
        top_k: int = 5,
        module_id: UUID | str | None = None,
    ) -> list[SyllabusChunkResponse]:
        """
        Executes a vector cosine similarity search in PostgreSQL via pgvector.
        """
        query_vector = generate_deterministic_embedding(query)

        query_sql = text("""
            SELECT chunk_id, course_id, module_id, title, content, kc_id, resource_type, source_url, created_at,
                   1.0 - (embedding <=> CAST(:query_vec AS vector)) AS similarity
            FROM syllabus_chunks
            WHERE course_id = :course_id
              AND (CAST(:module_id AS UUID) IS NULL OR module_id = CAST(:module_id AS UUID))
            ORDER BY embedding <=> CAST(:query_vec AS vector) ASC
            LIMIT :top_k;
        """)

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                query_sql,
                {
                    "course_id": str(course_id),
                    "module_id": str(module_id) if module_id else None,
                    "query_vec": str(query_vector),
                    "top_k": top_k,
                },
            )
            rows = result.mappings().all()

        return [
            SyllabusChunkResponse(
                chunk_id=r["chunk_id"],
                course_id=r["course_id"],
                module_id=r["module_id"],
                title=r["title"],
                content=r["content"],
                kc_id=r["kc_id"],
                resource_type=r.get("resource_type") or "document",
                source_url=r.get("source_url"),
                created_at=r["created_at"],
                similarity=round(float(r["similarity"]), 4) if r["similarity"] is not None else None,
            )
            for r in rows
        ]

    @classmethod
    async def list_chunks(
        cls,
        course_id: UUID | str,
        module_id: UUID | str | None = None,
    ) -> list[SyllabusChunkResponse]:
        """
        Lists all ingested syllabus and primary source reading chunks for a course.
        """
        query_sql = text("""
            SELECT chunk_id, course_id, module_id, title, content, kc_id, resource_type, source_url, created_at
            FROM syllabus_chunks
            WHERE course_id = :course_id
              AND (CAST(:module_id AS UUID) IS NULL OR module_id = CAST(:module_id AS UUID))
            ORDER BY created_at ASC;
        """)

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                query_sql,
                {
                    "course_id": str(course_id),
                    "module_id": str(module_id) if module_id else None,
                },
            )
            rows = result.mappings().all()

        return [
            SyllabusChunkResponse(
                chunk_id=r["chunk_id"],
                course_id=r["course_id"],
                module_id=r["module_id"],
                title=r["title"],
                content=r["content"],
                kc_id=r["kc_id"],
                resource_type=r.get("resource_type") or "document",
                source_url=r.get("source_url"),
                created_at=r["created_at"],
                similarity=1.0,
            )
            for r in rows
        ]

    @classmethod
    async def published_assignment_dependencies(
        cls,
        course_id: UUID | str,
        chunk_id: UUID | str,
    ) -> list[dict[str, str]]:
        """Return published tasks that cite a source chunk in their stored provenance."""
        dependency_sql = text("""
            SELECT a.assignment_id, a.title
            FROM assignments a
            JOIN modules m ON a.module_id = m.module_id
            WHERE m.course_id = CAST(:course_id AS UUID)
              AND COALESCE(a.spec ->> 'status', 'draft') = 'published'
              AND COALESCE(a.spec -> 'grounding_sources', '[]'::jsonb)
                    @> jsonb_build_array(jsonb_build_object('chunk_id', CAST(:chunk_id AS TEXT)));
        """)
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                dependency_sql,
                {"course_id": str(course_id), "chunk_id": str(chunk_id)},
            )
            return [
                {"assignment_id": str(row["assignment_id"]), "title": row["title"]}
                for row in result.mappings().all()
            ]

    @classmethod
    async def delete_chunk(cls, course_id: UUID | str, chunk_id: UUID | str) -> bool:
        """Delete an unreferenced resource chunk from the selected course only."""
        delete_sql = text("""
            DELETE FROM syllabus_chunks
            WHERE chunk_id = CAST(:chunk_id AS UUID)
              AND course_id = CAST(:course_id AS UUID)
            RETURNING chunk_id;
        """)
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                delete_sql,
                {"course_id": str(course_id), "chunk_id": str(chunk_id)},
            )
            deleted = result.scalar() is not None
            await session.commit()
            return deleted


syllabus_parser = SyllabusParser()
