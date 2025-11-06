from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import ProfileIngestRequest, ProfileIngestResponse
from app.services.profile_service import ProfileService
from app.models import User, Profile
import uuid
import os
import aiofiles

router = APIRouter()

@router.post("/ingest", response_model=ProfileIngestResponse)
async def ingest_profile(
    email: str = Form(...),
    name: str = Form(None),
    roleTarget: str = Form(None),
    levelTarget: str = Form(None),
    resumeText: str = Form(None),
    resumeFile: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    """Ingest and parse a user's resume (supports PDF upload or text)"""
    try:
        # Get or create user
        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = User(
                id=uuid.uuid4(),
                email=email,
                name=name,
                role_target=roleTarget,
                level_target=levelTarget
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            # Update user info if provided
            if name:
                user.name = name
            if roleTarget:
                user.role_target = roleTarget
            if levelTarget:
                user.level_target = levelTarget
            db.commit()
        
        # Handle PDF upload
        pdf_path = None
        if resumeFile and resumeFile.filename.endswith('.pdf'):
            # Save uploaded PDF
            uploads_dir = "uploads/resumes"
            os.makedirs(uploads_dir, exist_ok=True)
            pdf_path = os.path.join(uploads_dir, f"{user.id}_resume.pdf")
            async with aiofiles.open(pdf_path, 'wb') as f:
                content = await resumeFile.read()
                await f.write(content)
        
        # Parse resume
        service = ProfileService()
        resume_data = await service.parse_resume(
            resume_text=resumeText,
            resume_url=None,
            resume_pdf_path=pdf_path
        )
        
        # Create or update profile
        profile = db.query(Profile).filter(Profile.user_id == user.id).first()
        if profile:
            profile.resume_json = resume_data["resume_json"]
            profile.resume_pdf_url = resume_data.get("resume_pdf_url")
            profile.resume_latex_template = resume_data.get("resume_latex_template")
            profile.skills = resume_data.get("skills")
            profile.metrics = resume_data.get("metrics")
            profile.links = resume_data.get("links")
            profile.resume_vector = resume_data.get("resume_vector")
        else:
            profile = Profile(
                user_id=user.id,
                resume_json=resume_data["resume_json"],
                resume_pdf_url=resume_data.get("resume_pdf_url"),
                resume_latex_template=resume_data.get("resume_latex_template"),
                skills=resume_data.get("skills"),
                metrics=resume_data.get("metrics"),
                links=resume_data.get("links"),
                resume_vector=resume_data.get("resume_vector")
            )
            db.add(profile)
        
        db.commit()
        db.refresh(profile)
        
        return ProfileIngestResponse(
            userId=user.id,
            parsed={
                "skills": resume_data.get("skills", []),
                "metrics": resume_data.get("metrics", {}),
                "links": resume_data.get("links", {})
            },
            resumeJson=resume_data["resume_json"],
            resumeVector=resume_data.get("resume_vector")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

