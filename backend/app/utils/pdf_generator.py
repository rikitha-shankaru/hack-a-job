from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from typing import Dict, Any
import os
import tempfile
import json

class PDFGenerator:
    """Generate ATS-friendly PDFs from JSON"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=16,
            textColor='black',
            spaceAfter=12,
            alignment=TA_LEFT
        )
        
        self.heading_style = ParagraphStyle(
            'CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=12,
            textColor='black',
            spaceAfter=6,
            spaceBefore=12,
            alignment=TA_LEFT
        )
        
        self.body_style = ParagraphStyle(
            'CustomBody',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor='black',
            spaceAfter=6,
            alignment=TA_LEFT,
            bulletIndent=20
        )
    
    async def generate_resume_pdf(self, resume_json: Dict[str, Any]) -> str:
        """Generate resume PDF from JSON"""
        # Create temporary file
        fd, temp_path = tempfile.mkstemp(suffix='.pdf')
        os.close(fd)
        
        doc = SimpleDocTemplate(temp_path, pagesize=letter,
                                rightMargin=72, leftMargin=72,
                                topMargin=72, bottomMargin=72)
        
        story = []
        
        # Summary
        if resume_json.get("summary"):
            story.append(Paragraph(resume_json["summary"], self.body_style))
            story.append(Spacer(1, 0.2*inch))
        
        # Skills
        if resume_json.get("skills"):
            story.append(Paragraph("<b>Skills</b>", self.heading_style))
            skills_text = ", ".join(resume_json["skills"])
            story.append(Paragraph(skills_text, self.body_style))
            story.append(Spacer(1, 0.15*inch))
        
        # Experience
        if resume_json.get("experience"):
            story.append(Paragraph("<b>Experience</b>", self.heading_style))
            for exp in resume_json["experience"]:
                # Company and title
                company = exp.get("company", "")
                title = exp.get("title", "")
                dates = f"{exp.get('start', '')} - {exp.get('end', 'Present')}"
                header = f"<b>{title}</b> at {company} | {dates}"
                story.append(Paragraph(header, self.body_style))
                
                # Bullets
                for bullet in exp.get("bullets", []):
                    story.append(Paragraph(f"• {bullet}", self.body_style))
                
                story.append(Spacer(1, 0.1*inch))
        
        # Projects
        if resume_json.get("projects"):
            story.append(Paragraph("<b>Projects</b>", self.heading_style))
            for project in resume_json["projects"]:
                name = project.get("name", "")
                story.append(Paragraph(f"<b>{name}</b>", self.body_style))
                for bullet in project.get("bullets", []):
                    story.append(Paragraph(f"• {bullet}", self.body_style))
                story.append(Spacer(1, 0.1*inch))
        
        # Education
        if resume_json.get("education"):
            story.append(Paragraph("<b>Education</b>", self.heading_style))
            for edu in resume_json["education"]:
                edu_text = json.dumps(edu) if isinstance(edu, dict) else str(edu)
                story.append(Paragraph(edu_text, self.body_style))
                story.append(Spacer(1, 0.1*inch))
        
        doc.build(story)
        return temp_path
    
    async def generate_cover_letter_pdf(self, cover_json: Dict[str, Any]) -> str:
        """Generate cover letter PDF from JSON"""
        fd, temp_path = tempfile.mkstemp(suffix='.pdf')
        os.close(fd)
        
        doc = SimpleDocTemplate(temp_path, pagesize=letter,
                                rightMargin=72, leftMargin=72,
                                topMargin=72, bottomMargin=72)
        
        story = []
        
        # Opening
        if cover_json.get("opening"):
            story.append(Paragraph(cover_json["opening"], self.body_style))
            story.append(Spacer(1, 0.2*inch))
        
        # Mapping bullets
        if cover_json.get("mapping"):
            for bullet in cover_json["mapping"]:
                story.append(Paragraph(f"• {bullet}", self.body_style))
            story.append(Spacer(1, 0.2*inch))
        
        # Closing
        if cover_json.get("closing"):
            story.append(Paragraph(cover_json["closing"], self.body_style))
        
        doc.build(story)
        return temp_path

