from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import date

# Profile schemas
class ProfileIngestRequest(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    roleTarget: Optional[str] = None
    levelTarget: Optional[str] = None
    resumeText: Optional[str] = None
    resumeFileUrl: Optional[str] = None

class ProfileIngestResponse(BaseModel):
    userId: UUID
    parsed: Dict[str, Any]
    resumeJson: Dict[str, Any]
    resumeVector: Optional[List[float]] = None

# Job search schemas
class JobSearchRequest(BaseModel):
    query: str
    location: Optional[str] = None
    recency: Optional[str] = Field(None, pattern="^(d7|w2|m1)$")
    roleTarget: Optional[str] = None
    levelTarget: Optional[str] = None

class JobResponse(BaseModel):
    id: UUID
    company: Optional[str]
    title: Optional[str]
    location: Optional[str]
    datePosted: Optional[date]
    url: str
    jd_keywords: Optional[List[str]] = []
    jd_text: Optional[str] = None  # Job description text for cover letter detection

class JobSearchResponse(BaseModel):
    jobs: List[JobResponse]

# Tailor schemas
class TailorRequest(BaseModel):
    userId: UUID
    jobId: UUID

class TailorResponse(BaseModel):
    assetsId: UUID
    originalResumePdfUrl: Optional[str] = None  # Original resume PDF URL
    resumePdfUrl: str  # Tailored resume PDF URL
    coverPdfUrl: str  # Cover letter PDF URL
    diffs: Dict[str, Any]

# Email schemas
class EmailSendRequest(BaseModel):
    userId: UUID
    jobId: UUID
    assetsId: UUID

class EmailSendResponse(BaseModel):
    status: str

# Autofill schemas (Phase-2)
class AutofillRunRequest(BaseModel):
    userId: UUID
    jobId: UUID

class AutofillRunResponse(BaseModel):
    runId: UUID
    status: str
    screenshots: List[str] = []
    confidence: Dict[str, float] = {}
    verification_url: Optional[str] = None

class AutofillApproveRequest(BaseModel):
    runId: UUID
    submit: bool = False

class AutofillApproveResponse(BaseModel):
    status: str

