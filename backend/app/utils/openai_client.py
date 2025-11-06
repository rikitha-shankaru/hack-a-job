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

WHAT TO DO:
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

Output ONLY valid JSON with the same structure. Preserve 95%+ of original text. Reorder, don't rewrite."""
        
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

