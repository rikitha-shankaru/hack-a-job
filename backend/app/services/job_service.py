from app.config import settings
from app.utils.job_parser import JobParser
from app.models import Job
from sqlalchemy.orm import Session
from typing import List, Optional
import httpx
import json
from datetime import datetime, date as date_type
import uuid
import asyncio
import time

class JobService:
    def __init__(self):
        self.parser = JobParser()
        self.last_request_time = 0
        self.min_request_interval = 0.5  # Minimum 500ms between requests to avoid rate limits
    
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
        # Rate limit: Google CSE allows ~100 queries/day free tier, so be smart
        # Search strategically: fewer queries but better quality
        for search_query in job_board_queries[:7]:  # Top 7 job boards (reduced from 10)
            for start in [1, 11]:  # 2 pages per board (reduced from 4) = 20 results each
                items = await self._search_cse(search_query, date_restrict, start)
                if not items:
                    break
                
                for item in items:
                    url = item.get("link", "")
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        all_items.append(item)
                
                # Rate limit: wait between requests
                await asyncio.sleep(self.min_request_interval)
                
                if len(all_items) >= 150:  # Reduced from 300
                    break
            
            if len(all_items) >= 150:
                break
        
        # Then search base queries for more coverage (but fewer)
        if len(all_items) < 80:
            for search_query in base_queries[:3]:  # Only top 3 base queries (reduced)
                for start in [1, 11]:  # 2 pages each
                    items = await self._search_cse(search_query, date_restrict, start)
                    if not items:
                        break
                    
                    for item in items:
                        url = item.get("link", "")
                        if url and url not in seen_urls:
                            seen_urls.add(url)
                            all_items.append(item)
                    
                    # Rate limit: wait between requests
                    await asyncio.sleep(self.min_request_interval)
                    
                    if len(all_items) >= 150:
                        break
                
                if len(all_items) >= 150:
                    break
        
        # all_items already deduplicated above, now process them
        # Fetch and parse each job posting - optimize for speed but respect rate limits
        jobs = []
        async with httpx.AsyncClient(timeout=15.0) as client:  # Reduced timeout for speed
            # Process items to account for filtering - we want 50-100+ good jobs
            # Process up to 150 items (reduced from 300 to avoid rate limits)
            total_items = min(len(all_items), 150)
            
            for idx, item in enumerate(all_items[:150]):
                # Rate limit: add small delay between fetches to avoid overwhelming servers
                if idx > 0 and idx % 10 == 0:  # Every 10 items, pause briefly
                    await asyncio.sleep(0.2)
                url = item.get("link", "")
                if not url:
                    continue
                
                # Filter out non-job URLs BEFORE fetching (saves time)
                if self._is_non_job_url(url):
                    continue
                
                try:
                    # Fetch HTML with shorter timeout for speed
                    response = await client.get(url, follow_redirects=True, timeout=10.0)
                    html = response.text if response.text else ""
                    
                    # Quick check for unavailable jobs before parsing
                    # BUT: Be more specific - don't skip LinkedIn/Indeed jobs based on generic text
                    # These sites often have "unavailable" text in their UI that doesn't mean the job is closed
                    is_linkedin_or_indeed = 'linkedin.com/jobs' in url or 'indeed.com' in url
                    
                    if not is_linkedin_or_indeed and html:
                        # For other sites, check for unavailable indicators
                        html_lower = html.lower()
                        unavailable_indicators = [
                            'no longer available', 'job is no longer available', 
                            'position has been filled', 'this job is closed',
                            'application closed', 'position closed', 'no longer accepting',
                            'sorry this job', 'expired', 'unavailable', 'filled'
                        ]
                        # Only skip if we find a clear unavailable message (not just the word "unavailable" alone)
                        if any(indicator in html_lower for indicator in unavailable_indicators):
                            # Double-check: make sure it's not just a false positive
                            # Skip if we see multiple indicators or very specific messages
                            specific_indicators = [
                                'no longer available', 'job is no longer available',
                                'position has been filled', 'this job is closed',
                                'application closed', 'position closed'
                            ]
                            if any(indicator in html_lower for indicator in specific_indicators):
                                print(f"Skipping unavailable job: {url}")
                                continue
                    
                    # Parse job posting
                    job_data = await self.parser.parse_job_posting(url, html)
                    
                    if job_data and self._is_valid_job(job_data, location_filter=location, html=html):
                        # Check for duplicates by title+company
                        is_duplicate = False
                        title = (job_data.get('title') or '').lower()
                        company = (job_data.get('company') or '').lower()
                        title_company_key = f"{title}_{company}"
                        for existing_job in jobs:
                            existing_title = (existing_job.title or '').lower() if existing_job.title else ''
                            existing_company = (existing_job.company or '').lower() if existing_job.company else ''
                            existing_key = f"{existing_title}_{existing_company}"
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
        
        # Rate limiting: ensure minimum time between requests
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        if time_since_last_request < self.min_request_interval:
            await asyncio.sleep(self.min_request_interval - time_since_last_request)
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            max_retries = 3
            retry_delay = 2  # Start with 2 seconds
            
            for attempt in range(max_retries):
                try:
                    self.last_request_time = time.time()
                    response = await client.get(
                        "https://www.googleapis.com/customsearch/v1",
                        params=params
                    )
                    
                    # Handle rate limiting (429)
                    if response.status_code == 429:
                        if attempt < max_retries - 1:
                            wait_time = retry_delay * (2 ** attempt)  # Exponential backoff: 2s, 4s, 8s
                            print(f"Rate limited (429). Waiting {wait_time}s before retry {attempt + 1}/{max_retries}...")
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            print(f"Rate limited (429) after {max_retries} attempts. Skipping this query.")
                            return []
                    
                    response.raise_for_status()
                    data = response.json()
                    return data.get("items", [])
                    
                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 429:
                        if attempt < max_retries - 1:
                            wait_time = retry_delay * (2 ** attempt)
                            print(f"Rate limited (429). Waiting {wait_time}s before retry {attempt + 1}/{max_retries}...")
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            print(f"Rate limited (429) after {max_retries} attempts. Skipping this query.")
                            return []
                    else:
                        print(f"HTTP error searching CSE: {e}")
                        return []
                except Exception as e:
                    print(f"Error searching CSE: {e}")
                    return []
            
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
    
    def _is_valid_job(self, job_data: dict, location_filter: Optional[str] = None, html: Optional[str] = None) -> bool:
        """
        Simplified job validation - only reject clearly invalid jobs
        Be lenient and accept most jobs from known job boards
        """
        # Safely handle None values - convert to empty string before calling .strip()
        title = (job_data.get("title") or "").strip()
        company = (job_data.get("company") or "").strip()
        jd_text = job_data.get("jd_text") or ""
        url = (job_data.get("url") or "").lower()
        job_location = (job_data.get("location") or "").lower() if job_data.get("location") else ""
        
        # CRITICAL CHECKS ONLY - reject if missing essential data
        if not title:
            print(f"❌ Rejecting: Missing title - {url[:50]}")
            return False
        
        # Check if this is from a known job board - trust these sources
        is_job_board_url = any(board in url for board in [
            'linkedin.com/jobs', 'indeed.com/viewjob', 'indeed.com/jobs', 
            'glassdoor.com/job', 'monster.com', 'ziprecruiter.com',
            'greenhouse.io', 'lever.co', 'careers.', 'jobs.'
        ])
        
        # For job boards, be VERY lenient - only reject obvious errors
        if is_job_board_url:
            # Only reject if:
            # 1. Title is clearly a generic page (homepage, login, etc.)
            # 2. Job is explicitly unavailable
            # 3. Future date (parsing error)
            
            title_lower = title.lower()
            generic_page_titles = [
                'homepage', 'home page', 'welcome', 'sign in', 'log in', 'login',
                'privacy policy', 'terms of service', 'about us', 'contact us',
                'request blocked', 'help us protect', 'blocked', 'access denied',
                'page not found', '404', 'error', 'forbidden', 'not found',
                'company not specified', 'not specified'
            ]
            
            # Reject generic page titles and error pages
            if any(generic in title_lower for generic in generic_page_titles):
                print(f"❌ Rejecting: Generic/error page title '{title}' - {url[:50]}")
                return False
            
            # Additional checks: reject titles that are clearly not job postings
            # Check for common non-job patterns in titles
            non_job_patterns = [
                'women in tech', 'event', 'workshop', 'conference', 'meetup',
                'news', 'article', 'blog', 'story', 'press release',
                'salary', 'interview', 'review', 'rating', 'comparison',
                'guide', 'how to', 'tips', 'advice', 'career advice',
                'resume template', 'cover letter template', 'sample'
            ]
            if any(pattern in title_lower for pattern in non_job_patterns):
                print(f"❌ Rejecting: Non-job pattern in title '{title}' - {url[:50]}")
                return False
            
            # Reject titles that start with numbers (parsing errors like "33Data")
            if title and len(title) > 0 and title[0].isdigit():
                # Check if it's a valid format (like "2024 Software Engineer") vs invalid ("33Data")
                words = title.split()
                if len(words) > 0 and words[0].isdigit() and len(words[0]) <= 2:
                    # Short number prefix (like "33") is likely a parsing error
                    print(f"❌ Rejecting: Invalid title format '{title}' - {url[:50]}")
                    return False
            
            # Check HTML content for error indicators (including non-English)
            if html:
                html_lower = html.lower()
                # Common error page indicators in various languages
                error_indicators = [
                    'page not found', '404', 'error', 'not found',
                    'لم يتم العثور',  # Arabic: "not found"
                    'صفحة غير موجودة',  # Arabic: "page not found"
                    'página no encontrada',  # Spanish
                    'seite nicht gefunden',  # German
                    'ページが見つかりません',  # Japanese
                    'страница не найдена'  # Russian
                ]
                if any(indicator in html_lower for indicator in error_indicators):
                    print(f"❌ Rejecting: Error page detected in HTML '{title}' - {url[:50]}")
                    return False
            
            # Check for unavailable jobs
            if jd_text:
                jd_lower = jd_text.lower()
                unavailable_indicators = [
                    'no longer available', 'no longer accepting', 'no longer accepting applications',
                    'position has been filled', 'this job is closed',
                    'application closed', 'position closed', 'expired', 'unavailable', 'filled',
                    'not accepting applications', 'applications closed'
                ]
                if any(indicator in jd_lower for indicator in unavailable_indicators):
                    print(f"❌ Rejecting: Unavailable job '{title}' - {url[:50]}")
                    return False
            
            # Check for future dates (parsing errors)
            date_posted = job_data.get("date_posted")
            if date_posted:
                from datetime import date, timedelta
                today = date.today()
                if date_posted > today:
                    print(f"❌ Rejecting: Future date {date_posted} - {url[:50]}")
                    return False
                # Allow old dates (don't reject - might be reposted)
            
            # Job boards are trusted - accept everything else
            print(f"✅ Accepting job board job: '{title}' at {company or 'Unknown'}")
            return True
        
        # For non-job-board URLs, do basic validation
        title_lower = title.lower()
        
        # Reject obviously non-job titles
        if len(title.split()) < 2:  # Too short
            print(f"❌ Rejecting: Title too short '{title}' - {url[:50]}")
            return False
        
        # Reject generic page titles and error pages
        generic_titles = [
            'homepage', 'home page', 'welcome', 'just a moment',
            'sorry, you have been blocked', 'headlines', 'upcoming events',
            'request blocked', 'help us protect', 'blocked', 'access denied',
            'page not found', '404', 'error', 'forbidden', 'loading',
            'redirecting', 'please wait', 'checking your browser'
        ]
        if any(generic in title_lower for generic in generic_titles):
            print(f"❌ Rejecting: Generic/error title '{title}' - {url[:50]}")
            return False
        
        # Additional checks: reject titles that are clearly not job postings
        non_job_patterns = [
            'women in tech', 'event', 'workshop', 'conference', 'meetup',
            'news', 'article', 'blog', 'story', 'press release',
            'salary', 'interview', 'review', 'rating', 'comparison',
            'guide', 'how to', 'tips', 'advice', 'career advice',
            'resume template', 'cover letter template', 'sample'
        ]
        if any(pattern in title_lower for pattern in non_job_patterns):
            print(f"❌ Rejecting: Non-job pattern in title '{title}' - {url[:50]}")
            return False
        
        # Reject if no company AND no job description
        if not company and not jd_text:
            print(f"❌ Rejecting: No company or description - {url[:50]}")
            return False
        
        # Reject if company is "Company not specified" or similar
        if company:
            company_lower = company.lower()
            if any(phrase in company_lower for phrase in ['not specified', 'not available', 'unknown', 'n/a', 'na']):
                print(f"❌ Rejecting: Invalid company name '{company}' - {url[:50]}")
                return False
        
        # Reject titles that start with numbers (parsing errors like "33Data")
        if title and len(title) > 0 and title[0].isdigit():
            words = title.split()
            if len(words) > 0 and words[0].isdigit() and len(words[0]) <= 2:
                # Short number prefix (like "33") is likely a parsing error
                print(f"❌ Rejecting: Invalid title format '{title}' - {url[:50]}")
                return False
        
        # Check HTML content for error indicators (including non-English)
        if html:
            html_lower = html.lower()
            error_indicators = [
                'page not found', '404', 'error', 'not found',
                'لم يتم العثور',  # Arabic: "not found"
                'صفحة غير موجودة',  # Arabic: "page not found"
                'página no encontrada',  # Spanish
                'seite nicht gefunden',  # German
                'ページが見つかりません',  # Japanese
                'страница не найдена'  # Russian
            ]
            if any(indicator in html_lower for indicator in error_indicators):
                print(f"❌ Rejecting: Error page detected in HTML '{title}' - {url[:50]}")
                return False
        
        # Check for unavailable jobs
        if jd_text:
            jd_lower = jd_text.lower()
            unavailable_indicators = [
                'no longer available', 'position has been filled', 'this job is closed',
                'application closed', 'position closed', 'expired', 'unavailable'
            ]
            if any(indicator in jd_lower for indicator in unavailable_indicators):
                print(f"❌ Rejecting: Unavailable job '{title}' - {url[:50]}")
                return False
        
        # Check for future dates
        date_posted = job_data.get("date_posted")
        if date_posted:
            from datetime import date
            today = date.today()
            if date_posted > today:
                print(f"❌ Rejecting: Future date {date_posted} - {url[:50]}")
                return False
        
        # Location filtering - if location specified, job must match OR be remote
        # Remote jobs are always included regardless of location filter
        if location_filter:
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
                print(f"✅ Accepting remote job: '{title}'")
                return True
            
            # If location filter specified and job is not remote, must match location
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

