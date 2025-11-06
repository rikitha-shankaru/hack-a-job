from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import (
    AutofillRunRequest, AutofillRunResponse,
    AutofillApproveRequest, AutofillApproveResponse
)
from app.services.autofill_service import AutofillService
from app.models import User, Job, AutofillRun

router = APIRouter()

@router.post("/run", response_model=AutofillRunResponse)
async def run_autofill(
    request: AutofillRunRequest,
    db: Session = Depends(get_db)
):
    """Pre-fill application portal (Phase-2)"""
    try:
        user = db.query(User).filter(User.id == request.userId).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        job = db.query(Job).filter(Job.id == request.jobId).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Get tailored assets first
        from app.models import TailoredAsset
        assets = db.query(TailoredAsset).filter(
            TailoredAsset.user_id == user.id,
            TailoredAsset.job_id == job.id
        ).first()
        
        if not assets:
            raise HTTPException(
                status_code=400, 
                detail="Tailored assets not found. Please tailor resume first."
            )
        
        service = AutofillService()
        run = await service.run_autofill_with_questions(
            user=user,
            job=job,
            resume_json=assets.resume_json,
            cover_letter=assets.cover_json,
            db=db
        )
        
        return AutofillRunResponse(
            runId=run.id,
            status=run.status,
            screenshots=run.screenshots or [],
            confidence=run.confidence or {},
            verification_url=run.verification_url
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/approve", response_model=AutofillApproveResponse)
async def approve_autofill(
    request: AutofillApproveRequest,
    db: Session = Depends(get_db)
):
    """Approve and optionally submit autofilled form (Phase-2)"""
    try:
        run = db.query(AutofillRun).filter(AutofillRun.id == request.runId).first()
        if not run:
            raise HTTPException(status_code=404, detail="Autofill run not found")
        
        service = AutofillService()
        if request.submit:
            await service.submit_form(run, db)
            run.status = "submitted"
        else:
            run.status = "prefilled"
        
        db.commit()
        
        return AutofillApproveResponse(status=run.status)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

