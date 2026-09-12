"""Canvas Scribe Helper Agent.

Autonomous document assistant service that executes canvas modifications
delegated by the Socratic Agent (e.g. section scaffolding, claim insertion).
Outputs strictly sanitized blocks conforming to ProseMirror and Fiosra schemas.
"""

import uuid
from typing import Any
from uuid import UUID

from fiosra.mvp.socratic_probe_schemas import HelperCanvasAction


class CanvasScribeHelper:
    """Headless document scribe that formats and stages student-articulated content."""

    @staticmethod
    def generate_section_blocks(
        session_id: UUID | str,
        section_titles: list[str],
        target_page: int = 1,
    ) -> HelperCanvasAction:
        """Create H2 section headings and placeholder guidance for student-proposed structure."""
        blocks: list[dict[str, Any]] = []
        cleaned_titles = [t.strip() for t in section_titles if t.strip()]
        if not cleaned_titles:
            cleaned_titles = ["Introduction & Working Claim", "Context & Evidence", "Analysis & Conclusion"]

        page_sec_id = f"page_{target_page}"

        for idx, title in enumerate(cleaned_titles):
            heading_id = uuid.uuid4()
            blocks.append({
                "block_id": str(heading_id),
                "block_type": "heading",
                "section_id": page_sec_id,
                "author_type": "student",
                "content": {
                    "type": "heading",
                    "attrs": {
                        "level": 2,
                        "blockId": str(heading_id),
                        "authorType": "student",
                        "sectionId": page_sec_id,
                        "pageNumber": target_page,
                    },
                    "content": [{"type": "text", "text": title}],
                },
            })

            para_id = uuid.uuid4()
            blocks.append({
                "block_id": str(para_id),
                "block_type": "paragraph",
                "section_id": page_sec_id,
                "author_type": "student",
                "content": {
                    "type": "paragraph",
                    "attrs": {
                        "blockId": str(para_id),
                        "authorType": "student",
                        "sectionId": page_sec_id,
                        "pageNumber": target_page,
                    },
                    "content": [
                        {
                            "type": "text",
                            "text": f"Articulate your core reasoning and evidence for {title.lower()}...",
                        }
                    ],
                },
            })

        summary = f"Created {len(cleaned_titles)} sections on Page {target_page}."
        return HelperCanvasAction(
            action="scaffold_sections",
            summary=summary,
            target_page=target_page,
            target_section=cleaned_titles[0] if cleaned_titles else None,
            blocks=blocks,
        )

    @staticmethod
    def generate_claim_block(
        session_id: UUID | str,
        validated_claim_text: str,
        target_section: str | None = None,
        target_page: int = 1,
    ) -> HelperCanvasAction:
        """Format a student-substantiated claim into a synthesized paragraph block."""
        claim_id = uuid.uuid4()
        clean_text = validated_claim_text.strip()
        page_sec_id = f"page_{target_page}"

        block = {
            "block_id": str(claim_id),
            "block_type": "paragraph",
            "section_id": page_sec_id,
            "author_type": "student",
            "content": {
                "type": "paragraph",
                "attrs": {
                    "blockId": str(claim_id),
                    "authorType": "student",
                    "sectionId": page_sec_id,
                    "pageNumber": target_page,
                },
                "content": [{"type": "text", "text": clean_text}],
            },
        }

        sec_label = target_section or "Target Section"
        summary = f"Appended verified claim into '{sec_label}'."
        return HelperCanvasAction(
            action="insert_claim",
            summary=summary,
            target_page=target_page,
            target_section=target_section,
            blocks=[block],
        )


canvas_scribe_helper = CanvasScribeHelper()
