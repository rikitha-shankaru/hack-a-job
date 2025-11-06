from sqlalchemy import Column, String, Boolean, Date, Text, ForeignKey, JSON, CheckConstraint, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from app.database import Base
import uuid

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False)
    name = Column(String)
    role_target = Column(String)
    level_target = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    profile = relationship("Profile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    tailored_assets = relationship("TailoredAsset", back_populates="user", cascade="all, delete-orphan")
    autofill_runs = relationship("AutofillRun", back_populates="user", cascade="all, delete-orphan")

class Profile(Base):
    __tablename__ = "profiles"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    resume_json = Column(JSONB, nullable=False)
    resume_pdf_url = Column(String)  # Original PDF URL
    resume_latex_template = Column(Text)  # LaTeX template extracted from original PDF
    skills = Column(JSONB)
    metrics = Column(JSONB)
    links = Column(JSONB)
    resume_vector = Column(Vector(1536))
    
    user = relationship("User", back_populates="profile")

class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company = Column(String)
    title = Column(String)
    location = Column(String)
    region = Column(String)
    remote = Column(Boolean, default=False)
    date_posted = Column(Date)
    valid_through = Column(Date)
    salary = Column(JSONB)
    url = Column(String, unique=True)
    source = Column(String)
    jd_text = Column(Text)
    jd_keywords = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    tailored_assets = relationship("TailoredAsset", back_populates="job", cascade="all, delete-orphan")
    autofill_runs = relationship("AutofillRun", back_populates="job", cascade="all, delete-orphan")

class TailoredAsset(Base):
    __tablename__ = "tailored_assets"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"))
    resume_json = Column(JSONB, nullable=False)
    resume_pdf_url = Column(String)
    cover_json = Column(JSONB, nullable=False)
    cover_pdf_url = Column(String)
    status = Column(String, default="draft")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        CheckConstraint("status IN ('draft', 'emailed')", name="check_status"),
    )
    
    user = relationship("User", back_populates="tailored_assets")
    job = relationship("Job", back_populates="tailored_assets")

class AutofillRun(Base):
    __tablename__ = "autofill_runs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"))
    portal = Column(String)  # greenhouse/lever/other
    status = Column(String, default="prefilled")
    filled_fields = Column(JSONB)
    confidence = Column(JSONB)
    screenshots = Column(JSONB)
    verification_url = Column(String)  # URL to verify autofilled application
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        CheckConstraint("status IN ('prefilled', 'needs_input', 'submitted', 'error')", name="check_autofill_status"),
    )
    
    user = relationship("User", back_populates="autofill_runs")
    job = relationship("Job", back_populates="autofill_runs")

