from app.config import settings
from openai import OpenAI
from typing import Dict, Any, List
import json

class OpenAIClient:
    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key)
    
    async def parse_resume(self, resume_text: str) -> Dict[str, Any]:
        """Parse resume text into structured JSON"""
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
        
        response = self.client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {
                    "role": "system",
                    "content": "You are a resume parser. Extract structured data from resume text. Output only valid JSON conforming to the provided schema."
                },
                {
                    "role": "user",
                    "content": f"Parse this resume:\n\n{resume_text}"
                }
            ],
            response_format={"type": "json_object"},
            temperature=0.1
        )
        
        result = json.loads(response.choices[0].message.content)
        return result
    
    async def tailor_resume(
        self,
        base_resume_json: Dict[str, Any],
        job_description: str,
        jd_keywords: List[str],
        role_target: str = None,
        level_target: str = None
    ) -> Dict[str, Any]:
        """Tailor resume for a specific job using AI"""
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
        
        system_prompt = """You are an expert AI resume writer specializing in ATS optimization and job matching. Your task is to intelligently rewrite resumes for specific job postings while maintaining complete factual accuracy.

Key principles:
1. Truth preservation: Never invent employers, titles, dates, or metrics. Only rephrase and reorder existing content.
2. Strategic alignment: Match the job description's language, skills, and requirements.
3. ATS optimization: Use keywords naturally while maintaining readability.
4. Impact highlighting: Surface metrics and achievements that demonstrate value.
5. Relevance prioritization: Reorder sections to emphasize most relevant experience first.

Analyze the job description to identify:
- Must-have skills and technologies
- Preferred qualifications
- Key responsibilities
- Industry-specific terminology

Then strategically tailor the resume by:
- Rephrasing bullet points to match job language
- Reordering experiences to highlight relevant roles first
- Adjusting skills section to prioritize job-relevant skills
- Enhancing summary to align with job requirements
- Maintaining all factual information exactly as provided

Output strictly valid JSON conforming to the schema. Do not exceed bullet count by more than +1 per role unless absolutely necessary for clarity."""
        
        user_content = f"""
Base Resume JSON:
{json.dumps(base_resume_json, indent=2)}

Job Description:
{job_description}

Job Keywords: {', '.join(jd_keywords)}
Role Target: {role_target or 'N/A'}
Level Target: {level_target or 'N/A'}

Using AI analysis, intelligently tailor this resume to maximize match with the job posting while preserving all factual information.
"""
        
        response = self.client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            response_format={"type": "json_object"},
            temperature=0.3
        )
        
        result = json.loads(response.choices[0].message.content)
        
        # Validate that we didn't invent facts
        self._validate_no_fabrication(base_resume_json, result)
        
        return result
    
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
        
        response = self.client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert AI resume writing assistant. Provide clear, helpful explanations of resume tailoring changes."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        return response.choices[0].message.content
    
    async def generate_ai_recommendations(
        self,
        resume_json: Dict[str, Any],
        job_description: str
    ) -> List[str]:
        """Generate AI-powered recommendations for resume improvements"""
        prompt = f"""Analyze this resume against a job description and provide 3-5 specific, actionable recommendations for improvement.

Resume:
{json.dumps(resume_json, indent=2)[:1500]}

Job Description:
{job_description[:1000]}

Provide recommendations as a JSON array of strings. Each recommendation should be:
- Specific and actionable
- Focused on improving job match
- Clear and concise (1-2 sentences)

Example format: ["Add keyword X to skills section", "Emphasize Y experience in summary", ...]"""
        
        response = self.client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {
                    "role": "system",
                    "content": "You are an AI resume optimization expert. Provide specific, actionable recommendations."
                },
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.6
        )
        
        result = json.loads(response.choices[0].message.content)
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

Provide a JSON object with:
- overall_score: integer 0-100
- skills_match: integer 0-100
- experience_match: integer 0-100
- keyword_match: integer 0-100
- explanation: string explaining the score

Be objective and thorough in your analysis."""
        
        response = self.client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {
                    "role": "system",
                    "content": "You are an AI job matching analyst. Provide accurate, objective match scores."
                },
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.3
        )
        
        return json.loads(response.choices[0].message.content)
    
    async def generate_cover_letter(
        self,
        resume_json: Dict[str, Any],
        job_description: str,
        company: str,
        jd_keywords: List[str]
    ) -> Dict[str, Any]:
        """Generate cover letter"""
        schema = {
            "type": "object",
            "required": ["opening", "mapping", "closing"],
            "properties": {
                "opening": {"type": "string", "maxLength": 300},
                "mapping": {
                    "type": "array",
                    "items": {"type": "string"},
                    "maxItems": 3
                },
                "closing": {"type": "string", "maxLength": 200}
            }
        }
        
        system_prompt = """Write a concise cover letter from structured facts only: 1–2 sentence opening referencing the company/team, three bullets mapping candidate impact to JD must-haves, and a short closing with availability and links. No fluff. 200–250 words total. Output JSON per schema."""
        
        user_content = f"""
Resume JSON:
{json.dumps(resume_json, indent=2)}

Company: {company}
Job Description:
{job_description}

Job Keywords: {', '.join(jd_keywords)}

Generate a cover letter.
"""
        
        response = self.client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            response_format={"type": "json_object"},
            temperature=0.5
        )
        
        return json.loads(response.choices[0].message.content)
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding vector for text"""
        response = self.client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding
    
    def _validate_no_fabrication(
        self,
        base: Dict[str, Any],
        tailored: Dict[str, Any]
    ):
        """Validate that tailored resume doesn't invent facts"""
        # Extract companies and titles from base
        base_companies = {exp.get("company") for exp in base.get("experience", [])}
        base_titles = {exp.get("title") for exp in base.get("experience", [])}
        
        # Check tailored resume
        tailored_companies = {exp.get("company") for exp in tailored.get("experience", [])}
        tailored_titles = {exp.get("title") for exp in tailored.get("experience", [])}
        
        # Ensure no new companies or titles were added
        if tailored_companies - base_companies:
            raise ValueError("Cannot add new companies to resume")
        if tailored_titles - base_titles:
            raise ValueError("Cannot add new titles to resume")

