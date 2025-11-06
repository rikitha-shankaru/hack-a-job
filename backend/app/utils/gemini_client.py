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
        
        # Validate response exists
        if not response or not hasattr(response, 'text'):
            raise ValueError("Empty response from Gemini API")
        
        result_text = response.text.strip()
        
        if not result_text:
            raise ValueError("Empty response text from Gemini API")
        
        # Clean up response (remove markdown code blocks if present)
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
    
    async def tailor_resume(
        self,
        base_resume_json: Dict[str, Any],
        job_description: str,
        jd_keywords: List[str],
        role_target: str = None,
        level_target: str = None
    ) -> Dict[str, Any]:
        """Tailor resume for a specific job using Gemini AI - preserving human authenticity"""
        prompt = f"""You are a professional resume editor helping a candidate tailor their resume for a specific job. Your goal is MINIMAL, STRATEGIC editing that preserves 90%+ of the original human-written content.

CRITICAL RULES FOR AUTHENTICITY:
1. PRESERVE ORIGINAL VOICE: Keep the candidate's original writing style, phrasing, and tone. Do NOT rewrite everything. Only make strategic tweaks.
2. MINIMAL CHANGES: Change only what's necessary. If a bullet point already works, keep it 95% the same. Only edit if it significantly improves job match.
3. TRUTH PRESERVATION: Never invent employers, titles, dates, metrics, or achievements. Only work with what exists.
4. STRATEGIC KEYWORD INSERTION: Naturally weave in 2-3 job-relevant keywords per section, but keep original phrasing intact.
5. REORDERING OVER REWRITING: Prioritize reordering bullets/experiences over rewriting them. Move most relevant items first.
6. PRESERVE METRICS: Keep all original numbers, percentages, and achievements exactly as written.
7. NATURAL LANGUAGE: All changes must sound like a human wrote them, not AI. Avoid corporate jargon or overly polished language.

WRITING STYLE RULES (CRITICAL):
- Use clear, simple language
- Use short, impactful sentences
- Use active voice. Avoid passive voice
- Focus on practical, actionable insights
- Use data and examples to support claims
- Avoid em dashes anywhere. Use only commas, periods, or other standard punctuation
- Avoid constructions like "not just this, but also this"
- Avoid metaphors and clichés
- Avoid generalizations
- Avoid common setup language like "in conclusion", "in closing", etc.
- Avoid unnecessary adjectives and adverbs
- Avoid semicolons
- Review your response and ensure no em dashes

EDITING APPROACH:
- Summary: Add 1-2 job-relevant keywords, but keep 90% of original text. Keep it concise (2-3 sentences max).
- Experience bullets: Only modify if missing critical keywords. Keep original achievements/metrics. Limit to 2-3 most relevant bullets per role.
- Skills: Add missing job-relevant skills IF they genuinely exist in experience. Don't fabricate.
- Projects: You MAY add 1-2 new relevant projects that align with the job requirements. These should be realistic, feasible projects that demonstrate skills mentioned in the job description. Format: name and 2-3 bullets describing the project. Only add if it significantly strengthens the resume match.
- Reorder: Move most relevant experience/projects first, but keep content unchanged.
- ONE PAGE LIMIT: Ensure the resume fits on ONE page. Prioritize most relevant content. If needed, reduce bullets or combine similar points.

Base Resume JSON:
{json.dumps(base_resume_json, indent=2)}

Job Description:
{job_description}

Job Keywords: {', '.join(jd_keywords)}
Role Target: {role_target or 'N/A'}
Level Target: {level_target or 'N/A'}

Output ONLY valid JSON with the same structure. Preserve 90%+ of original content. Make minimal, strategic edits that sound human-written. Follow the writing style rules above."""
        
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
            result = json.loads(result_text)
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
        prompt = f"""Write a professional but authentic cover letter that sounds like a real person wrote it, not AI. Use natural, conversational language while staying professional.

CRITICAL RULES FOR AUTHENTICITY:
1. HUMAN VOICE: Write like a real candidate would. Natural, genuine, not overly polished or corporate-sounding
2. USE ACTUAL FACTS: Only reference real experiences, achievements, and skills from the resume
3. SPECIFIC EXAMPLES: Reference specific projects, metrics, or experiences from the resume
4. CONVERSATIONAL TONE: Sound like you're talking to a hiring manager, not a robot
5. AVOID CLICHÉS: No "I'm excited to apply" or "I'm the perfect candidate". Be genuine
6. SHOW, DON'T TELL: Use specific examples from resume rather than generic statements

WRITING STYLE RULES (CRITICAL):
- Use clear, simple language
- Use short, impactful sentences
- Use active voice. Avoid passive voice
- Focus on practical, actionable insights
- Use data and examples to support claims
- Avoid em dashes anywhere. Use only commas, periods, or other standard punctuation
- Avoid constructions like "not just this, but also this"
- Avoid metaphors and clichés
- Avoid generalizations
- Avoid common setup language like "in conclusion", "in closing", etc.
- Avoid unnecessary adjectives and adverbs
- Avoid semicolons
- Review your response and ensure no em dashes

STRUCTURE:
- Opening (2-3 sentences): Reference the specific role/company naturally. Mention why you're interested. Be specific, not generic.
- Three mapping bullets: Connect your REAL achievements from resume to job requirements. Use actual metrics/projects.
- Closing (2-3 sentences): Professional but warm closing. Mention availability naturally.

Keep it 200-300 words total. Sound human, not AI-generated.

Resume JSON:
{json.dumps(resume_json, indent=2)}

Company: {company}
Job Description:
{job_description[:1000]}

Job Keywords: {', '.join(jd_keywords)}

Output JSON with this structure:
{{
  "opening": "string (2-3 sentences, max 400 chars, natural and specific)",
  "mapping": ["bullet 1 (specific achievement from resume)", "bullet 2 (specific achievement)", "bullet 3 (specific achievement)"],
  "closing": "string (2-3 sentences, max 300 chars, warm and professional)"
}}

Write like a real person would. Authentic, specific, and genuine. Follow the writing style rules above."""
        
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
        """Validate that tailored resume doesn't invent facts"""
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
            raise ValueError(f"Cannot add new titles to resume: {new_titles}")

