from typing import Dict, Any, Optional
import os
import tempfile
import subprocess
from jinja2 import Template

class LaTeXGenerator:
    """Generate LaTeX resumes from structured data"""
    
    def __init__(self):
        self.template = self._get_resume_template()
    
    def _get_resume_template(self) -> str:
        """Get LaTeX resume template"""
        return r"""\documentclass[10pt,a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage[margin=0.6in]{geometry}
\usepackage{fancyhdr}
\usepackage{enumitem}
\usepackage{titlesec}
\usepackage{xcolor}

% Style settings
\pagestyle{empty}
\setlength{\parindent}{0pt}
\setlength{\parskip}{4pt}

% Section formatting - more compact
\titleformat{\section}{\large\bfseries\uppercase}{}{0em}{}[\titlerule]
\titlespacing*{\section}{0pt}{8pt}{4pt}

% Custom commands
\newcommand{\resumeheader}[4]{
    \begin{center}
        \textbf{\Large #1} \\
        #2 \textbar{} #3 \textbar{} #4
    \end{center}
    \vspace{0.3cm}
}

\newcommand{\resumeitem}[4]{
    \textbf{#1} \hfill #2 \\
    \textit{#3} \hfill #4
    \begin{itemize}[leftmargin=*,topsep=0pt,itemsep=2pt]
}

\begin{document}

\resumeheader{${name}}{${email}}{${phone}}{${location}}

\section{Summary}
${summary}

\section{Experience}
${experience}

\section{Education}
${education}

\section{Skills}
${skills}

${projects}

\end{document}
"""
    
    async def generate_latex(
        self,
        resume_json: Dict[str, Any],
        original_latex_template: Optional[str] = None
    ) -> str:
        """Generate LaTeX from resume JSON, optionally using original template"""
        if original_latex_template:
            # Use original template and inject new content
            return self._inject_content_into_template(original_latex_template, resume_json)
        else:
            # Generate new LaTeX from template
            return self._generate_from_template(resume_json)
    
    def _generate_from_template(self, resume_json: Dict[str, Any]) -> str:
        """Generate LaTeX using default template"""
        template = Template(self.template)
        
        # Format experience - limit bullets to fit on 1 page
        experience_latex = ""
        for exp in resume_json.get("experience", []):
            company = exp.get("company", "")
            title = exp.get("title", "")
            start = exp.get("start", "")
            end = exp.get("end", "Present")
            # Limit to 3 most relevant bullets per role
            bullets = exp.get("bullets", [])[:3]
            
            experience_latex += f"\\resumeitem{{{title}}}{{{start} - {end}}}{{{company}}}{{}}\n"
            for bullet in bullets:
                # Escape LaTeX special characters
                bullet_escaped = self._escape_latex(bullet)
                experience_latex += f"        \\item {bullet_escaped}\n"
            experience_latex += "    \\end{itemize}\n\\vspace{4pt}\n"  # Reduced from 6pt
        
        # Format education
        education_latex = ""
        for edu in resume_json.get("education", []):
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
                
                # Escape LaTeX special characters
                edu_line_escaped = self._escape_latex(edu_line)
                education_latex += f"\\textbf{{{edu_line_escaped}}}\\\\\n"
            else:
                edu_escaped = self._escape_latex(str(edu))
                education_latex += f"{edu_escaped}\\\\\n"
        
        # Format skills
        skills = resume_json.get("skills", [])
        skills_latex = ", ".join(skills)
        
        # Format projects - limit to fit on 1 page
        projects_latex = ""
        if resume_json.get("projects"):
            projects_latex = "\\section{Projects}\n"
            # Limit to 3 most relevant projects
            projects_list = resume_json.get("projects", [])[:3]
            for project in projects_list:
                name = project.get("name", "")
                # Limit to 2 bullets per project
                bullets = project.get("bullets", [])[:2]
                projects_latex += f"\\textbf{{{name}}}\n"
                projects_latex += "\\begin{itemize}[leftmargin=*,topsep=0pt,itemsep=2pt]\n"
                for bullet in bullets:
                    bullet_escaped = self._escape_latex(bullet)
                    projects_latex += f"    \\item {bullet_escaped}\n"
                projects_latex += "\\end{itemize}\n\\vspace{4pt}\n"  # Reduced from 6pt
        
        return template.render(
            name=resume_json.get("name", ""),
            email=resume_json.get("email", ""),
            phone=resume_json.get("phone", ""),
            location=resume_json.get("location", ""),
            summary=self._escape_latex(resume_json.get("summary", "")),
            experience=experience_latex,
            education=education_latex,
            skills=skills_latex,
            projects=projects_latex
        )
    
    def _inject_content_into_template(
        self,
        template: str,
        resume_json: Dict[str, Any]
    ) -> str:
        """Inject new content into original LaTeX template"""
        # This is a simplified version - in production, you'd want more sophisticated
        # parsing to preserve exact formatting
        latex = template
        
        # Replace experience sections
        experience_latex = ""
        for exp in resume_json.get("experience", []):
            company = exp.get("company", "")
            title = exp.get("title", "")
            start = exp.get("start", "")
            end = exp.get("end", "Present")
            bullets = exp.get("bullets", [])
            
            experience_latex += f"\\textbf{{{title}}} at {company} ({start} - {end})\\\\\n"
            experience_latex += "\\begin{itemize}[leftmargin=*]\n"
            for bullet in bullets:
                bullet_escaped = self._escape_latex(bullet)
                experience_latex += f"    \\item {bullet_escaped}\n"
            experience_latex += "\\end{itemize}\n\\vspace{6pt}\n"
        
        # Simple substitution (can be enhanced)
        latex = latex.replace("${experience}", experience_latex)
        
        return latex
    
    def _escape_latex(self, text: str) -> str:
        """Escape LaTeX special characters"""
        special_chars = {
            '&': r'\&',
            '%': r'\%',
            '$': r'\$',
            '#': r'\#',
            '^': r'\textasciicircum{}',
            '_': r'\_',
            '{': r'\{',
            '}': r'\}',
            '~': r'\textasciitilde{}',
            '\\': r'\textbackslash{}'
        }
        for char, escaped in special_chars.items():
            text = text.replace(char, escaped)
        return text

