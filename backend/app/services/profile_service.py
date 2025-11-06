from app.config import settings
from app.utils.gemini_client import GeminiClient
from app.utils.resume_parser import ResumeParser
from app.utils.pdf_parser import PDFParser
from app.utils.pdf_to_latex import PDFToLaTeXConverter
from typing import Dict, Any, Optional
import json
import os

class ProfileService:
    def __init__(self):
        self.gemini_client = GeminiClient()
        self.parser = ResumeParser()
        self.pdf_parser = PDFParser()
        self.pdf_to_latex = PDFToLaTeXConverter()
    
    async def parse_resume(
        self,
        resume_text: Optional[str] = None,
        resume_url: Optional[str] = None,
        resume_pdf_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Parse resume text or PDF and extract structured data"""
        resume_pdf_url = None
        resume_latex_template = None
        
        if resume_pdf_path and os.path.exists(resume_pdf_path):
            # Parse PDF
            pdf_data = await self.pdf_parser.parse_pdf(resume_pdf_path)
            resume_text = pdf_data["text"]
            resume_pdf_url = f"/uploads/resumes/{os.path.basename(resume_pdf_path)}"
            
            # Parse resume JSON first (needed for LaTeX conversion)
            # We'll parse it here temporarily to get structure
            temp_resume_json = await self.gemini_client.parse_resume(resume_text)
            
            # Convert PDF to LaTeX code preserving exact formatting
            try:
                resume_latex_template = await self.pdf_to_latex.convert_pdf_to_latex(
                    pdf_path=resume_pdf_path,
                    resume_json=temp_resume_json
                )
            except Exception as e:
                print(f"Failed to convert PDF to LaTeX: {e}, using fallback")
                # Fallback to basic template generation
                resume_latex_template = await self._generate_latex_template_from_pdf(pdf_data)
        
        elif resume_url:
            # Fetch resume from URL
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get(resume_url)
                resume_text = response.text
        
        if not resume_text:
            raise ValueError("Either resumeText, resumeFileUrl, or resumeFile must be provided")
        
        # Parse resume using Gemini for structured extraction
        # If we already parsed it for LaTeX conversion, reuse it
        if 'temp_resume_json' in locals() and temp_resume_json:
            structured_resume = temp_resume_json
        else:
            structured_resume = await self.gemini_client.parse_resume(resume_text)
        
        # Extract skills, metrics, links
        skills = structured_resume.get("skills", [])
        metrics = self._extract_metrics(structured_resume)
        links = self._extract_links(structured_resume)
        
        # Generate embedding vector (using Gemini or fallback)
        resume_vector = await self.gemini_client.generate_embedding(
            json.dumps(structured_resume)
        )
        
        return {
            "resume_json": structured_resume,
            "resume_pdf_url": resume_pdf_url,
            "resume_latex_template": resume_latex_template,
            "skills": skills,
            "metrics": metrics,
            "links": links,
            "resume_vector": resume_vector
        }
    
    async def _generate_latex_template_from_pdf(self, pdf_data: Dict[str, Any]) -> str:
        """Generate a basic LaTeX template from PDF structure analysis"""
        # This is a simplified version - in production, you'd want more sophisticated
        # analysis to preserve exact formatting
        structure = pdf_data.get("structure", {})
        sections = structure.get("sections", [])
        
        # Create basic LaTeX template
        template = r"""\documentclass[11pt,a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage[margin=0.75in]{geometry}
\usepackage{enumitem}
\usepackage{titlesec}

\pagestyle{empty}
\setlength{\parindent}{0pt}
\setlength{\parskip}{6pt}

\titleformat{\section}{\large\bfseries\uppercase}{}{0em}{}[\titlerule]
\titlespacing*{\section}{0pt}{12pt}{6pt}

\begin{document}
"""
        
        # Add sections based on detected structure
        for section in sections:
            section_name = section.get("name", "")
            template += f"\\section{{{section_name}}}\n"
            template += "${" + section_name.lower().replace(" ", "_") + "}\n\n"
        
        template += "\\end{document}"
        
        return template
    
    def _extract_metrics(self, resume_json: Dict[str, Any]) -> Dict[str, Any]:
        """Extract quantitative metrics from resume"""
        metrics = {}
        for exp in resume_json.get("experience", []):
            bullets = exp.get("bullets", [])
            for bullet in bullets:
                # Look for numbers and percentages
                import re
                numbers = re.findall(r'\d+%?|\$\d+[KM]?', bullet)
                if numbers:
                    metrics[exp.get("company", "")] = numbers
        return metrics
    
    def _extract_links(self, resume_json: Dict[str, Any]) -> Dict[str, str]:
        """Extract links from resume"""
        links = {}
        # Extract from projects, experience, or dedicated links section
        if "links" in resume_json:
            links = resume_json["links"]
        return links

