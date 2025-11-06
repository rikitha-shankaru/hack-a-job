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
            fontSize=9,  # Reduced from 10 to fit more content
            textColor='black',
            spaceAfter=4,  # Reduced from 6
            alignment=TA_LEFT,
            bulletIndent=15  # Reduced from 20
        )
    
    async def generate_resume_pdf(self, resume_json: Dict[str, Any]) -> str:
        """Generate resume PDF from JSON - optimized for 1 page"""
        # Create temporary file
        fd, temp_path = tempfile.mkstemp(suffix='.pdf')
        os.close(fd)
        
        # Reduced margins to fit more content on 1 page
        doc = SimpleDocTemplate(temp_path, pagesize=letter,
                                rightMargin=60, leftMargin=60,
                                topMargin=60, bottomMargin=60)
        
        story = []
        
        # Summary - compact
        if resume_json.get("summary"):
            # Truncate summary if too long to fit on 1 page
            summary = resume_json["summary"]
            if len(summary) > 300:
                summary = summary[:297] + "..."
            story.append(Paragraph(summary, self.body_style))
            story.append(Spacer(1, 0.1*inch))  # Reduced from 0.2
        
        # Skills - compact
        if resume_json.get("skills"):
            story.append(Paragraph("<b>Skills</b>", self.heading_style))
            # Limit to top 15-20 skills to save space
            skills = resume_json["skills"][:20]
            skills_text = ", ".join(skills)
            story.append(Paragraph(skills_text, self.body_style))
            story.append(Spacer(1, 0.1*inch))  # Reduced from 0.15
        
        # Experience - limit bullets per role
        if resume_json.get("experience"):
            story.append(Paragraph("<b>Experience</b>", self.heading_style))
            for exp in resume_json["experience"]:
                # Company and title
                company = exp.get("company", "")
                title = exp.get("title", "")
                dates = f"{exp.get('start', '')} - {exp.get('end', 'Present')}"
                header = f"<b>{title}</b> at {company} | {dates}"
                story.append(Paragraph(header, self.body_style))
                
                # Limit to 3 most relevant bullets per role
                bullets = exp.get("bullets", [])[:3]
                for bullet in bullets:
                    story.append(Paragraph(f"• {bullet}", self.body_style))
                
                story.append(Spacer(1, 0.05*inch))  # Reduced from 0.1
        
        # Projects - limit bullets per project
        if resume_json.get("projects"):
            story.append(Paragraph("<b>Projects</b>", self.heading_style))
            # Limit to 3 most relevant projects
            projects = resume_json["projects"][:3]
            for project in projects:
                name = project.get("name", "")
                story.append(Paragraph(f"<b>{name}</b>", self.body_style))
                # Limit to 2 bullets per project
                bullets = project.get("bullets", [])[:2]
                for bullet in bullets:
                    story.append(Paragraph(f"• {bullet}", self.body_style))
                story.append(Spacer(1, 0.05*inch))  # Reduced from 0.1
        
        # Education - compact
        if resume_json.get("education"):
            story.append(Paragraph("<b>Education</b>", self.heading_style))
            for edu in resume_json["education"]:
                if isinstance(edu, dict):
                    degree = edu.get("degree", "")
                    school = edu.get("school", "")
                    major = edu.get("major", "")
                    start = edu.get("start", "")
                    end = edu.get("end", "")
                    gpa = edu.get("gpa", "")
                    
                    # Build education line: "Degree in Major - School (Start - End) | GPA: X.XX"
                    edu_parts = []
                    if degree:
                        if major:
                            edu_parts.append(f"{degree} in {major}")
                        else:
                            edu_parts.append(degree)
                    if school:
                        edu_parts.append(school)
                    
                    date_range = ""
                    if start and end:
                        date_range = f"({start} - {end})"
                    elif start:
                        date_range = f"({start})"
                    
                    edu_line = " - ".join(edu_parts)
                    if date_range:
                        edu_line += f" {date_range}"
                    if gpa:
                        edu_line += f" | GPA: {gpa}"
                    
                    story.append(Paragraph(edu_line, self.body_style))
                else:
                    story.append(Paragraph(str(edu), self.body_style))
            # No spacer after education (last section)
        
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

