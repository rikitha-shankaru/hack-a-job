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
        
        # Search all queries aggressively - but limit to avoid timeout
        # Focus on job board queries first (they give better results faster)
        all_items = []
        seen_urls = set()
        
        # Search job boards first (better quality, faster)
        # Search VERY aggressively to get 50-100+ results
        for search_query in job_board_queries[:10]:  # Top 10 job boards (maximum coverage)
            for start in [1, 11, 21, 31]:  # 4 pages per board (40 results each) = 400 potential results
                items = await self._search_cse(search_query, date_restrict, start)
                if not items:
                    break
                
                for item in items:
                    url = item.get("link", "")
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        all_items.append(item)
                
                if len(all_items) >= 300:  # Get LOTS of results for filtering
                    break
            
            if len(all_items) >= 300:
                break
        
        # Then search base queries for even more coverage
        if len(all_items) < 150:
            for search_query in base_queries:  # ALL base queries
                for start in [1, 11, 21]:  # 3 pages each
                    items = await self._search_cse(search_query, date_restrict, start)
                    if not items:
                        break
                    
                    for item in items:
                        url = item.get("link", "")
                        if url and url not in seen_urls:
                            seen_urls.add(url)
                            all_items.append(item)
                    
                    if len(all_items) >= 300:
                        break
                
                if len(all_items) >= 300:
                    break
        
        # all_items already deduplicated above, now process them
        # Fetch and parse each job posting - optimize for speed
        jobs = []
        async with httpx.AsyncClient(timeout=15.0) as client:  # Reduced timeout for speed
            # Process MANY items to account for filtering - we want 50-100+ good jobs
            # Process up to 300 items, filtering will reduce to quality results
            total_items = min(len(all_items), 300)
            
            for idx, item in enumerate(all_items[:300]):
                url = item.get("link", "")
                if not url:
                    continue
                
                # Filter out non-job URLs BEFORE fetching (saves time)
                if self._is_non_job_url(url):
                    continue
                
                try:
                    # Fetch HTML with shorter timeout for speed
                    response = await client.get(url, follow_redirects=True, timeout=10.0)
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
                    
                    if job_data and self._is_valid_job(job_data, location_filter=location):
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
    
    def _is_valid_job(self, job_data: dict, location_filter: Optional[str] = None) -> bool:
        """Validate that job data represents an actual job posting"""
        title = job_data.get("title", "").lower()
        company = job_data.get("company", "")
        jd_text = job_data.get("jd_text", "")
        url = job_data.get("url", "").lower()
        job_location = job_data.get("location", "").lower() if job_data.get("location") else ""
        
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
        
        # Check if this is from a known job board - be more lenient with these
        is_job_board_url = any(board in url for board in [
            'linkedin.com/jobs', 'indeed.com/viewjob', 'indeed.com/jobs', 
            'glassdoor.com/job', 'monster.com', 'ziprecruiter.com',
            'greenhouse.io', 'lever.co', 'careers.', 'jobs.'
        ])
        
        # Reject generic/nonsensical titles - but be lenient for job boards
        generic_titles = [
            'homepage', 'home page', 'welcome', 'sorry, you have been blocked',
            'just a moment', 'headlines', 'upcoming events', 'search salaries',
            'jobs jobs found', 'jobs found', 'jobs jobs',  # Generic search result pages
            'powered by people', 'qualcomm careers', 'engineering jobs and more',
            'careers |', 'careers page', 'all jobs', 'view all jobs',
            'browse jobs', 'find jobs', 'search jobs', 'job search',
            'sign in', 'log in', 'create account', 'register', 'login',
            'privacy policy', 'terms of service', 'cookie policy',
            'about us', 'contact us', 'help center', 'support'
        ]
        
        # Check if title is EXACTLY a generic site name (not just containing it)
        title_lower = title.lower().strip()
        if title_lower in ['linkedin', 'indeed', 'glassdoor', 'monster', 'ziprecruiter', 'google']:
            # If it's from a job board URL and has a job description, allow it
            if not (is_job_board_url and jd_text and len(jd_text) > 100):
                return False
        
        # For job boards, be more lenient - only reject if it's clearly not a job
        if is_job_board_url:
            # Only reject if title is clearly a generic page AND no job description
            if any(gt in title_lower for gt in generic_titles) and (not jd_text or len(jd_text) < 100):
                return False
        else:
            # For non-job-board URLs, be stricter
            if any(gt in title_lower for gt in generic_titles):
                return False
        
        # Reject titles with emojis (usually not real job titles)
        import re
        if re.search(r'[🐻🎯🔥💼🚀]', job_data.get("title", "")):
            return False
        
        # Must have a meaningful title (more than 3 words, less than 100 chars)
        # But be lenient for job boards - they might have shorter titles
        title_words = title.split()
        if not is_job_board_url:
            # Stricter for non-job-board URLs
            if len(title_words) < 3 or len(title) > 100:
                return False
        else:
            # More lenient for job boards - allow 2-word titles if there's a good description
            if len(title_words) < 2 or len(title) > 100:
                return False
            # If title is too short, require substantial job description
            if len(title_words) < 3 and (not jd_text or len(jd_text) < 150):
                return False
        
        # Title should look like a job title (not just company name + "jobs")
        if title.endswith(' jobs') and len(title_words) <= 3:
            return False
        
        # Reject titles that are clearly career pages, not job postings
        career_page_indicators = [
            'careers |', 'careers page', 'all jobs', 'view all jobs',
            'jobs and more', 'engineering jobs and more', 'find jobs',
            'search jobs', 'browse jobs', 'job search',
            'careers at', 'careers in', 'career opportunities',  # "Careers at RBC"
            'join our team', 'work with us', 'we are hiring', 'open positions'
        ]
        if any(indicator in title.lower() for indicator in career_page_indicators):
            return False
        
        # Reject if title starts with "Careers" (career pages, not jobs)
        if title.lower().startswith('careers'):
            return False
        
        # Must have company OR job description
        if not company and not jd_text:
            return False
        
        # Company name shouldn't be generic or weird
        generic_companies = [
            'health care', 'healthcare', 'linkedin', 'indeed', 'glassdoor',
            'professional', 'company', 'corporation', 'inc', 'llc',  # Too generic
            'rbc',  # Just "RBC" without context is likely a career page
        ]
        if company:
            company_lower = company.lower().strip()
            # Reject generic company names
            if company_lower in generic_companies:
                if not jd_text or len(jd_text) < 200:  # Need substantial job description
                    return False
            # Reject company names with weird prefixes (like "z_Greendale")
            if company_lower.startswith('z_') or company_lower.startswith('x_'):
                return False
            # Company name should be meaningful (more than 2 characters, less than 100)
            if len(company_lower) < 3 or len(company_lower) > 100:
                return False
        
        # Job description should contain job-related keywords
        # But be lenient for job boards - they're usually valid even without keywords
        if jd_text:
            jd_lower = jd_text.lower()
            job_keywords = ['responsibilities', 'requirements', 'qualifications', 
                          'experience', 'skills', 'apply', 'position', 'role',
                          'salary', 'benefits', 'full-time', 'part-time', 'remote',
                          'job description', 'we are looking', 'candidate', 'must have',
                          'about the role', 'what you', 'you will', 'you\'ll', 'we need']
            if not any(keyword in jd_lower for keyword in job_keywords):
                # If no job keywords, only reject if it's NOT from a known job board
                # Job boards are trusted sources - allow them even without keywords
                if not is_job_board_url:
                    return False
        
        # Check for future dates (likely parsing errors) - reject ALL future dates
        date_posted = job_data.get("date_posted")
        if date_posted:
            from datetime import date, timedelta
            today = date.today()
            if date_posted > today:
                # Future date is definitely a parsing error - reject it
                print(f"Rejecting job with future date: {date_posted} (today: {today})")
                return False
            # Also reject dates too far in the past (more than 1 year old)
            one_year_ago = today - timedelta(days=365)
            if date_posted < one_year_ago:
                print(f"Rejecting job with old date: {date_posted} (more than 1 year old)")
                return False
        
        # Location filtering - if location specified, job must match OR be remote
        # Remote jobs are always included regardless of location filter
        is_remote_job = False
        if job_location:
            job_location_lower = job_location.lower()
            remote_indicators = ['remote', 'anywhere', 'work from home', 'wfh', 'virtual', 'distributed']
            is_remote_job = any(indicator in job_location_lower for indicator in remote_indicators)
        
        # Also check job description for remote indicators
        if not is_remote_job and jd_text:
            jd_lower = jd_text.lower()
            remote_indicators = ['remote', 'anywhere', 'work from home', 'wfh', 'virtual', 'distributed', 'work remotely']
            is_remote_job = any(indicator in jd_lower for indicator in remote_indicators)
        
        # If it's a remote job, always include it (regardless of location filter)
        if is_remote_job:
            return True
        
        # If location filter specified and job is not remote, must match location
        if location_filter:
            location_filter_lower = location_filter.lower().strip()
            # Normalize location filter (remove common variations)
            location_variations = {
                'new york': ['new york', 'ny', 'nyc', 'new york city', 'manhattan', 'brooklyn', 'queens', 'bronx', 'staten island'],
                'california': ['california', 'ca', 'san francisco', 'sf', 'los angeles', 'la', 'san diego', 'palo alto', 'san jose', 'oakland'],
                'chicago': ['chicago', 'il', 'illinois'],
                'boston': ['boston', 'ma', 'massachusetts'],
                'seattle': ['seattle', 'wa', 'washington'],
                'texas': ['texas', 'tx', 'austin', 'dallas', 'houston'],
                'florida': ['florida', 'fl', 'miami', 'tampa', 'orlando'],
            }
            
            # Check if location filter matches any known variations
            matched_location = False
            for key, variations in location_variations.items():
                if location_filter_lower in variations or any(var in location_filter_lower for var in variations):
                    # Check if job location matches any variation
                    if job_location:
                        for var in variations:
                            if var in job_location:
                                matched_location = True
                                break
                    # Also check in job description
                    if jd_text:
                        jd_lower = jd_text.lower()
                        for var in variations:
                            if var in jd_lower:
                                matched_location = True
                                break
                    break
            
            # If no match found, do simple substring check
            if not matched_location:
                if job_location:
                    # Check if location filter appears in job location
                    if location_filter_lower not in job_location and job_location not in location_filter_lower:
                        # Reject if location doesn't match at all
                        if not self._is_location_match(location_filter_lower, job_location):
                            print(f"Rejecting job - location mismatch: '{job_location}' doesn't match '{location_filter}'")
                            return False
        
        return True
    
    def _is_location_match(self, filter_location: str, job_location: str) -> bool:
        """Check if job location matches filter location (lenient matching)"""
        # Extract state/country from filter
        filter_parts = filter_location.split()
        
        # Check if any part of filter matches job location
        for part in filter_parts:
            if len(part) > 2 and part in job_location:
                return True
        
        # Check for common abbreviations
        location_abbrevs = {
            'ny': 'new york',
            'nyc': 'new york',
            'ca': 'california',
            'sf': 'san francisco',
            'la': 'los angeles',
            'il': 'illinois',
            'ma': 'massachusetts',
            'wa': 'washington',
        }
        
        for abbrev, full in location_abbrevs.items():
            if abbrev in filter_location and (full in job_location or abbrev in job_location):
                return True
        
        return False

