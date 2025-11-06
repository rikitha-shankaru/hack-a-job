from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import TailorRequest, TailorResponse
from app.workflows.job_application_workflow import JobApplicationWorkflow
from app.models import User, Job
from typing import Dict, Any
import uuid

router = APIRouter()

@router.post("/complete", response_model=Dict[str, Any])
async def run_complete_workflow(
    request: TailorRequest,
    db: Session = Depends(get_db)
):
    """Run the complete LangGraph workflow: Parse → Search → Tailor → Cover Letter → Autofill → Email"""
    try:
        # Validate user and job exist
        user = db.query(User).filter(User.id == request.userId).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if not user.profile:
            raise HTTPException(status_code=400, detail="User profile not found. Please ingest resume first.")
        
        job = db.query(Job).filter(Job.id == request.jobId).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Get resume PDF path
        resume_pdf_path = user.profile.resume_pdf_url
        if not resume_pdf_path:
            raise HTTPException(status_code=400, detail="Resume PDF not found. Please upload a PDF resume.")
        
        # Remove leading slash if present
        if resume_pdf_path.startswith('/'):
            resume_pdf_path = resume_pdf_path[1:]
        
        # Run complete workflow
        workflow = JobApplicationWorkflow(db)
        result = await workflow.run(
            user_id=str(request.userId),
            job_id=str(request.jobId),
            resume_pdf_path=resume_pdf_path
        )
        
        return {
            "status": "completed",
            "verification_url": result.get("verification_url", ""),
            "message": "Complete workflow executed successfully. Check your email for verification link."
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("", response_model=TailorResponse)
async def tailor_resume(
    request: TailorRequest,
    db: Session = Depends(get_db)
):
    """Generate tailored resume and cover letter for a job"""
    try:
        # Validate user and job exist
        user = db.query(User).filter(User.id == request.userId).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if not user.profile:
            raise HTTPException(status_code=400, detail="User profile not found. Please ingest resume first.")
        
        job = db.query(Job).filter(Job.id == request.jobId).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Generate tailored assets
        from app.services.tailor_service import TailorService
        service = TailorService()
        
        try:
            assets = await service.generate_tailored_assets(
                user=user,
                job=job,
                db=db
            )
        except ValueError as e:
            # Convert ValueError to HTTPException with proper status code
            raise HTTPException(status_code=400, detail=str(e))
        
        return TailorResponse(
            assetsId=assets.id,
            resumePdfUrl=assets.resume_pdf_url or "",
            coverPdfUrl=assets.cover_pdf_url or "",
            diffs=assets.resume_json.get("diffs", {})
        )
    except HTTPException:
        raise
    except Exception as e:
        # Log the full error for debugging
        import traceback
        print(f"Error in tailor_resume: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
