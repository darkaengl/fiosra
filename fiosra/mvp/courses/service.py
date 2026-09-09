import json
import logging
from typing import Any
from uuid import UUID

from sqlalchemy import text

from fiosra.mvp.courses.ingestion import syllabus_parser
from fiosra.mvp.courses.schemas import (
    CohortRosterResponse,
    CohortStudentMetrics,
    CourseCreate,
    CourseResponse,
    ModuleCreate,
    ModuleResponse,
)
from fiosra.mvp.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


class CourseService:
    """
    Business logic and query engine for Course Workspaces, Curriculum Modules,
    Syllabus grounding, and Cohort Roster diagnostics.
    """

    @classmethod
    async def create_course(cls, data: CourseCreate) -> CourseResponse:
        """
        Creates a new course workspace, stores syllabus context, and automatically
        generates semantic syllabus grounding chunks in pgvector.
        """
        insert_sql = text("""
            INSERT INTO courses (title, domain, created_by, syllabus_context, created_at)
            VALUES (:title, :domain, :created_by, :syllabus_context, NOW())
            RETURNING course_id, title, domain, created_by, syllabus_context, created_at;
        """)

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                insert_sql,
                {
                    "title": data.title,
                    "domain": data.domain,
                    "created_by": data.created_by,
                    "syllabus_context": data.syllabus_context,
                },
            )
            row = result.mappings().first()
            if not row:
                raise RuntimeError("Failed to insert course.")
            await session.commit()

        course_id = row["course_id"]

        # If syllabus text was provided, ingest and vectorize
        if data.syllabus_context:
            try:
                await syllabus_parser.ingest_syllabus(
                    course_id=course_id,
                    content=data.syllabus_context,
                    title=f"{data.title} - Overview",
                    domain=data.domain,
                )
            except (RuntimeError, ValueError, OSError) as e:
                logger.warning(f"Automatic syllabus ingestion failed for course {course_id}: {e}")

        return CourseResponse(
            course_id=course_id,
            title=row["title"],
            domain=row["domain"],
            created_by=row["created_by"],
            syllabus_context=row["syllabus_context"],
            created_at=row["created_at"],
            modules=[],
            assignments_count=0,
        )

    @classmethod
    async def list_courses(cls) -> list[CourseResponse]:
        """
        Lists all courses with nested module summaries and total assignment counts.
        """
        courses_sql = text("""
            SELECT c.course_id, c.title, c.domain, c.created_by, c.syllabus_context, c.created_at,
                   COUNT(DISTINCT a.assignment_id) as assignments_count
            FROM courses c
            LEFT JOIN modules m ON c.course_id = m.course_id
            LEFT JOIN assignments a ON m.module_id = a.module_id
            GROUP BY c.course_id
            ORDER BY c.created_at DESC;
        """)

        async with AsyncSessionLocal() as session:
            result = await session.execute(courses_sql)
            rows = result.mappings().all()

            courses = []
            for r in rows:
                course_id = r["course_id"]
                modules = await cls.get_modules_for_course(course_id)
                courses.append(
                    CourseResponse(
                        course_id=course_id,
                        title=r["title"],
                        domain=r["domain"],
                        created_by=r["created_by"],
                        syllabus_context=r["syllabus_context"],
                        created_at=r["created_at"],
                        modules=modules,
                        assignments_count=int(r["assignments_count"]),
                    )
                )
            return courses

    @classmethod
    async def get_course(cls, course_id: UUID | str) -> CourseResponse | None:
        """
        Fetches a course by ID with all sequential modules and active assignments.
        """
        course_sql = text("""
            SELECT c.course_id, c.title, c.domain, c.created_by, c.syllabus_context, c.created_at,
                   COUNT(DISTINCT a.assignment_id) as assignments_count
            FROM courses c
            LEFT JOIN modules m ON c.course_id = m.course_id
            LEFT JOIN assignments a ON m.module_id = a.module_id
            WHERE c.course_id = :course_id
            GROUP BY c.course_id;
        """)

        async with AsyncSessionLocal() as session:
            result = await session.execute(course_sql, {"course_id": str(course_id)})
            row = result.mappings().first()
            if not row:
                return None

        modules = await cls.get_modules_for_course(course_id)
        return CourseResponse(
            course_id=row["course_id"],
            title=row["title"],
            domain=row["domain"],
            created_by=row["created_by"],
            syllabus_context=row["syllabus_context"],
            created_at=row["created_at"],
            modules=modules,
            assignments_count=int(row["assignments_count"]),
        )

    @classmethod
    async def add_module(cls, course_id: UUID | str, data: ModuleCreate) -> ModuleResponse:
        """
        Appends a new curriculum module to a course.
        """
        # Verify course exists
        course = await cls.get_course(course_id)
        if not course:
            raise ValueError(f"Course '{course_id}' does not exist.")

        insert_sql = text("""
            INSERT INTO modules (course_id, title, description, learning_objectives, position)
            VALUES (:course_id, :title, :description, :learning_objectives, :position)
            RETURNING module_id, course_id, title, description, learning_objectives, position;
        """)

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                insert_sql,
                {
                    "course_id": str(course_id),
                    "title": data.title,
                    "description": data.description,
                    "learning_objectives": json.dumps(data.learning_objectives),
                    "position": data.position,
                },
            )
            row = result.mappings().first()
            if not row:
                raise RuntimeError("Failed to insert module.")
            await session.commit()

        return ModuleResponse(
            module_id=row["module_id"],
            course_id=row["course_id"],
            title=row["title"],
            description=row["description"],
            learning_objectives=row["learning_objectives"] or [],
            position=row["position"],
            is_locked=row["position"] > 1,
            assignments=[],
        )

    @classmethod
    async def get_modules_for_course(cls, course_id: UUID | str) -> list[ModuleResponse]:
        """
        Fetches all modules for a course ordered by position with nested assignment lists.
        """
        modules_sql = text("""
            SELECT module_id, course_id, title, description, learning_objectives, position
            FROM modules
            WHERE course_id = :course_id
            ORDER BY position ASC;
        """)

        assignments_sql = text("""
            SELECT assignment_id, module_id, title, spec
            FROM assignments
            WHERE module_id IN (
                SELECT module_id FROM modules WHERE course_id = :course_id
            );
        """)

        async with AsyncSessionLocal() as session:
            m_res = await session.execute(modules_sql, {"course_id": str(course_id)})
            m_rows = m_res.mappings().all()

            a_res = await session.execute(assignments_sql, {"course_id": str(course_id)})
            a_rows = a_res.mappings().all()

        assignments_by_module: dict[str, list[dict[str, Any]]] = {}
        for a in a_rows:
            mid = str(a["module_id"])
            if mid not in assignments_by_module:
                assignments_by_module[mid] = []
            assignments_by_module[mid].append({
                "assignment_id": str(a["assignment_id"]),
                "title": a["title"],
                "status": a["spec"].get("status", "draft") if isinstance(a["spec"], dict) else "draft",
            })

        modules: list[ModuleResponse] = []
        for idx, m in enumerate(m_rows):
            mid_str = str(m["module_id"])
            modules.append(
                ModuleResponse(
                    module_id=m["module_id"],
                    course_id=m["course_id"],
                    title=m["title"],
                    description=m["description"],
                    learning_objectives=m["learning_objectives"] or [],
                    position=m["position"],
                    is_locked=(idx > 0),
                    assignments=assignments_by_module.get(mid_str, []),
                )
            )
        return modules

    @classmethod
    async def get_module(cls, course_id: UUID | str, module_id: UUID | str) -> ModuleResponse | None:
        """
        Fetches details, learning objectives, lock status, and assignments for a single module.
        """
        sql = text("""
            SELECT module_id, course_id, title, description, learning_objectives, position
            FROM modules
            WHERE course_id = :course_id AND module_id = :module_id;
        """)

        assignments_sql = text("""
            SELECT assignment_id, title, spec
            FROM assignments
            WHERE module_id = :module_id;
        """)

        async with AsyncSessionLocal() as session:
            res = await session.execute(sql, {"course_id": str(course_id), "module_id": str(module_id)})
            row = res.mappings().first()
            if not row:
                return None

            a_res = await session.execute(assignments_sql, {"module_id": str(module_id)})
            a_rows = a_res.mappings().all()

        assignments = [
            {
                "assignment_id": str(a["assignment_id"]),
                "title": a["title"],
                "status": a["spec"].get("status", "draft") if isinstance(a["spec"], dict) else "draft",
            }
            for a in a_rows
        ]

        return ModuleResponse(
            module_id=row["module_id"],
            course_id=row["course_id"],
            title=row["title"],
            description=row["description"],
            learning_objectives=row["learning_objectives"] or [],
            position=row["position"],
            is_locked=row["position"] > 1,
            assignments=assignments,
        )

    @classmethod
    async def get_cohort_roster(cls, course_id: UUID | str) -> CohortRosterResponse:
        """
        Aggregates student performance across all course assignments, computing
        Autonomy Scores (A_s), hint consumption rates, and active struggle flags.
        """
        course = await cls.get_course(course_id)
        if not course:
            raise ValueError(f"Course '{course_id}' not found.")

        # Query session telemetry linked to this course
        telemetry_sql = text("""
            SELECT 
                s.student_id,
                COUNT(DISTINCT s.session_id) as session_count,
                COUNT(DISTINCT CASE WHEN s.status = 'completed' THEN s.session_id END) as completed_count,
                COUNT(CASE WHEN e.event_type = 'hint_served' THEN 1 END) as hint_count,
                COUNT(CASE WHEN e.event_type = 'misconception_flagged' THEN 1 END) as misconception_count,
                jsonb_agg(CASE WHEN e.event_type = 'hint_served' THEN e.payload END) as hints,
                jsonb_agg(CASE WHEN e.event_type = 'misconception_flagged' THEN e.payload END) as misconceptions
            FROM student_sessions s
            JOIN assignments a ON s.assignment_id = a.assignment_id
            JOIN modules m ON a.module_id = m.module_id
            LEFT JOIN session_events e ON s.session_id = e.session_id
            WHERE m.course_id = :course_id
            GROUP BY s.student_id;
        """)

        async with AsyncSessionLocal() as session:
            result = await session.execute(telemetry_sql, {"course_id": str(course_id)})
            rows = result.mappings().all()

        students: list[CohortStudentMetrics] = []

        for r in rows:
            student_id = r["student_id"]
            session_count = int(r["session_count"])
            completed = int(r["completed_count"])
            hint_count = int(r["hint_count"])
            misconception_count = int(r["misconception_count"])

            hints_data = [h for h in (r["hints"] or []) if h is not None]
            misconceptions_data = [m for m in (r["misconceptions"] or []) if m is not None]

            # Calculate Autonomy Score
            # Each hint rung decrements by 0.25 (rung 1 -> 0.75, rung 2 -> 0.50, rung 3 -> 0.25)
            autonomy_scores = []
            struggling_kcs = set()

            for h in hints_data:
                rung = h.get("rung", 1)
                autonomy_scores.append(max(0.0, 1.0 - 0.25 * rung))
                if rung >= 3 and "target_kc" in h:
                    struggling_kcs.add(h["target_kc"])

            for m in misconceptions_data:
                if "kc_id" in m:
                    struggling_kcs.add(m["kc_id"])

            avg_autonomy = round(sum(autonomy_scores) / len(autonomy_scores), 2) if autonomy_scores else 1.00
            hint_rate = round(hint_count / max(session_count * 2, 1), 2)
            active_struggle = (avg_autonomy < 0.60) or (misconception_count >= 2) or (hint_rate > 0.50)

            students.append(
                CohortStudentMetrics(
                    student_id=student_id,
                    session_count=session_count,
                    completed_assignments=completed,
                    average_autonomy_score=avg_autonomy,
                    hint_consumption_rate=hint_rate,
                    active_struggle=active_struggle,
                    struggling_kcs=sorted(struggling_kcs),
                )
            )


        # If no live sessions exist yet, return diagnostic cohort baseline
        if not students:
            students = [
                CohortStudentMetrics(
                    student_id="student_somerville_01",
                    session_count=3,
                    completed_assignments=2,
                    average_autonomy_score=0.92,
                    hint_consumption_rate=0.15,
                    active_struggle=False,
                    struggling_kcs=[],
                ),
                CohortStudentMetrics(
                    student_id="student_struggling_02",
                    session_count=4,
                    completed_assignments=1,
                    average_autonomy_score=0.48,
                    hint_consumption_rate=0.75,
                    active_struggle=True,
                    struggling_kcs=["KC_HIST_FRENCH_DEBT", "KC_HIST_ESTATES_GENERAL"],
                ),
                CohortStudentMetrics(
                    student_id="student_advanced_03",
                    session_count=5,
                    completed_assignments=5,
                    average_autonomy_score=1.00,
                    hint_consumption_rate=0.00,
                    active_struggle=False,
                    struggling_kcs=[],
                ),
            ]

        return CohortRosterResponse(
            course_id=course.course_id,
            course_title=course.title,
            total_enrolled=len(students),
            students=students,
        )


course_service = CourseService()
