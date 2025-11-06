from bs4 import BeautifulSoup
from typing import Dict, Any, Optional, List
import json
import re
from datetime import datetime, date

class JobParser:
    """Parse job postings from JSON-LD or HTML"""
    
    def __init__(self):
        pass
    
    async def parse_job_posting(self, url: str, html: str) -> Optional[Dict[str, Any]]:
        """Parse job posting from HTML, preferring JSON-LD"""
        # Try JSON-LD first
        job_data = self._extract_jobposting_jsonld(html)
        
        if job_data:
            return self._normalize_job(url, job_data, html, structured=True)
        else:
            # Fallback to HTML parsing
            return self._normalize_job(url, None, html, structured=False)
    
    def _extract_jobposting_jsonld(self, html: str) -> Optional[Dict[str, Any]]:
        """Extract JobPosting JSON-LD from HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find all script tags with type="application/ld+json"
        scripts = soup.find_all('script', type='application/ld+json')
        
        for script in scripts:
            try:
                data = json.loads(script.string)
                
                # Handle @graph or direct object
                if isinstance(data, dict):
                    if data.get("@type") == "JobPosting":
                        return data
                    elif "@graph" in data:
                        for item in data["@graph"]:
                            if item.get("@type") == "JobPosting":
                                return item
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and item.get("@type") == "JobPosting":
                            return item
            except (json.JSONDecodeError, AttributeError):
                continue
        
        return None
    
    def _normalize_job(
        self,
        url: str,
        jsonld_data: Optional[Dict[str, Any]],
        html: str,
        structured: bool
    ) -> Optional[Dict[str, Any]]:
        """Normalize job data from JSON-LD or HTML"""
        job = {
            "url": url,
            "source": self._extract_source(url)
            # Note: 'structured' is removed - not a field in Job model
        }
        
        if jsonld_data:
            # Extract from JSON-LD
            job["title"] = self._safe_get(jsonld_data, "title")
            job["company"] = self._safe_get(jsonld_data, "hiringOrganization", "name")
            job["location"] = self._extract_location(jsonld_data)
            job["remote"] = self._is_remote(jsonld_data)
            job["date_posted"] = self._parse_date(self._safe_get(jsonld_data, "datePosted"))
            job["valid_through"] = self._parse_date(self._safe_get(jsonld_data, "validThrough"))
            job["salary"] = self._extract_salary(jsonld_data)
            job["jd_text"] = self._safe_get(jsonld_data, "description")
            job["jd_keywords"] = self._extract_keywords(self._safe_get(jsonld_data, "description"))
        else:
            # Fallback HTML parsing
            soup = BeautifulSoup(html, 'html.parser')
            job["title"] = self._extract_title_html(soup)
            job["company"] = self._extract_company_html(soup)
            job["location"] = self._extract_location_html(soup)
            job["jd_text"] = self._extract_description_html(soup)
            job["jd_keywords"] = self._extract_keywords(job["jd_text"])
            job["date_posted"] = None
            job["remote"] = "remote" in html.lower()
        
        # Ensure required fields
        if not job.get("title") or not job.get("url"):
            return None
        
        # Additional validation: reject obviously non-job titles
        title = job.get("title", "").lower()
        if len(title.split()) < 2:  # Too short to be a job title
            return None
        
        # Reject generic page titles
        generic_patterns = ['homepage', 'home page', 'welcome', 'just a moment', 
                          'sorry, you have been blocked', 'headlines', 'upcoming events']
        if any(pattern in title for pattern in generic_patterns):
            return None
        
        return job
    
    def _safe_get(self, data: Dict, *keys) -> Optional[str]:
        """Safely get nested dictionary values"""
        current = data
        for key in keys:
            if isinstance(current, dict):
                current = current.get(key)
            else:
                return None
            if current is None:
                return None
        return str(current) if current is not None else None
    
    def _extract_location(self, jsonld_data: Dict) -> Optional[str]:
        """Extract location from JSON-LD"""
        job_location = jsonld_data.get("jobLocation")
        if isinstance(job_location, dict):
            address = job_location.get("address")
            if isinstance(address, dict):
                return address.get("addressLocality") or address.get("addressRegion")
            return job_location.get("name")
        return None
    
    def _is_remote(self, jsonld_data: Dict) -> bool:
        """Check if job is remote"""
        job_location = jsonld_data.get("jobLocation")
        if isinstance(job_location, dict):
            return job_location.get("@type") == "Place" and not job_location.get("address")
        return False
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[date]:
        """Parse date string to date object"""
        if not date_str:
            return None
        
        from datetime import date as date_type
        
        # Common date formats to try
        date_formats = [
            "%Y-%m-%d",  # ISO format: 2024-10-26
            "%Y/%m/%d",  # Slash format: 2024/10/26
            "%m/%d/%Y",  # US format: 10/26/2024
            "%d/%m/%Y",  # European format: 26/10/2024
            "%Y-%m-%dT%H:%M:%S",  # ISO with time
            "%Y-%m-%dT%H:%M:%SZ",  # ISO with time and Z
        ]
        
        # Clean the date string
        date_str = date_str.strip()
        
        # Remove timezone info if present
        if 'T' in date_str:
            date_str = date_str.split('T')[0]
        if '+' in date_str:
            date_str = date_str.split('+')[0]
        if 'Z' in date_str:
            date_str = date_str.replace('Z', '')
        
        # Try parsing with different formats
        for fmt in date_formats:
            try:
                parsed_date = datetime.strptime(date_str, fmt).date()
                # Validate: reject future dates (parsing errors)
                today = date_type.today()
                if parsed_date > today:
                    # This is likely a parsing error (e.g., MM/DD/YYYY vs DD/MM/YYYY confusion)
                    # Or the date is actually in the future (unlikely for job postings)
                    print(f"Warning: Parsed future date {parsed_date} from '{date_str}' - rejecting")
                    return None
                return parsed_date
            except ValueError:
                continue
        
        # Try ISO format with timezone handling
        try:
            parsed = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            parsed_date = parsed.date()
            today = date_type.today()
            if parsed_date > today:
                print(f"Warning: Parsed future date {parsed_date} from '{date_str}' - rejecting")
                return None
            return parsed_date
        except:
            pass
        
        return None
    
    def _extract_salary(self, jsonld_data: Dict) -> Optional[Dict[str, Any]]:
        """Extract salary information"""
        base_salary = jsonld_data.get("baseSalary")
        if isinstance(base_salary, dict):
            return {
                "currency": base_salary.get("currency"),
                "value": base_salary.get("value"),
                "min": base_salary.get("value", {}).get("minValue"),
                "max": base_salary.get("value", {}).get("maxValue")
            }
        return None
    
    def _extract_keywords(self, text: Optional[str]) -> List[str]:
        """Extract keywords from job description"""
        if not text:
            return []
        
        # Simple keyword extraction (can be enhanced)
        keywords = []
        # Look for common tech keywords
        tech_keywords = ["python", "javascript", "react", "typescript", "aws", "docker", "kubernetes"]
        text_lower = text.lower()
        for keyword in tech_keywords:
            if keyword in text_lower:
                keywords.append(keyword)
        
        return keywords[:10]  # Limit to 10 keywords
    
    def _extract_source(self, url: str) -> str:
        """Extract source from URL"""
        if "greenhouse.io" in url:
            return "greenhouse"
        elif "lever.co" in url:
            return "lever"
        elif "linkedin.com" in url:
            return "linkedin"
        elif "indeed.com" in url:
            return "indeed"
        else:
            return "other"
    
    def _extract_title_html(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract job title from HTML"""
        # Try common selectors
        selectors = ['h1', '.job-title', '[data-testid*="title"]', 'title']
        for selector in selectors:
            elem = soup.select_one(selector)
            if elem:
                text = elem.get_text(strip=True)
                if text and len(text) < 200:
                    return text
        return None
    
    def _extract_company_html(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract company name from HTML"""
        selectors = ['.company-name', '[data-testid*="company"]', 'a[href*="/company"]']
        for selector in selectors:
            elem = soup.select_one(selector)
            if elem:
                return elem.get_text(strip=True)
        return None
    
    def _extract_location_html(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract location from HTML"""
        selectors = ['.location', '[data-testid*="location"]']
        for selector in selectors:
            elem = soup.select_one(selector)
            if elem:
                return elem.get_text(strip=True)
        return None
    
    def _extract_description_html(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract job description from HTML"""
        # Check for expired/unavailable indicators first
        page_text = soup.get_text().lower()
        unavailable_indicators = [
            'no longer available', 'job is no longer available', 'position has been filled',
            'this job is closed', 'application closed', 'position closed', 'no longer accepting',
            'expired', 'unavailable', 'filled', 'closed position', 'sorry this job'
        ]
        if any(indicator in page_text for indicator in unavailable_indicators):
            return None  # Don't extract description for unavailable jobs
        
        selectors = ['.job-description', '.description', '[data-testid*="description"]', 'main']
        for selector in selectors:
            elem = soup.select_one(selector)
            if elem:
                # Remove script and style tags
                for script in elem(["script", "style"]):
                    script.decompose()
                text = elem.get_text(separator='\n', strip=True)
                if len(text) > 100:
                    return text[:5000]  # Limit length
        return None

