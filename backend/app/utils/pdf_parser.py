from pypdf import PdfReader
from typing import Dict, Any, Optional
import re
import os

class PDFParser:
    """Parse PDF resume and extract structure for LaTeX generation"""
    
    def __init__(self):
        pass
    
    async def parse_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """Parse PDF and extract text, structure, and formatting info"""
        reader = PdfReader(pdf_path)
        
        # Extract text from all pages
        full_text = ""
        for page in reader.pages:
            full_text += page.extract_text() + "\n"
        
        # Analyze structure
        structure = self._analyze_structure(full_text)
        
        return {
            "text": full_text,
            "structure": structure,
            "num_pages": len(reader.pages)
        }
    
    def _analyze_structure(self, text: str) -> Dict[str, Any]:
        """Analyze text structure to identify sections, bullets, etc."""
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        structure = {
            "sections": [],
            "has_bullets": False,
            "has_numbers": False,
            "formatting": {
                "font_sizes": [],
                "bold_patterns": [],
                "indentation_patterns": []
            }
        }
        
        # Identify sections (usually all caps or title case headers)
        current_section = None
        bullets = []
        
        for i, line in enumerate(lines):
            # Check if line is a section header
            if self._is_section_header(line, lines, i):
                if current_section:
                    structure["sections"].append({
                        "name": current_section,
                        "content": bullets
                    })
                current_section = line
                bullets = []
            else:
                # Check for bullets
                if re.match(r'^[•\-\*•]\s+', line) or re.match(r'^\d+[\.\)]\s+', line):
                    structure["has_bullets"] = True
                    if re.match(r'^\d+[\.\)]\s+', line):
                        structure["has_numbers"] = True
                bullets.append(line)
        
        if current_section:
            structure["sections"].append({
                "name": current_section,
                "content": bullets
            })
        
        return structure
    
    def _is_section_header(self, line: str, all_lines: list, index: int) -> bool:
        """Determine if a line is a section header"""
        # Common section headers
        common_sections = [
            "education", "experience", "skills", "projects", "summary",
            "objective", "achievements", "certifications", "publications",
            "references", "awards", "honors"
        ]
        
        line_lower = line.lower()
        
        # Check if it's a known section
        if any(section in line_lower for section in common_sections):
            return True
        
        # Check if it's short and likely a header (less than 30 chars)
        if len(line) < 30 and len(line.split()) < 5:
            # Check if next line is not a header
            if index + 1 < len(all_lines):
                next_line = all_lines[index + 1]
                if len(next_line) > len(line) * 2:
                    return True
        
        return False

