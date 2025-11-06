from app.config import settings
import google.generativeai as genai
from typing import Dict, Any, List
import json
import asyncio
import time
from google.api_core import retry

class GeminiClient:
    """Google Gemini API client for AI operations"""
    
    def __init__(self):
        genai.configure(api_key=settings.google_gemini_api_key)
        # Use gemini-2.0-flash (latest stable, fast and efficient)
        self.model = genai.GenerativeModel('gemini-2.0-flash')
    
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
        result_text = response.text.strip()
        
        # Clean up response (remove markdown code blocks if present)
        if result_text.startswith("```json"):
            result_text = result_text[7:]
        if result_text.startswith("```"):
            result_text = result_text[3:]
        if result_text.endswith("```"):
            result_text = result_text[:-3]
        result_text = result_text.strip()
        
        return json.loads(result_text)
    
    async def tailor_resume(
        self,
        base_resume_json: Dict[str, Any],
        job_description: str,
        jd_keywords: List[str],
        role_target: str = None,
        level_target: str = None
    ) -> Dict[str, Any]:
        """Tailor resume for a specific job using Gemini AI"""
        prompt = f"""You are an expert AI resume writer specializing in ATS optimization and job matching. Intelligently rewrite this resume for a specific job posting while maintaining complete factual accuracy.

Key principles:
1. Truth preservation: Never invent employers, titles, dates, or metrics. Only rephrase and reorder existing content.
2. Strategic alignment: Match the job description's language, skills, and requirements.
3. ATS optimization: Use keywords naturally while maintaining readability.
4. Impact highlighting: Surface metrics and achievements that demonstrate value.
5. Relevance prioritization: Reorder sections to emphasize most relevant experience first.

Base Resume JSON:
{json.dumps(base_resume_json, indent=2)}

Job Description:
{job_description}

Job Keywords: {', '.join(jd_keywords)}
Role Target: {role_target or 'N/A'}
Level Target: {level_target or 'N/A'}

Output ONLY valid JSON with the same structure as the base resume. Do not add new companies, titles, or dates. Only rephrase and reorder."""
        
        # Add retry logic for rate limiting
        response = await self._generate_with_retry(prompt)
        result_text = response.text.strip()
        
        # Clean up response
        if result_text.startswith("```json"):
            result_text = result_text[7:]
        if result_text.startswith("```"):
            result_text = result_text[3:]
        if result_text.endswith("```"):
            result_text = result_text[:-3]
        result_text = result_text.strip()
        
        result = json.loads(result_text)
        
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
        """Generate cover letter using Gemini"""
        prompt = f"""Write a concise cover letter from structured facts only: 1–2 sentence opening referencing the company/team, three bullets mapping candidate impact to JD must-haves, and a short closing with availability and links. No fluff. 200–250 words total.

Resume JSON:
{json.dumps(resume_json, indent=2)}

Company: {company}
Job Description:
{job_description[:1000]}

Job Keywords: {', '.join(jd_keywords)}

Output JSON with this structure:
{{
  "opening": "string (max 300 chars)",
  "mapping": ["bullet 1", "bullet 2", "bullet 3"],
  "closing": "string (max 200 chars)"
}}"""
        
        # Add retry logic for rate limiting
        response = await self._generate_with_retry(prompt)
        result_text = response.text.strip()
        
        # Clean up response
        if result_text.startswith("```json"):
            result_text = result_text[7:]
        if result_text.startswith("```"):
            result_text = result_text[3:]
        if result_text.endswith("```"):
            result_text = result_text[:-3]
        result_text = result_text.strip()
        
        return json.loads(result_text)
    
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
        result_text = response.text.strip()
        
        # Clean up
        if result_text.startswith("```json"):
            result_text = result_text[7:]
        if result_text.startswith("```"):
            result_text = result_text[3:]
        if result_text.endswith("```"):
            result_text = result_text[:-3]
        result_text = result_text.strip()
        
        result = json.loads(result_text)
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
        result_text = response.text.strip()
        
        # Clean up
        if result_text.startswith("```json"):
            result_text = result_text[7:]
        if result_text.startswith("```"):
            result_text = result_text[3:]
        if result_text.endswith("```"):
            result_text = result_text[:-3]
        result_text = result_text.strip()
        
        return json.loads(result_text)
    
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
        return response.text.strip()
    
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
        """Validate that tailored resume doesn't invent facts"""
        base_companies = {exp.get("company") for exp in base.get("experience", [])}
        base_titles = {exp.get("title") for exp in base.get("experience", [])}
        
        tailored_companies = {exp.get("company") for exp in tailored.get("experience", [])}
        tailored_titles = {exp.get("title") for exp in tailored.get("experience", [])}
        
        if tailored_companies - base_companies:
            raise ValueError("Cannot add new companies to resume")
        if tailored_titles - base_titles:
            raise ValueError("Cannot add new titles to resume")

