from app.config import settings
from app.utils.job_parser import JobParser
from app.models import Job
from sqlalchemy.orm import Session
from typing import List, Optional
import httpx
import json
from datetime import datetime, date as date_type
import uuid

class JobService:
    def __init__(self):
        self.parser = JobParser()
    
    async def search_and_store_jobs(
        self,
        query: str,
        location: Optional[str],
        recency: str,
        db: Session
    ) -> List[Job]:
        """Search jobs using Google Custom Search API and store them"""
        # Build search query
        search_query = f"{query}"
        if location:
            search_query += f" {location}"
        
        # Map recency to Google CSE dateRestrict format
        date_mapping = {
            "d7": "d7",
            "w2": "w2",
            "m1": "m1"
        }
        date_restrict = date_mapping.get(recency, "w2")
        
        # Search Google CSE (paginate 2-3 pages)
        all_items = []
        for start in [1, 11, 21]:
            items = await self._search_cse(search_query, date_restrict, start)
            all_items.extend(items)
        
        # Deduplicate by URL
        seen_urls = set()
        unique_items = []
        for item in all_items:
            url = item.get("link", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_items.append(item)
        
        # Fetch and parse each job posting
        jobs = []
        async with httpx.AsyncClient(timeout=30.0) as client:
            for item in unique_items[:30]:  # Limit to 30 jobs
                url = item.get("link", "")
                if not url:
                    continue
                
                try:
                    # Fetch HTML
                    response = await client.get(url, follow_redirects=True)
                    html = response.text
                    
                    # Parse job posting
                    job_data = await self.parser.parse_job_posting(url, html)
                    
                    if job_data:
                        # Store or update job
                        job = self._upsert_job(job_data, db)
                        if job:
                            jobs.append(job)
                except Exception as e:
                    print(f"Error parsing job {url}: {e}")
                    continue
        
        return jobs
    
    async def _search_cse(self, query: str, date_restrict: str, start: int) -> List[dict]:
        """Search Google Custom Search API"""
        params = {
            "key": settings.google_cse_key,
            "cx": settings.google_cse_cx,
            "q": query.strip(),
            "dateRestrict": date_restrict,
            "gl": "US",
            "lr": "lang_en",
            "num": 10,
            "start": start
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    "https://www.googleapis.com/customsearch/v1",
                    params=params
                )
                response.raise_for_status()
                data = response.json()
                return data.get("items", [])
            except Exception as e:
                print(f"Error searching CSE: {e}")
                return []
    
    def _upsert_job(self, job_data: dict, db: Session) -> Optional[Job]:
        """Upsert job with deduplication by URL"""
        url = job_data.get("url")
        if not url:
            return None
        
        # Check if job already exists
        existing = db.query(Job).filter(Job.url == url).first()
        
        if existing:
            # Update existing job
            for key, value in job_data.items():
                if hasattr(existing, key) and value is not None:
                    setattr(existing, key, value)
            db.commit()
            db.refresh(existing)
            return existing
        else:
            # Create new job
            job = Job(
                id=uuid.uuid4(),
                **job_data
            )
            db.add(job)
            db.commit()
            db.refresh(job)
            return job

