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
        """Search jobs using Google Custom Search API - matching Google's native job search format"""
        # Match Google's exact search format: "software jobs in california"
        # Google's native job search uses natural language, no site restrictions
        
        # Map recency to Google CSE dateRestrict format
        date_mapping = {
            "d7": "d7",
            "w2": "w2",
            "m1": "m1"
        }
        date_restrict = date_mapping.get(recency, "w2")
        
        # Build multiple query strategies to maximize results
        # Google searches broadly across many sources, so we'll do the same
        
        base_queries = []
        if location:
            base_queries = [
                f'{query} jobs in {location}',
                f'{query} {location} jobs',
                f'{query} job {location}',
                f'{query} hiring {location}',
                f'{query} career {location}',
                f'{query} position {location}',
            ]
        else:
            base_queries = [
                f'{query} jobs',
                f'{query} job',
                f'{query} hiring',
                f'{query} career',
                f'{query} position',
            ]
        
        # Also search specific job boards directly (these give better results)
        job_board_queries = []
        if location:
            job_board_queries = [
                f'{query} site:linkedin.com/jobs {location}',
                f'{query} site:indeed.com {location}',
                f'{query} site:glassdoor.com {location}',
                f'{query} site:greenhouse.io {location}',
                f'{query} site:lever.co {location}',
                f'{query} site:monster.com {location}',
                f'{query} site:ziprecruiter.com {location}',
                f'{query} site:careers.google.com {location}',
                f'{query} site:jobs.apple.com {location}',
                f'{query} site:careers.microsoft.com {location}',
            ]
        else:
            job_board_queries = [
                f'{query} site:linkedin.com/jobs',
                f'{query} site:indeed.com',
                f'{query} site:glassdoor.com',
                f'{query} site:greenhouse.io',
                f'{query} site:lever.co',
                f'{query} site:monster.com',
                f'{query} site:ziprecruiter.com',
            ]
        
        # Combine all queries
        all_queries = base_queries + job_board_queries
        
        # Search all queries aggressively
        all_items = []
        seen_urls = set()
        
        for search_query in all_queries:
            # Search up to 3 pages per query (30 results per query)
            for start in [1, 11, 21]:
                items = await self._search_cse(search_query, date_restrict, start)
                if not items:
                    break
                
                # Add unique items only
                for item in items:
                    url = item.get("link", "")
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        all_items.append(item)
                
                # Stop if we have enough results
                if len(all_items) >= 100:
                    break
            
            # Stop if we have enough results
            if len(all_items) >= 100:
                break
        
        # all_items already deduplicated above, now process them
        # Fetch and parse each job posting
        jobs = []
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Process MORE items to account for filtering - we want 20-30 good jobs
            # Process up to 100 items, filtering will reduce to quality results
            for item in all_items[:100]:
                url = item.get("link", "")
                if not url:
                    continue
                
                # Filter out non-job URLs
                if self._is_non_job_url(url):
                    continue
                
                try:
                    # Fetch HTML
                    response = await client.get(url, follow_redirects=True)
                    html = response.text
                    
                    # Quick check for unavailable jobs before parsing
                    html_lower = html.lower()
                    unavailable_indicators = [
                        'no longer available', 'job is no longer available', 
                        'position has been filled', 'this job is closed',
                        'application closed', 'position closed', 'no longer accepting',
                        'sorry this job', 'expired', 'unavailable', 'filled'
                    ]
                    if any(indicator in html_lower for indicator in unavailable_indicators):
                        print(f"Skipping unavailable job: {url}")
                        continue
                    
                    # Parse job posting
                    job_data = await self.parser.parse_job_posting(url, html)
                    
                    if job_data and self._is_valid_job(job_data):
                        # Check for duplicates by title+company
                        is_duplicate = False
                        title_company_key = f"{job_data.get('title', '').lower()}_{job_data.get('company', '').lower()}"
                        for existing_job in jobs:
                            existing_key = f"{existing_job.title.lower() if existing_job.title else ''}_{existing_job.company.lower() if existing_job.company else ''}"
                            if title_company_key == existing_key and title_company_key:
                                is_duplicate = True
                                break
                        
                        if not is_duplicate:
                            # Store or update job
                            job = self._upsert_job(job_data, db)
                            if job:
                                jobs.append(job)
                except Exception as e:
                    print(f"Error parsing job {url}: {e}")
                    continue
        
        return jobs
    
    async def _search_cse(self, query: str, date_restrict: str, start: int) -> List[dict]:
        """Search Google Custom Search API - matching Google's native search behavior"""
        params = {
            "key": settings.google_cse_key,
            "cx": settings.google_cse_cx,
            "q": query.strip(),
            "dateRestrict": date_restrict,
            "gl": "US",  # Country: United States
            "lr": "lang_en",  # Language: English
            "num": 10,  # Results per page
            "start": start,  # Start index
            # Don't use site restrictions - let Google CSE search broadly like native search
            # The filtering will handle removing non-job URLs
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
        
        # Filter out fields that don't exist in Job model
        valid_fields = {
            "company", "title", "location", "region", "remote", 
            "date_posted", "valid_through", "salary", "url", 
            "source", "jd_text", "jd_keywords"
        }
        filtered_data = {k: v for k, v in job_data.items() if k in valid_fields}
        
        # Check if job already exists
        existing = db.query(Job).filter(Job.url == url).first()
        
        if existing:
            # Update existing job
            for key, value in filtered_data.items():
                if hasattr(existing, key) and value is not None:
                    setattr(existing, key, value)
            db.commit()
            db.refresh(existing)
            return existing
        else:
            # Create new job
            job = Job(
                id=uuid.uuid4(),
                **filtered_data
            )
            db.add(job)
            db.commit()
            db.refresh(job)
            return job
    
    def _is_non_job_url(self, url: str) -> bool:
        """Filter out URLs that are clearly not job postings"""
        url_lower = url.lower()
        
        # Allow job board URLs (these are good!)
        job_board_patterns = [
            'linkedin.com/jobs', 'indeed.com', 'glassdoor.com', 'greenhouse.io',
            'lever.co', 'monster.com', 'ziprecruiter.com', 'careers.',
            'jobs.', 'job.', 'hiring.', 'apply.', 'career.'
        ]
        
        # If it's from a known job board, allow it
        if any(pattern in url_lower for pattern in job_board_patterns):
            return False
        
        # Exclude common non-job domains
        exclude_patterns = [
            'facebook.com', 'twitter.com', 'instagram.com', 'linkedin.com/company',
            'linkedin.com/in/', 'linkedin.com/feed', 'youtube.com', 'reddit.com',
            'wikipedia.org', '/news/', '/blog/', '/article/', '/story/',
            '.gov/', '.edu/', 'consulado', 'police', 'park', 'library', 'museum',
            'aquarium', 'botanic', 'school', 'university', 'college', 'law.',
            'nba.com', 'mlb.com', 'nhl.com', 'sports', 'entertainment',
            'blockclubchicago', 'southsideweekly', 'abc7chicago', 'fox32chicago',
            '6figr.com', 'levels.fyi', '/event/', '/events/', '/calendar/',
            '/about/', '/contact/', '/privacy/', '/terms/', '/help/',
            'linkedin.com/company/', 'linkedin.com/feed', 'linkedin.com/pulse'
        ]
        
        return any(pattern in url_lower for pattern in exclude_patterns)
    
    def _is_valid_job(self, job_data: dict) -> bool:
        """Validate that job data represents an actual job posting"""
        title = job_data.get("title", "").lower()
        company = job_data.get("company", "")
        jd_text = job_data.get("jd_text", "")
        url = job_data.get("url", "").lower()
        
        # Check for expired/unavailable job indicators
        unavailable_indicators = [
            'no longer available', 'job is no longer available', 'position has been filled',
            'this job is closed', 'application closed', 'position closed', 'no longer accepting',
            'expired', 'unavailable', 'filled', 'closed position'
        ]
        
        if jd_text:
            jd_lower = jd_text.lower()
            if any(indicator in jd_lower for indicator in unavailable_indicators):
                return False
        
        # Reject generic/nonsensical titles - be more aggressive
        generic_titles = [
            'homepage', 'home page', 'welcome', 'sorry, you have been blocked',
            'just a moment', 'headlines', 'upcoming events', 'search salaries',
            'jobs jobs found', 'jobs found', 'jobs jobs',  # Generic search result pages
            'powered by people', 'qualcomm careers', 'engineering jobs and more',
            'careers |', 'careers page', 'all jobs', 'view all jobs',
            'browse jobs', 'find jobs', 'search jobs', 'job search',
            'linkedin', 'indeed', 'glassdoor', 'monster', 'ziprecruiter',  # Generic site names
            'sign in', 'log in', 'create account', 'register', 'login',
            'privacy policy', 'terms of service', 'cookie policy',
            'about us', 'contact us', 'help center', 'support'
        ]
        
        # Check if title is just a generic site name
        title_lower = title.lower().strip()
        if title_lower in ['linkedin', 'indeed', 'glassdoor', 'monster', 'ziprecruiter', 'google']:
            return False
        
        if any(gt in title_lower for gt in generic_titles):
            return False
        
        # Reject titles with emojis (usually not real job titles)
        import re
        if re.search(r'[🐻🎯🔥💼🚀]', job_data.get("title", "")):
            return False
        
        # Must have a meaningful title (more than 3 words, less than 100 chars)
        title_words = title.split()
        if len(title_words) < 3 or len(title) > 100:
            return False
        
        # Title should look like a job title (not just company name + "jobs")
        if title.endswith(' jobs') and len(title_words) <= 3:
            return False
        
        # Reject titles that are clearly career pages, not job postings
        career_page_indicators = [
            'careers |', 'careers page', 'all jobs', 'view all jobs',
            'jobs and more', 'engineering jobs and more', 'find jobs',
            'search jobs', 'browse jobs', 'job search'
        ]
        if any(indicator in title for indicator in career_page_indicators):
            return False
        
        # Must have company OR job description
        if not company and not jd_text:
            return False
        
        # Company name shouldn't be generic
        if company and company.lower() in ['health care', 'healthcare', 'linkedin', 'indeed']:
            if not jd_text or len(jd_text) < 200:  # Need substantial job description
                return False
        
        # Job description should contain job-related keywords
        if jd_text:
            jd_lower = jd_text.lower()
            job_keywords = ['responsibilities', 'requirements', 'qualifications', 
                          'experience', 'skills', 'apply', 'position', 'role',
                          'salary', 'benefits', 'full-time', 'part-time', 'remote',
                          'job description', 'we are looking', 'candidate', 'must have']
            if not any(keyword in jd_lower for keyword in job_keywords):
                # If no job keywords, reject unless it's from a known job board
                known_job_boards = ['greenhouse', 'lever', 'linkedin.com/jobs', 
                                   'indeed.com', 'glassdoor.com', 'monster.com',
                                   'ziprecruiter.com', 'careers.', 'jobs.']
                if not any(board in url for board in known_job_boards):
                    return False
        
        # Check for future dates (likely parsing errors) - reject ALL future dates
        date_posted = job_data.get("date_posted")
        if date_posted:
            from datetime import date
            today = date.today()
            if date_posted > today:
                # Future date is definitely a parsing error - reject it
                print(f"Rejecting job with future date: {date_posted} (today: {today})")
                return False
        
        return True

