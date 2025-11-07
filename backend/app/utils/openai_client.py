from app.config import settings
from openai import AsyncOpenAI
from typing import Dict, Any, List
import json
import asyncio

class OpenAIClient:
    """OpenAI client for resume tailoring and cover letter generation"""
    
    def __init__(self):
        if not settings.openai_api_key:
            raise ValueError("OpenAI API key not configured")
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = "gpt-4o-mini"  # Fast and cost-effective
    
    async def tailor_resume(
        self,
        base_resume_json: Dict[str, Any],
        job_description: str,
        jd_keywords: List[str],
        role_target: str = None,
        level_target: str = None
    ) -> Dict[str, Any]:
        """Tailor resume for a specific job using OpenAI - preserving human authenticity"""
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
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a professional resume editor. Output only valid JSON, no other text."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # Low temperature for consistency
                response_format={"type": "json_object"}
            )
            
            result_text = response.choices[0].message.content.strip()
            
            if not result_text:
                raise ValueError("Empty response from OpenAI API")
            
            # Parse JSON
            try:
                result = json.loads(result_text)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON response from OpenAI API: {str(e)}\nResponse: {result_text[:500]}")
            
            # Validate result structure
            if not isinstance(result, dict):
                raise ValueError(f"Invalid resume structure returned from OpenAI API. Expected dict, got {type(result)}")
            
            return result
            
        except Exception as e:
            raise ValueError(f"OpenAI API error: {str(e)}")
    
    async def generate_cover_letter(
        self,
        resume_json: Dict[str, Any],
        job_description: str,
        company: str,
        jd_keywords: List[str]
    ) -> Dict[str, Any]:
        """Generate authentic, human-sounding cover letter using OpenAI"""
        # Extract key achievements and projects from resume for context
        experience = resume_json.get("experience", [])
        projects = resume_json.get("projects", [])
        skills = resume_json.get("skills", [])
        
        # Build context about user's actual experience
        experience_summary = []
        for exp in experience[:2]:  # Top 2 experiences
            company_name = exp.get("company", "")
            title = exp.get("title", "")
            bullets = exp.get("bullets", [])[:2]  # Top 2 bullets
            if company_name and title:
                exp_text = f"{title} at {company_name}: {', '.join(bullets[:2])}"
                experience_summary.append(exp_text)
        
        projects_summary = []
        for proj in projects[:2]:  # Top 2 projects
            name = proj.get("name", "")
            bullets = proj.get("bullets", [])[:1]  # Top bullet
            if name:
                projects_summary.append(f"{name}: {bullets[0] if bullets else ''}")
        
        prompt = f"""Write a cover letter that sounds like a real person wrote it. Be direct, specific, and avoid corporate speak.

CRITICAL RULES:
1. SOUND HUMAN: Write like you're emailing a hiring manager directly. Casual but professional. Use "I" and "my" naturally.
2. NO CLICHÉS: Avoid "excited to apply", "perfect candidate", "passionate about", "thrilled", "eager", "I believe", "I think". Just state facts directly.
3. USE REAL FACTS ONLY: Reference ONLY actual projects, companies, technologies, and metrics from the resume below. Never invent or assume.
4. BE SPECIFIC: Name actual projects, companies, technologies. Use exact names from the resume. Don't use vague statements.
5. SHORT SENTENCES: Keep sentences under 15 words. Be clear and direct. One idea per sentence.
6. NO FLUFF: Cut unnecessary words. Get to the point immediately.
7. ACTIVE VOICE: Use active voice. "I built X" not "X was built by me".

WHAT TO AVOID:
- Corporate jargon ("leverage", "synergy", "utilize", "implement", "facilitate")
- Overly formal language ("I am writing to express my interest", "I would like to")
- Generic statements ("I have experience in software development" - too vague)
- Exclamation points (never use them)
- Em dashes (use periods or commas instead)
- Semicolons (use periods instead)
- Phrases like "I believe", "I think", "I feel" (just state facts)

STRUCTURE (200-250 words total):
- Opening (2 sentences, max 200 chars): "I saw the [Role] position at [Company]. [One SPECIFIC reason from job description why it's interesting - mention actual technology or project type]."
- Three bullets (each 1-2 sentences, max 100 chars each): Each connects a REAL achievement from resume to job requirement. Use actual project names, company names, technologies, and metrics. Format: "At [Company], I [specific action] that [specific result/metric]."
- Closing (2 sentences, max 150 chars): "I'd like to discuss how my experience with [specific technology/project from resume] can help [Company]. I'm available to talk this week."

Resume Context:
Experience: {', '.join(experience_summary)}
Projects: {', '.join(projects_summary)}
Skills: {', '.join(skills[:10])}

Company: {company}
Job Description (key requirements):
{job_description[:1000]}

Job Keywords: {', '.join(jd_keywords[:15])}

Output JSON (ONLY output valid JSON, no other text):
{{
  "opening": "2 sentences, max 200 chars, direct and specific. Mention actual technology or project type from job description.",
  "mapping": [
    "bullet 1: Connect REAL experience to job requirement. Use actual company/project name and metric.",
    "bullet 2: Connect REAL experience to job requirement. Use actual company/project name and metric.",
    "bullet 3: Connect REAL experience to job requirement. Use actual company/project name and metric."
  ],
  "closing": "2 sentences, max 150 chars, direct and professional. Mention specific technology/project from resume."
}}

CRITICAL: Write like a real person wrote this, not AI. Be direct, specific, and genuine. Use ONLY facts from the resume. Never invent anything."""
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a professional cover letter writer. Output only valid JSON, no other text."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,  # Slightly higher for more natural language
                response_format={"type": "json_object"}
            )
            
            result_text = response.choices[0].message.content.strip()
            
            if not result_text:
                raise ValueError("Empty response from OpenAI API")
            
            # Parse JSON
            try:
                result = json.loads(result_text)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON response from OpenAI API: {str(e)}\nResponse: {result_text[:500]}")
            
            return result
            
        except Exception as e:
            raise ValueError(f"OpenAI API error: {str(e)}")

