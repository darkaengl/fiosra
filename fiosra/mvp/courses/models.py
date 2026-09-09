import uuid
from datetime import UTC, datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from fiosra.mvp.database import Base


class Course(Base):
    __tablename__ = "courses"

    course_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    domain = Column(String(64), nullable=True, default="General")
    created_by = Column(String(64), nullable=False)
    syllabus_context = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    modules = relationship("Module", back_populates="course", cascade="all, delete-orphan", order_by="Module.position")
    syllabus_chunks = relationship("SyllabusChunk", back_populates="course", cascade="all, delete-orphan")


class Module(Base):
    __tablename__ = "modules"

    module_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id = Column(UUID(as_uuid=True), ForeignKey("courses.course_id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    learning_objectives = Column(JSONB, nullable=True, default=list)
    position = Column(Integer, nullable=False, default=1)

    course = relationship("Course", back_populates="modules")
    syllabus_chunks = relationship("SyllabusChunk", back_populates="module")


class SyllabusChunk(Base):
    __tablename__ = "syllabus_chunks"

    chunk_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id = Column(UUID(as_uuid=True), ForeignKey("courses.course_id", ondelete="CASCADE"), nullable=False)
    module_id = Column(UUID(as_uuid=True), ForeignKey("modules.module_id", ondelete="SET NULL"), nullable=True)
    title = Column(String(255), nullable=True)
    content = Column(Text, nullable=False)
    kc_id = Column(String(64), nullable=True)
    embedding = Column(Vector(1536), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    course = relationship("Course", back_populates="syllabus_chunks")
    module = relationship("Module", back_populates="syllabus_chunks")
