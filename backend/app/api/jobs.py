from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import JobSearchRequest, JobSearchResponse, JobResponse
from app.services.job_service import JobService
from app.models import Job
from datetime import date, timedelta
from functools import lru_cache
import hashlib
import json

router = APIRouter()

# Simple in-memory cache for job searches (TTL: 5 minutes)
_job_cache = {}
_cache_ttl = timedelta(minutes=5)

def _get_cache_key(query: str, location: str, recency: str) -> str:
    """Generate cache key from search parameters"""
    key_data = f"{query}:{location}:{recency}"
    return hashlib.md5(key_data.encode()).hexdigest()

@router.post("/search", response_model=JobSearchResponse)
async def search_jobs(
    request: JobSearchRequest,
    db: Session = Depends(get_db)
):
    """Search for jobs using Google Custom Search API with caching"""
    try:
        # Check cache first
        cache_key = _get_cache_key(request.query, request.location or "", request.recency or "w2")
        if cache_key in _job_cache:
            cached_data, cached_time = _job_cache[cache_key]
            if (date.today() - cached_time) < _cache_ttl:
                return cached_data
        
        service = JobService()
        jobs = await service.search_and_store_jobs(
            query=request.query,
            location=request.location,
            recency=request.recency or "w2",
            db=db
        )
        
        # Return up to 100 jobs (user requested 50-100)
        jobs_to_return = jobs[:100]
        
        response = JobSearchResponse(
            jobs=[
                JobResponse(
                    id=job.id,
                    company=job.company,
                    title=job.title,
                    location=job.location,
                    datePosted=job.date_posted,
                    url=job.url,
                    jd_keywords=job.jd_keywords or [],
                    jd_text=job.jd_text  # Include job description for cover letter detection
                )
                for job in jobs_to_return
            ]
        )
        
        # Cache the response
        _job_cache[cache_key] = (response, date.today())
        
        # Clean old cache entries (keep only last 50)
        if len(_job_cache) > 50:
            oldest_key = min(_job_cache.keys(), key=lambda k: _job_cache[k][1])
            del _job_cache[oldest_key]
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

