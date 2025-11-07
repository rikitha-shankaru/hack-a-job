from app.config import settings
import google.generativeai as genai
from typing import Dict, Any, List
import json
import asyncio
import time
import re
from google.api_core import retry

class GeminiClient:
    """Google Gemini API client for AI operations"""
    
    def __init__(self):
        genai.configure(api_key=settings.google_gemini_api_key)
        # Use gemini-2.0-flash (latest stable, fast and efficient)
        self.model = genai.GenerativeModel('gemini-2.0-flash')
    
    def _extract_json_from_text(self, text: str) -> str:
        """Extract JSON from text that may contain conversational text around it"""
        if not text:
            raise ValueError("Empty text provided")
        
        text = text.strip()
        
        # Remove markdown code blocks
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        
        # Try to find JSON object boundaries
        # Look for first { and last }
        first_brace = text.find('{')
        last_brace = text.rfind('}')
        
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            # Extract JSON between braces
            json_candidate = text[first_brace:last_brace + 1]
            # Try to parse it
            try:
                json.loads(json_candidate)
                return json_candidate
            except json.JSONDecodeError:
                pass
        
        # If that didn't work, try to find JSON array boundaries
        first_bracket = text.find('[')
        last_bracket = text.rfind(']')
        
        if first_bracket != -1 and last_bracket != -1 and last_bracket > first_bracket:
            json_candidate = text[first_bracket:last_bracket + 1]
            try:
                json.loads(json_candidate)
                return json_candidate
            except json.JSONDecodeError:
                pass
        
        # Last resort: try parsing the whole text
        return text
    
    async def parse_resume(self, resume_text: str) -> Dict[str, Any]:
        """Parse resume text into structured JSON using Gemini"""
        schema = {
            "type": "object",
            "required": ["summary", "skills", "experience", "projects", "education"],
            "properties": {
                "summary": {"type": "string", "maxLength": 500},
                "skills": {"type": "array", "items": {"type": "string"}},
                "experience": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["company", "title", "start", "bullets"],
                        "properties": {
                            "company": {"type": "string"},
                            "title": {"type": "string"},
                            "start": {"type": "string"},
                            "end": {"type": ["string", "null"]},
                            "bullets": {"type": "array", "items": {"type": "string"}}
                        }
                    }
                },
                "projects": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["name", "bullets"],
                        "properties": {
                            "name": {"type": "string"},
                            "bullets": {"type": "array", "items": {"type": "string"}}
                        }
                    }
                },
                "education": {
                    "type": "array",
                    "items": {"type": "object"}
                }
            }
        }
        
        prompt = f"""Parse this resume text into structured JSON. Extract all sections including summary, skills, experience, projects, and education. Output ONLY valid JSON conforming to this schema:

{json.dumps(schema, indent=2)}

Resume text:
{resume_text}

Output only the JSON object, no other text."""
        
        # Add retry logic for rate limiting
        response = await self._generate_with_retry(prompt)
        
        # Validate response exists
        if not response or not hasattr(response, 'text'):
            raise ValueError("Empty response from Gemini API")
        
        result_text = response.text.strip()
        
        if not result_text:
            raise ValueError("Empty response text from Gemini API")
        
        # Extract JSON from response (may have conversational text)
        try:
            json_text = self._extract_json_from_text(result_text)
            return json.loads(json_text)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON response from Gemini API: {str(e)}\nResponse: {result_text[:500]}")
    
    async def tailor_resume(
        self,
        base_resume_json: Dict[str, Any],
        job_description: str,
        jd_keywords: List[str],
        role_target: str = None,
        level_target: str = None
    ) -> Dict[str, Any]:
        """Tailor resume for a specific job using Gemini AI - preserving human authenticity"""
        prompt = f"""You are helping tailor a resume. CRITICAL: Preserve 95%+ of the original text. Only reorder, don't rewrite.

ABSOLUTE RULES:
1. DO NOT REWRITE: Keep original bullet points 95%+ identical. Only change 1-2 words if absolutely necessary for keyword matching.
2. DO NOT ADD PROJECTS: Keep only the original projects. Do not invent or add new ones.
3. DO NOT CHANGE METRICS: Keep all numbers, percentages, dates exactly as written.
4. DO NOT CHANGE COMPANIES/TITLES: Keep all employer names and job titles exactly as written.
5. REORDER ONLY: Move most relevant experience/projects first. Keep the exact same wording.
6. MINIMAL KEYWORD INSERTION: Add 1-2 job keywords ONLY if they naturally fit. Don't force them.
7. PRESERVE ALL CONTACT INFO: ALWAYS keep name, email, phone, location, and links EXACTLY as in original. NEVER remove or modify these fields.

WHAT TO DO:
- Name, Email, Phone, Location, Links: Keep EXACTLY as in original. NEVER modify or remove.
- Summary: Keep 95%+ of original text. Add 1 keyword max if it fits naturally.
- Experience: Reorder by relevance. Keep bullets 95%+ identical. Limit to 3 bullets per role.
- Skills: Keep original skills. Add only if clearly mentioned in experience. Don't invent.
- Projects: Keep original projects only. Reorder by relevance. Limit to 3 projects, 2 bullets each.
- Education: Keep exactly as is.

ONE PAGE LIMIT: If needed, keep only top 3 experiences and top 3 projects. Don't rewrite to fit.

Base Resume JSON:
{json.dumps(base_resume_json, indent=2)}

Job Description:
{job_description[:1500]}

Job Keywords: {', '.join(jd_keywords[:10])}

Output ONLY valid JSON with the same structure. MUST include name, email, phone, location, and links from original. Preserve 95%+ of original text. Reorder, don't rewrite."""
        
        # Add retry logic for rate limiting
        response = await self._generate_with_retry(prompt)
        
        # Validate response exists
        if not response or not hasattr(response, 'text'):
            raise ValueError("Empty response from Gemini API")
        
        result_text = response.text.strip()
        
        if not result_text:
            raise ValueError("Empty response text from Gemini API")
        
        # Extract JSON from response (may have conversational text)
        try:
            json_text = self._extract_json_from_text(result_text)
            result = json.loads(json_text)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON response from Gemini API: {str(e)}\nResponse: {result_text[:500]}")
        
        # Validate result structure
        if not isinstance(result, dict):
            raise ValueError(f"Invalid resume structure returned from Gemini API. Expected dict, got {type(result)}")
        
        # Validate no fabrication
        self._validate_no_fabrication(base_resume_json, result)
        
        return result
    
    async def generate_cover_letter(
        self,
        resume_json: Dict[str, Any],
        job_description: str,
        company: str,
        jd_keywords: List[str]
    ) -> Dict[str, Any]:
        """Generate authentic, human-sounding cover letter using Gemini"""
        prompt = f"""Write a cover letter that sounds like a real person wrote it. Be direct, specific, and avoid corporate speak.

CRITICAL RULES:
1. SOUND HUMAN: Write like you're emailing a hiring manager directly. Casual but professional.
2. NO CLICHÉS: Avoid "excited to apply", "perfect candidate", "passionate about", "thrilled", "eager". Just be direct.
3. USE REAL FACTS: Only reference actual projects, companies, and metrics from the resume.
4. BE SPECIFIC: Name actual projects, companies, technologies. Don't use vague statements.
5. SHORT SENTENCES: Keep sentences under 20 words. Be clear and direct.
6. NO FLUFF: Cut unnecessary words. Get to the point.

WHAT TO AVOID:
- Corporate jargon ("leverage", "synergy", "utilize")
- Overly formal language ("I am writing to express my interest")
- Generic statements ("I have experience in software development")
- Exclamation points
- Em dashes
- Semicolons

STRUCTURE (200-250 words total):
- Opening (2 sentences): "I saw the [Role] position at [Company]. [One specific reason why it's interesting]."
- Three bullets: Each connects a REAL achievement from resume to job requirement. Use actual project names, companies, metrics.
- Closing (2 sentences): "I'd like to discuss how my experience can help [Company]. I'm available to talk this week."

Resume JSON:
{json.dumps(resume_json, indent=2)}

Company: {company}
Job Description:
{job_description[:800]}

Output JSON:
{{
  "opening": "2 sentences, max 200 chars, direct and specific",
  "mapping": ["bullet 1 with actual project/company name", "bullet 2 with actual project/company name", "bullet 3 with actual project/company name"],
  "closing": "2 sentences, max 150 chars, direct and professional"
}}

Write like a real person, not AI. Be direct, specific, and genuine."""
        
        # Add retry logic for rate limiting
        response = await self._generate_with_retry(prompt)
        
        # Validate response exists
        if not response or not hasattr(response, 'text'):
            raise ValueError("Empty response from Gemini API")
        
        result_text = response.text.strip()
        
        if not result_text:
            raise ValueError("Empty response text from Gemini API")
        
        # Clean up response
        if result_text.startswith("```json"):
            result_text = result_text[7:]
        if result_text.startswith("```"):
            result_text = result_text[3:]
        if result_text.endswith("```"):
            result_text = result_text[:-3]
        result_text = result_text.strip()
        
        # Parse JSON with error handling
        try:
            return json.loads(result_text)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON response from Gemini API: {str(e)}\nResponse: {result_text[:500]}")
    
    async def generate_ai_explanation(
        self,
        base_resume: Dict[str, Any],
        tailored_resume: Dict[str, Any],
        job_description: str,
        jd_keywords: List[str]
    ) -> str:
        """Generate AI explanation of resume changes"""
        prompt = f"""You are an AI resume writing assistant. Analyze the changes made to tailor this resume for a specific job and provide a clear, helpful explanation.

Original Resume Summary:
{json.dumps(base_resume.get('summary', ''), indent=2)}

Tailored Resume Summary:
{json.dumps(tailored_resume.get('summary', ''), indent=2)}

Job Description:
{job_description[:500]}

Job Keywords: {', '.join(jd_keywords[:10])}

Provide a concise explanation (2-3 paragraphs) explaining:
1. What changes were made and why
2. How the resume now better matches the job requirements
3. Key improvements in ATS optimization and keyword matching

Write in a friendly, professional tone. Focus on actionable insights."""
        
        # Add retry logic for rate limiting
        response = await self._generate_with_retry(prompt)
        return response.text.strip()
    
    async def generate_ai_recommendations(
        self,
        resume_json: Dict[str, Any],
        job_description: str
    ) -> List[str]:
        """Generate AI-powered recommendations"""
        prompt = f"""Analyze this resume against a job description and provide 3-5 specific, actionable recommendations for improvement.

Resume:
{json.dumps(resume_json, indent=2)[:1500]}

Job Description:
{job_description[:1000]}

Output a JSON object with a "recommendations" array of strings. Each recommendation should be:
- Specific and actionable
- Focused on improving job match
- Clear and concise (1-2 sentences)

Example: {{"recommendations": ["Add keyword X to skills section", "Emphasize Y experience in summary", ...]}}"""
        
        # Add retry logic for rate limiting
        response = await self._generate_with_retry(prompt)
        
        # Validate response exists
        if not response or not hasattr(response, 'text'):
            raise ValueError("Empty response from Gemini API")
        
        result_text = response.text.strip()
        
        if not result_text:
            raise ValueError("Empty response text from Gemini API")
        
        # Clean up
        if result_text.startswith("```json"):
            result_text = result_text[7:]
        if result_text.startswith("```"):
            result_text = result_text[3:]
        if result_text.endswith("```"):
            result_text = result_text[:-3]
        result_text = result_text.strip()
        
        # Parse JSON with error handling
        try:
            result = json.loads(result_text)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON response from Gemini API: {str(e)}\nResponse: {result_text[:500]}")
        
        if not isinstance(result, dict):
            return []
        
        return result.get("recommendations", [])
    
    async def calculate_job_match_score(
        self,
        resume_json: Dict[str, Any],
        job_description: str,
        jd_keywords: List[str]
    ) -> Dict[str, Any]:
        """Calculate AI-powered job match score"""
        prompt = f"""Analyze how well this resume matches a job posting and provide a detailed match score breakdown.

Resume JSON:
{json.dumps(resume_json, indent=2)[:2000]}

Job Description:
{job_description[:1000]}

Job Keywords: {', '.join(jd_keywords)}

Output JSON with:
- overall_score: integer 0-100
- skills_match: integer 0-100
- experience_match: integer 0-100
- keyword_match: integer 0-100
- explanation: string explaining the score

Be objective and thorough."""
        
        # Add retry logic for rate limiting
        response = await self._generate_with_retry(prompt)
        
        # Validate response exists
        if not response or not hasattr(response, 'text'):
            raise ValueError("Empty response from Gemini API")
        
        result_text = response.text.strip()
        
        if not result_text:
            raise ValueError("Empty response text from Gemini API")
        
        # Clean up
        if result_text.startswith("```json"):
            result_text = result_text[7:]
        if result_text.startswith("```"):
            result_text = result_text[3:]
        if result_text.endswith("```"):
            result_text = result_text[:-3]
        result_text = result_text.strip()
        
        # Parse JSON with error handling
        try:
            return json.loads(result_text)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON response from Gemini API: {str(e)}\nResponse: {result_text[:500]}")
    
    async def answer_application_question(
        self,
        question: str,
        resume_json: Dict[str, Any],
        job_description: str
    ) -> str:
        """Use Gemini to intelligently answer application form questions"""
        prompt = f"""You are helping fill out a job application form. Answer this question based on the candidate's resume and the job description.

Question: {question}

Resume:
{json.dumps(resume_json, indent=2)[:2000]}

Job Description:
{job_description[:1000]}

Provide a concise, professional answer (1-3 sentences) that:
- Directly addresses the question
- Uses relevant information from the resume
- Aligns with the job requirements
- Is truthful and accurate

Answer:"""
        
        # Add retry logic for rate limiting
        response = await self._generate_with_retry(prompt)
        
        # Validate response exists
        if not response or not hasattr(response, 'text'):
            raise ValueError("Empty response from Gemini API")
        
        result_text = response.text.strip()
        
        if not result_text:
            raise ValueError("Empty response text from Gemini API")
        
        return result_text
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding vector"""
        # Note: Gemini doesn't have a direct embedding API
        # For now, we'll use Google's text-embedding-004 or similar
        # Fallback: return a placeholder vector (in production, use Google's embedding API)
        # For MVP, we can skip embeddings or use a simple hash-based approach
        import hashlib
        hash_obj = hashlib.sha256(text.encode())
        # Generate a 1536-dim vector from hash (simplified)
        hash_int = int(hash_obj.hexdigest()[:8], 16)
        return [(hash_int % 1000) / 1000.0 for _ in range(1536)]
    
    async def _generate_with_retry(self, prompt: str, max_retries: int = 3):
        """Generate content with retry logic for rate limiting"""
        for attempt in range(max_retries):
            try:
                response = self.model.generate_content(prompt)
                return response
            except Exception as e:
                error_str = str(e)
                # Check if it's a 429 rate limit error
                if "429" in error_str or "Resource exhausted" in error_str or "quota" in error_str.lower():
                    if attempt < max_retries - 1:
                        # Exponential backoff: wait 2^attempt seconds
                        wait_time = (2 ** attempt) * 2  # 2, 4, 8 seconds
                        print(f"⚠️  Rate limit hit. Waiting {wait_time} seconds before retry {attempt + 1}/{max_retries}...")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        raise Exception(f"Rate limit exceeded after {max_retries} attempts. Please wait a few minutes and try again.")
                else:
                    # Not a rate limit error, re-raise
                    raise e
        raise Exception("Failed to generate content after retries")
    
    def _validate_no_fabrication(
        self,
        base: Dict[str, Any],
        tailored: Dict[str, Any]
    ):
        """Validate that tailored resume doesn't invent facts - STRICT validation"""
        # Handle empty experience lists
        base_experience = base.get("experience", [])
        tailored_experience = tailored.get("experience", [])
        
        if not base_experience and tailored_experience:
            raise ValueError("Cannot add experience when base resume has none")
        
        if not isinstance(base_experience, list) or not isinstance(tailored_experience, list):
            raise ValueError("Experience must be a list")
        
        # Extract companies and titles, filtering out None values
        base_companies = {exp.get("company") for exp in base_experience if exp.get("company")}
        base_titles = {exp.get("title") for exp in base_experience if exp.get("title")}
        
        tailored_companies = {exp.get("company") for exp in tailored_experience if exp.get("company")}
        tailored_titles = {exp.get("title") for exp in tailored_experience if exp.get("title")}
        
        # Check for new companies (excluding None/empty strings)
        new_companies = tailored_companies - base_companies
        if new_companies:
            raise ValueError(f"Cannot add new companies to resume: {new_companies}")
        
        # Check for new titles (excluding None/empty strings)
        new_titles = tailored_titles - base_titles
        if new_titles:
            raise ValueError(f"Cannot add new job titles to resume: {new_titles}")
        
        # Validate projects - NO NEW PROJECTS ALLOWED
        base_projects = base.get("projects", [])
        tailored_projects = tailored.get("projects", [])
        
        if not isinstance(base_projects, list) or not isinstance(tailored_projects, list):
            raise ValueError("Projects must be a list")
        
        # Extract project names
        base_project_names = {proj.get("name") for proj in base_projects if proj.get("name")}
        tailored_project_names = {proj.get("name") for proj in tailored_projects if proj.get("name")}
        
        # Check for new projects
        new_projects = tailored_project_names - base_project_names
        if new_projects:
            raise ValueError(f"Cannot add new projects to resume: {new_projects}")

