import json
import logging
import re
from typing import Any
from uuid import UUID

from sqlalchemy import text

from fiosra.mvp.authoring.schemas import (
    AssignmentDraftRequest,
    AssignmentDraftRevisionRequest,
    AssignmentDraftRevisionResponse,
    AssignmentDraftSpec,
    CognitiveTrapSpec,
    CourseDraftRequest,
    CourseDraftRevisionRequest,
    CourseDraftRevisionResponse,
    CourseDraftSpec,
    DraftAssignmentMilestoneSpec,
    DraftModuleSpec,
    HintRungSpec,
    PublishAssignmentDraftRequest,
    PublishCourseDraftRequest,
)
from fiosra.mvp.config import settings
from fiosra.mvp.courses.ingestion import syllabus_parser
from fiosra.mvp.courses.schemas import CourseResponse
from fiosra.mvp.courses.service import course_service
from fiosra.mvp.database import AsyncSessionLocal
from fiosra.mvp.llm.contracts import CompletionRequest
from fiosra.mvp.llm.litellm_provider import LiteLLMProvider

logger = logging.getLogger(__name__)


def _extract_json_block(text_response: str) -> dict[str, Any] | None:
    """Extracts and parses JSON from markdown code fences or raw text."""
    if not text_response:
        return None
    # Try direct parse
    try:
        return json.loads(text_response.strip())
    except json.JSONDecodeError:
        pass

    # Try fenced json
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text_response, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # Try outermost braces
    start = text_response.find("{")
    end = text_response.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text_response[start : end + 1])
        except json.JSONDecodeError:
            pass
    return None


class CourseAuthoringService:
    """
    AI Co-Pilot service for curriculum ingestion, structured course blueprint synthesis,
    multi-turn iterative educator review loops, and one-click publishing.
    """

    @classmethod
    async def generate_course_draft(cls, req: CourseDraftRequest) -> CourseDraftSpec:
        """
        Synthesizes a structured CourseDraftSpec from raw syllabus text, lecture notes, or readings.
        """
        system_prompt = (
            "You are an expert university curriculum designer and pedagogical architect. "
            "Analyze the provided course materials and output a rigorous, well-sequenced university course draft. "
            "Respond ONLY with a valid JSON object strictly matching this schema:\n"
            "{\n"
            '  "title": "Course Title",\n'
            '  "domain": "Discipline/Domain",\n'
            '  "overview": "Comprehensive syllabus overview and course rationale",\n'
            '  "target_audience": "Undergraduate",\n'
            '  "modules": [\n'
            "    {\n"
            '      "title": "Module Title",\n'
            '      "description": "Pedagogical focus and historical/scientific scope",\n'
            '      "learning_objectives": ["Objective 1 using Bloom\'s verbs", "Objective 2"],\n'
            '      "position": 1,\n'
            '      "knowledge_components": ["KC_DOMAIN_TOPIC1", "KC_DOMAIN_TOPIC2"],\n'
            '      "suggested_assignments": [\n'
            "        {\n"
            '          "title": "Milestone Task Title",\n'
            '          "description": "Task brief and inquiry question",\n'
            '          "primary_sources": ["Primary text 1", "Evidence document 2"]\n'
            "        }\n"
            "      ],\n"
            '      "change_status": "unchanged"\n'
            "    }\n"
            "  ]\n"
            "}"
        )

        user_prompt = (
            f"Course Materials / Syllabus Content:\n"
            f"---\n{req.materials_text}\n---\n"
            f"Domain: {req.domain}\n"
            f"Title Hint: {req.title_hint or 'Derive optimal title from materials'}\n\n"
            f"Synthesize 3 to 6 cohesive modules that scaffold student reasoning progressively."
        )

        if settings.FIOSRA_LLM_PROVIDER.strip().lower() != "deterministic":
            provider = LiteLLMProvider.from_settings()
            comp_req = CompletionRequest(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                purpose="course_draft_synthesis",
                max_tokens=2500,
                temperature=0.3,
            )
            result = await provider.complete(comp_req)
            parsed = _extract_json_block(result.content)
            if not parsed or "title" not in parsed or "modules" not in parsed:
                raise RuntimeError(
                    f"LLM did not return a valid course draft JSON. Provider output: {result.content[:300]}"
                )
            return CourseDraftSpec.model_validate(parsed)

        # High quality deterministic synthesis fallback
        lines = [line.strip() for line in req.materials_text.splitlines() if line.strip()]
        title = req.title_hint or (lines[0] if lines else f"{req.domain} Foundations")
        if len(title) > 100:
            title = title[:97] + "..."

        modules: list[DraftModuleSpec] = [
            DraftModuleSpec(
                title=f"Unit 1: Foundations of {req.domain}",
                description="Introduction to core concepts, historiographical / methodological framing, and initial evidence analysis.",
                learning_objectives=[
                    f"Identify core foundational frameworks in {req.domain}",
                    "Critically evaluate primary source evidence and context",
                ],
                position=1,
                knowledge_components=[f"KC_{req.domain.upper()}_FOUNDATIONS", f"KC_{req.domain.upper()}_SOURCES"],
                suggested_assignments=[
                    DraftAssignmentMilestoneSpec(
                        title=f"{req.domain} Methodological Inquiry",
                        description="Analyze foundational documents and construct an evidentiary claim.",
                        primary_sources=["Foundational Source Excerpt", "Methodological Overview"],
                    )
                ],
                change_status="unchanged",
            ),
            DraftModuleSpec(
                title=f"Unit 2: Structural Dynamics & Critical Inquiries",
                description="Deep dive into causal mechanisms, competing perspectives, and secondary literature debate.",
                learning_objectives=[
                    "Examine causal interactions and institutional pressures",
                    "Synthesize competing interpretations from primary evidence",
                ],
                position=2,
                knowledge_components=[f"KC_{req.domain.upper()}_DYNAMICS", f"KC_{req.domain.upper()}_CAUSALITY"],
                suggested_assignments=[
                    DraftAssignmentMilestoneSpec(
                        title="Evidentiary Synthesis & Thesis Formulation",
                        description="Examine structural constraints and resolve contradictory historical accounts.",
                        primary_sources=["Comparative Case Accounts", "Statistical Summary"],
                    )
                ],
                change_status="unchanged",
            ),
            DraftModuleSpec(
                title=f"Unit 3: Synthesis, Historiography & Modern Implications",
                description="Culminating synthesis applying learned knowledge components to broader academic and contemporary debates.",
                learning_objectives=[
                    "Construct rigorous, source-grounded academic arguments",
                    "Defend claims against counter-arguments and cognitive traps",
                ],
                position=3,
                knowledge_components=[f"KC_{req.domain.upper()}_SYNTHESIS", f"KC_{req.domain.upper()}_EVALUATION"],
                suggested_assignments=[
                    DraftAssignmentMilestoneSpec(
                        title="Culminating Reasoning Portfolio",
                        description="Final long-form synthesis essay defended through Socratic reasoning probes.",
                        primary_sources=["Archive Compendium", "Contemporary Debate Transcripts"],
                    )
                ],
                change_status="unchanged",
            ),
        ]

        return CourseDraftSpec(
            title=title,
            domain=req.domain,
            overview=f"Comprehensive {req.domain} course synthesized from educator materials, designed for Socratic student inquiry and autonomous reasoning development.",
            target_audience="Undergraduate",
            modules=modules,
        )

    @classmethod
    async def revise_course_draft(cls, req: CourseDraftRevisionRequest) -> CourseDraftRevisionResponse:
        """
        Applies educator critique/review comments to the current course draft in a multi-turn refinement loop.
        """
        system_prompt = (
            "You are a pedagogical course builder assistant collaborating with a university educator.\n"
            "The educator is providing review comments, critiques, additions, questions, or conversational messages.\n"
            "Guidelines:\n"
            "1. If the educator requests changes (e.g. adding/modifying/removing modules, updating learning objectives, scope, sources):\n"
            "   Update the course draft accordingly. Set change_status to 'modified' for updated modules, 'added' for new modules, and 'unchanged' for untouched modules.\n"
            "2. If the educator sends a greeting (e.g. 'hi', 'hello') or asks an exploratory question without requesting draft modifications:\n"
            "   Keep the course draft intact in 'revised_draft' (with change_status='unchanged'), and respond warmly and helpfully in 'changes_summary' explaining what you can help them refine or build.\n"
            "Respond ONLY with a JSON object strictly matching:\n"
            "{\n"
            '  "revised_draft": { ...CourseDraftSpec... },\n'
            '  "changes_summary": "Your explanation of changes or conversational response to the educator."\n'
            "}"
        )

        user_prompt = (
            f"Current Course Draft:\n{json.dumps(req.current_draft.model_dump(), indent=2)}\n\n"
            f"Educator Input / Instructions:\n{req.review_comments}\n"
        )
        if req.target_module_index is not None:
            user_prompt += f"Target Focused Module Index: {req.target_module_index}\n"

        if settings.FIOSRA_LLM_PROVIDER.strip().lower() != "deterministic":
            provider = LiteLLMProvider.from_settings()
            comp_req = CompletionRequest(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                purpose="course_draft_revision",
                temperature=0.3,
                max_tokens=2500,
            )
            result = await provider.complete(comp_req)
            parsed = _extract_json_block(result.content)
            if parsed and "revised_draft" in parsed:
                revised = CourseDraftSpec.model_validate(parsed["revised_draft"])
                summary = parsed.get("changes_summary", "Updated course draft according to review comments.")
                return CourseDraftRevisionResponse(
                    revised_draft=revised,
                    changes_summary=summary,
                    revision_count=len(req.conversation_history) + 1,
                )
            elif parsed and "changes_summary" in parsed:
                return CourseDraftRevisionResponse(
                    revised_draft=req.current_draft,
                    changes_summary=parsed["changes_summary"],
                    revision_count=len(req.conversation_history) + 1,
                )
            elif result.content.strip():
                return CourseDraftRevisionResponse(
                    revised_draft=req.current_draft,
                    changes_summary=result.content.strip(),
                    revision_count=len(req.conversation_history) + 1,
                )
            else:
                raise RuntimeError("LLM returned empty revision response.")

        # Deterministic revision handling
        revised = req.current_draft.model_copy(deep=True)
        comment_lower = req.review_comments.lower()

        # Handle adding a module
        if "add module" in comment_lower or "new module" in comment_lower:
            new_pos = len(revised.modules) + 1
            mod_title = req.review_comments.split(":")[-1].strip() if ":" in req.review_comments else f"Module {new_pos}: Advanced Topics in {revised.domain}"
            revised.modules.append(
                DraftModuleSpec(
                    title=mod_title,
                    description=f"Specialized exploration addressing educator feedback: {req.review_comments}",
                    learning_objectives=[f"Analyze targeted topics in {revised.domain}", "Synthesize primary evidence"],
                    position=new_pos,
                    knowledge_components=[f"KC_{revised.domain.upper()}_EXT_{new_pos}"],
                    suggested_assignments=[
                        DraftAssignmentMilestoneSpec(
                            title=f"{mod_title} Milestone",
                            description="Inquiry assessment based on educator curriculum additions.",
                            primary_sources=["Curriculum Extension Readings"],
                        )
                    ],
                    change_status="added",
                )
            )
            summary = f"Added new module '{mod_title}' at position {new_pos} to reflect educator instructions."
        elif req.target_module_index is not None and 0 <= req.target_module_index < len(revised.modules):
            tgt = revised.modules[req.target_module_index]
            tgt.description = f"{tgt.description} [Refined: {req.review_comments}]"
            tgt.learning_objectives.append(f"Demonstrate competency in {req.review_comments[:40]}")
            tgt.change_status = "modified"
            summary = f"Updated module '{tgt.title}' with refined objectives and scope."
        else:
            # Mark first module as modified with note
            if revised.modules:
                revised.modules[0].description = f"{revised.modules[0].description} (Revised with educator feedback)"
                revised.modules[0].change_status = "modified"
            summary = f"Applied educator revision: '{req.review_comments}' across the course blueprint."

        return CourseDraftRevisionResponse(
            revised_draft=revised,
            changes_summary=summary,
            revision_count=len(req.conversation_history) + 1,
        )

    @classmethod
    async def publish_course_draft(cls, req: PublishCourseDraftRequest) -> CourseResponse:
        """
        Atomically publishes the approved course draft into the database (courses, modules, assignments)
        and indexes the curriculum content into pgvector.
        """
        draft = req.draft
        async with AsyncSessionLocal() as session:
            # 1. Insert course
            insert_course_sql = text("""
                INSERT INTO courses (title, domain, created_by, syllabus_context, created_at)
                VALUES (:title, :domain, :created_by, :syllabus_context, NOW())
                RETURNING course_id, title, domain, created_by, syllabus_context, created_at;
            """)
            c_res = await session.execute(
                insert_course_sql,
                {
                    "title": draft.title,
                    "domain": draft.domain,
                    "created_by": req.author_id,
                    "syllabus_context": draft.overview,
                },
            )
            course_row = c_res.mappings().first()
            if not course_row:
                raise RuntimeError("Failed to publish course.")
            course_id = course_row["course_id"]

            # 2. Insert modules and assignments
            for mod in draft.modules:
                insert_mod_sql = text("""
                    INSERT INTO modules (course_id, title, description, learning_objectives, position)
                    VALUES (:course_id, :title, :description, :learning_objectives, :position)
                    RETURNING module_id;
                """)
                m_res = await session.execute(
                    insert_mod_sql,
                    {
                        "course_id": course_id,
                        "title": mod.title,
                        "description": mod.description,
                        "learning_objectives": json.dumps(mod.learning_objectives),
                        "position": mod.position,
                    },
                )
                mod_row = m_res.mappings().first()
                if mod_row and mod.suggested_assignments:
                    module_id = mod_row["module_id"]
                    for assign in mod.suggested_assignments:
                        assign_spec = {
                            "status": "published",
                            "topic": assign.title,
                            "domain": draft.domain,
                            "task_brief": assign.description,
                            "allowed_sources": assign.primary_sources,
                            "learning_objectives": mod.learning_objectives,
                        }
                        insert_assign_sql = text("""
                            INSERT INTO assignments (module_id, title, spec, created_by, created_at)
                            VALUES (:module_id, :title, :spec, :created_by, NOW());
                        """)
                        await session.execute(
                            insert_assign_sql,
                            {
                                "module_id": module_id,
                                "title": assign.title,
                                "spec": json.dumps(assign_spec),
                                "created_by": req.author_id,
                            },
                        )

            await session.commit()

        # Ingest course syllabus into pgvector
        try:
            full_syllabus_text = f"# {draft.title}\n\n{draft.overview}\n\n"
            for m in draft.modules:
                full_syllabus_text += f"## {m.title}\n{m.description}\nObjectives: {', '.join(m.learning_objectives)}\n\n"

            await syllabus_parser.ingest_syllabus(
                course_id=course_id,
                content=full_syllabus_text,
                title=f"{draft.title} - Complete Curriculum",
                domain=draft.domain,
            )
        except Exception as e:
            logger.warning(f"Syllabus vectorization during publish encountered warning: {e}")

        course_response = await course_service.get_course(course_id)
        if not course_response:
            raise RuntimeError("Course created but could not be loaded.")
        return course_response


class AssignmentAuthoringService:
    """
    AI Co-Pilot service for synthesizing, tuning, and publishing Socratic assignments.
    """

    @classmethod
    async def generate_assignment_draft(cls, req: AssignmentDraftRequest) -> AssignmentDraftSpec:
        """
        Synthesizes an AssignmentDraftSpec including 3-Rung Hint Ladder and Cognitive Traps.
        """
        context_text = f"Assignment Topic: {req.task_topic}\nDomain: {req.domain}\n"
        if req.course_id:
            try:
                course = await course_service.get_course(req.course_id)
                if course:
                    context_text += f"Course: {course.title}\nCourse Overview: {course.syllabus_context or ''}\n"
            except Exception:
                pass

        system_prompt = (
            "You are an expert Socratic assignment designer and learning sciences specialist. "
            "Design an inquiry-based assignment with a rigorous 3-Rung Socratic Hint Ladder: "
            "Rung 1: Orienting Question (broad conceptual steer), "
            "Rung 2: Source-bounded directional cue (directing student to specific evidence), "
            "Rung 3: Structural scaffold (step-by-step reasoning breakdown without giving the answer). "
            "Also define potential cognitive traps/misconceptions and AutoSCORE rubric criteria. "
            "Respond ONLY with a JSON object strictly matching:\n"
            "{\n"
            '  "title": "Assignment Title",\n'
            '  "domain": "Domain",\n'
            '  "task_brief": "Detailed student prompt and challenge",\n'
            '  "context_scope": "Historical / disciplinary bounds",\n'
            '  "learning_objectives": ["Objective 1", "Objective 2"],\n'
            '  "allowed_sources": ["Source 1", "Source 2"],\n'
            '  "hint_ladder": [\n'
            '    {"rung": 1, "title": "Orienting Question", "content": "..."},\n'
            '    {"rung": 2, "title": "Source Evidence Cue", "content": "..."},\n'
            '    {"rung": 3, "title": "Structural Scaffold", "content": "..."}\n'
            "  ],\n"
            '  "cognitive_traps": [\n'
            '    {"trap_id": "TRAP_1", "name": "Trap Name", "description": "...", "remediation_hint": "..."}\n'
            "  ],\n"
            '  "rubric_criteria": ["Criterion 1", "Criterion 2"]\n'
            "}"
        )

        if settings.FIOSRA_LLM_PROVIDER.strip().lower() != "deterministic":
            provider = LiteLLMProvider.from_settings()
            comp_req = CompletionRequest(
                system_prompt=system_prompt,
                user_prompt=context_text,
                purpose="assignment_draft_synthesis",
                temperature=0.3,
                max_tokens=2000,
            )
            result = await provider.complete(comp_req)
            parsed = _extract_json_block(result.content)
            if not parsed or "title" not in parsed or "hint_ladder" not in parsed:
                raise RuntimeError(
                    f"LLM did not return a valid assignment draft JSON. Provider output: {result.content[:300]}"
                )
            return AssignmentDraftSpec.model_validate(parsed)

        # Deterministic fallback
        return AssignmentDraftSpec(
            title=f"Inquiry Analysis: {req.task_topic[:60]}",
            domain=req.domain,
            task_brief=f"Examine the core historical/disciplinary dynamics of {req.task_topic}. Synthesize primary evidence into a defensible thesis while addressing counter-arguments.",
            context_scope=f"Focused pedagogical scope concerning {req.task_topic}.",
            learning_objectives=[
                f"Evaluate evidentiary claims regarding {req.task_topic}",
                "Construct a structured academic argument defended against cognitive traps",
                "Demonstrate autonomous reasoning without over-reliance on explicit hints",
            ],
            allowed_sources=[
                f"Primary Account on {req.task_topic}",
                "Archival Document Series A",
                "Secondary Historiographical Essay",
            ],
            hint_ladder=[
                HintRungSpec(
                    rung=1,
                    title="Orienting Question",
                    content=f"What primary factors or institutional conditions initially framed {req.task_topic}?",
                ),
                HintRungSpec(
                    rung=2,
                    title="Source Evidence Cue",
                    content="Consult the primary account excerpt—how does the author explain the immediate fiscal or institutional pressures?",
                ),
                HintRungSpec(
                    rung=3,
                    title="Structural Scaffold",
                    content="Break your argument into three parts: (1) Immediate triggers, (2) Structural institutional factors, and (3) Long-term consequences. Ground each in a cited source.",
                ),
            ],
            cognitive_traps=[
                CognitiveTrapSpec(
                    trap_id="TRAP_SINGLE_CAUSE",
                    name="Monocausal Fallacy",
                    description="Attributing a complex event to a single isolated cause while ignoring structural context.",
                    remediation_hint="Notice how multiple economic and social pressures intersected—what other dimensions contributed?",
                ),
                CognitiveTrapSpec(
                    trap_id="TRAP_ANACHRONISM",
                    name="Anachronistic Judgment",
                    description="Judging historical actors through contemporary modern values rather than contemporary constraints.",
                    remediation_hint="Consider the institutional constraints and available information in the specific historical era.",
                ),
            ],
            rubric_criteria=[
                "Evidence Grounding: Cites verified allowed sources accurately",
                "Cognitive Autonomy: Develops reasoning independently without trap collapse",
                "Thesis Defense: Addresses counter-arguments and structural causality",
            ],
        )

    @classmethod
    async def revise_assignment_draft(cls, req: AssignmentDraftRevisionRequest) -> AssignmentDraftRevisionResponse:
        """
        Refines assignment hints, scope, traps, or rubric based on educator review feedback.
        """
        system_prompt = (
            "You are a pedagogical assistant refining an assignment draft for a university educator.\n"
            "Update the assignment specification according to the educator's review comments or handle conversational inquiries.\n"
            "If the educator provides a greeting or question without requesting draft modifications, keep the draft intact and respond warmly in 'changes_summary'.\n"
            "Respond ONLY with a JSON object strictly matching:\n"
            "{\n"
            '  "revised_draft": { ...AssignmentDraftSpec... },\n'
            '  "changes_summary": "Explanation of changes made or conversational response."\n'
            "}"
        )

        user_prompt = (
            f"Current Assignment Draft:\n{json.dumps(req.current_draft.model_dump(), indent=2)}\n\n"
            f"Educator Review Comments:\n{req.review_comments}\n"
        )

        if settings.FIOSRA_LLM_PROVIDER.strip().lower() != "deterministic":
            provider = LiteLLMProvider.from_settings()
            comp_req = CompletionRequest(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                purpose="assignment_draft_revision",
                temperature=0.3,
                max_tokens=2000,
            )
            result = await provider.complete(comp_req)
            parsed = _extract_json_block(result.content)
            if parsed and "revised_draft" in parsed:
                revised = AssignmentDraftSpec.model_validate(parsed["revised_draft"])
                summary = parsed.get("changes_summary", "Updated assignment spec according to review comments.")
                return AssignmentDraftRevisionResponse(
                    revised_draft=revised,
                    changes_summary=summary,
                )
            elif parsed and "changes_summary" in parsed:
                return AssignmentDraftRevisionResponse(
                    revised_draft=req.current_draft,
                    changes_summary=parsed["changes_summary"],
                )
            elif result.content.strip():
                return AssignmentDraftRevisionResponse(
                    revised_draft=req.current_draft,
                    changes_summary=result.content.strip(),
                )
            else:
                raise RuntimeError("LLM returned empty assignment revision response.")

        # Deterministic fallback
        revised = req.current_draft.model_copy(deep=True)
        if "hint" in req.review_comments.lower() and revised.hint_ladder:
            revised.hint_ladder[0].content = f"{revised.hint_ladder[0].content} (Refined: {req.review_comments})"
        else:
            revised.task_brief = f"{revised.task_brief}\n\n[Educator Note: {req.review_comments}]"

        return AssignmentDraftRevisionResponse(
            revised_draft=revised,
            changes_summary=f"Refined assignment based on feedback: '{req.review_comments}'",
        )

    @classmethod
    async def publish_assignment_draft(cls, req: PublishAssignmentDraftRequest) -> dict[str, Any]:
        """
        Publishes the assignment draft into the target course module.
        """
        spec = {
            "status": "published",
            "topic": req.draft.title,
            "domain": req.draft.domain,
            "task_brief": req.draft.task_brief,
            "context_scope": req.draft.context_scope,
            "learning_objectives": req.draft.learning_objectives,
            "allowed_sources": req.draft.allowed_sources,
            "hint_ladder": [h.model_dump() for h in req.draft.hint_ladder],
            "cognitive_traps": [t.model_dump() for t in req.draft.cognitive_traps],
            "rubric_criteria": req.draft.rubric_criteria,
            "created_by": req.author_id,
        }

        insert_sql = text("""
            INSERT INTO assignments (module_id, title, spec, created_by, created_at)
            VALUES (:module_id, :title, :spec, :created_by, NOW())
            RETURNING assignment_id, module_id, title, spec, created_at;
        """)

        async with AsyncSessionLocal() as session:
            res = await session.execute(
                insert_sql,
                {
                    "module_id": str(req.module_id),
                    "title": req.draft.title,
                    "spec": json.dumps(spec),
                    "created_by": req.author_id,
                },
            )
            row = res.mappings().first()
            if not row:
                raise RuntimeError("Failed to insert published assignment.")
            await session.commit()

        return {
            "assignment_id": str(row["assignment_id"]),
            "module_id": str(row["module_id"]),
            "course_id": str(req.course_id),
            "title": row["title"],
            "status": "published",
            "spec": spec,
        }


course_authoring_service = CourseAuthoringService()
assignment_authoring_service = AssignmentAuthoringService()
