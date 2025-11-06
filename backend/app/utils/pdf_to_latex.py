from app.config import settings
from app.utils.gemini_client import GeminiClient
from app.utils.openai_client import OpenAIClient
from app.utils.pdf_parser import PDFParser
from typing import Optional, Dict, Any
import json

class PDFToLaTeXConverter:
    """Convert PDF resume to LaTeX code preserving exact formatting"""
    
    def __init__(self):
        self.pdf_parser = PDFParser()
        self.gemini_client = GeminiClient()
        # Try to initialize OpenAI, fallback to Gemini
        try:
            self.openai_client = OpenAIClient()
            self.use_openai = True
        except:
            self.openai_client = None
            self.use_openai = False
    
    async def convert_pdf_to_latex(
        self,
        pdf_path: str,
        resume_json: Dict[str, Any]
    ) -> str:
        """
        Convert PDF resume to LaTeX code using AI, preserving exact formatting.
        The LaTeX will have placeholders for dynamic content that can be replaced during tailoring.
        """
        # Parse PDF to get text and structure
        pdf_data = await self.pdf_parser.parse_pdf(pdf_path)
        pdf_text = pdf_data["text"]
        structure = pdf_data.get("structure", {})
        
        # Use AI to convert PDF to LaTeX
        if self.use_openai and self.openai_client:
            try:
                latex_code = await self._convert_with_openai(pdf_text, structure, resume_json)
            except Exception as e:
                print(f"OpenAI conversion failed, using Gemini: {e}")
                latex_code = await self._convert_with_gemini(pdf_text, structure, resume_json)
        else:
            latex_code = await self._convert_with_gemini(pdf_text, structure, resume_json)
        
        return latex_code
    
    async def _convert_with_openai(
        self,
        pdf_text: str,
        structure: Dict[str, Any],
        resume_json: Dict[str, Any]
    ) -> str:
        """Convert PDF to LaTeX using OpenAI"""
        prompt = f"""Convert this resume PDF text into LaTeX code that preserves the EXACT formatting, fonts, spacing, margins, and layout.

CRITICAL REQUIREMENTS:
1. Preserve ALL formatting: fonts, sizes, spacing, margins, indentation, alignment
2. Use placeholders for dynamic content:
   - ${{name}} for name
   - ${{email}} for email
   - ${{phone}} for phone
   - ${{location}} for location
   - ${{summary}} for summary text
   - ${{experience}} for experience section (will be replaced with formatted experience)
   - ${{education}} for education section (will be replaced with formatted education)
   - ${{skills}} for skills section (will be replaced with formatted skills)
   - ${{projects}} for projects section (will be replaced with formatted projects)
3. Keep ALL LaTeX packages, custom commands, and style definitions
4. Preserve exact spacing, margins, and layout
5. Use proper LaTeX commands for formatting (textbf, textit, etc.)

PDF Text:
{pdf_text[:3000]}

Resume Structure (for reference):
{json.dumps(resume_json, indent=2)[:1000]}

Output ONLY the LaTeX code, no explanations. Start with \\documentclass and end with \\end{{document}}."""
        
        response = await self.openai_client.client.chat.completions.create(
            model=self.openai_client.model,
            messages=[
                {"role": "system", "content": "You are a LaTeX expert. Output only valid LaTeX code, no explanations."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        
        latex_code = response.choices[0].message.content.strip()
        
        # Clean up if wrapped in code blocks
        if latex_code.startswith("```latex"):
            latex_code = latex_code[8:]
        elif latex_code.startswith("```"):
            latex_code = latex_code[3:]
        if latex_code.endswith("```"):
            latex_code = latex_code[:-3]
        
        return latex_code.strip()
    
    async def _convert_with_gemini(
        self,
        pdf_text: str,
        structure: Dict[str, Any],
        resume_json: Dict[str, Any]
    ) -> str:
        """Convert PDF to LaTeX using Gemini"""
        prompt = f"""Convert this resume PDF text into LaTeX code that preserves the EXACT formatting, fonts, spacing, margins, and layout.

CRITICAL REQUIREMENTS:
1. Preserve ALL formatting: fonts, sizes, spacing, margins, indentation, alignment
2. Use placeholders for dynamic content:
   - ${{name}} for name
   - ${{email}} for email
   - ${{phone}} for phone
   - ${{location}} for location
   - ${{summary}} for summary text
   - ${{experience}} for experience section (will be replaced with formatted experience)
   - ${{education}} for education section (will be replaced with formatted education)
   - ${{skills}} for skills section (will be replaced with formatted skills)
   - ${{projects}} for projects section (will be replaced with formatted projects)
3. Keep ALL LaTeX packages, custom commands, and style definitions
4. Preserve exact spacing, margins, and layout
5. Use proper LaTeX commands for formatting (textbf, textit, etc.)

PDF Text:
{pdf_text[:3000]}

Resume Structure (for reference):
{json.dumps(resume_json, indent=2)[:1000]}

Output ONLY the LaTeX code, no explanations. Start with \\documentclass and end with \\end{{document}}."""
        
        response = await self.gemini_client._generate_with_retry(prompt)
        
        if not response or not hasattr(response, 'text'):
            raise ValueError("Empty response from Gemini API")
        
        latex_code = response.text.strip()
        
        # Clean up if wrapped in code blocks
        if latex_code.startswith("```latex"):
            latex_code = latex_code[8:]
        elif latex_code.startswith("```"):
            latex_code = latex_code[3:]
        if latex_code.endswith("```"):
            latex_code = latex_code[:-3]
        
        return latex_code.strip()

