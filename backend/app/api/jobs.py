from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import JobSearchRequest, JobSearchResponse, JobResponse
from app.services.job_service import JobService
from app.models import Job
from datetime import date

router = APIRouter()

@router.post("/search", response_model=JobSearchResponse)
async def search_jobs(
    request: JobSearchRequest,
    db: Session = Depends(get_db)
):
    """Search for jobs using Google Custom Search API"""
    try:
        service = JobService()
        jobs = await service.search_and_store_jobs(
            query=request.query,
            location=request.location,
            recency=request.recency or "w2",
            db=db
        )
        
        return JobSearchResponse(
            jobs=[
                JobResponse(
                    id=job.id,
                    company=job.company,
                    title=job.title,
                    location=job.location,
                    datePosted=job.date_posted,
                    url=job.url,
                    jd_keywords=job.jd_keywords or []
                )
                for job in jobs
            ]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

