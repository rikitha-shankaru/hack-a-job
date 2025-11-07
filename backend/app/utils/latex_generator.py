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
        """
        Inject new content into original LaTeX template - preserving exact formatting.
        This replaces ONLY the content placeholders while keeping all formatting intact.
        """
        latex = template
        
        # Format header - replace placeholders
        name = resume_json.get("name", "") or ""
        email = resume_json.get("email", "") or ""
        phone = resume_json.get("phone", "") or ""
        location = resume_json.get("location", "") or ""
        
        # Format links if they exist
        links = resume_json.get("links", {})
        links_text = ""
        if links:
            link_parts = []
            if links.get("linkedin"):
                link_parts.append(f"\\href{{{links['linkedin']}}}{{LinkedIn}}")
            if links.get("github"):
                link_parts.append(f"\\href{{{links['github']}}}{{GitHub}}")
            if links.get("portfolio"):
                link_parts.append(f"\\href{{{links['portfolio']}}}{{Portfolio}}")
            if links.get("website"):
                link_parts.append(f"\\href{{{links['website']}}}{{Website}}")
            if link_parts:
                links_text = " | ".join(link_parts)
        
        # Ensure hyperref package is included for links to work
        if links_text and "\\usepackage{hyperref}" not in latex:
            # Find where packages are and add hyperref
            if "\\usepackage" in latex:
                # Add after other packages
                latex = latex.replace("\\usepackage{xcolor}", "\\usepackage{xcolor}\n\\usepackage{hyperref}")
                if "\\usepackage{xcolor}" not in latex:
                    # Find last \usepackage and add after it
                    import re
                    matches = list(re.finditer(r'\\usepackage\{[^}]+\}', latex))
                    if matches:
                        last_match = matches[-1]
                        insert_pos = last_match.end()
                        latex = latex[:insert_pos] + "\n\\usepackage{hyperref}" + latex[insert_pos:]
        
        # Replace header placeholders (handle both ${var} and {var} formats)
        # Also handle cases where links might be in the header
        # Use regex to handle variations and preserve formatting
        import re
        
        # Replace name (handle various formats)
        latex = re.sub(r'\$\{name\}|\{name\}', self._escape_latex(name), latex)
        latex = latex.replace("${name}", self._escape_latex(name))
        
        # Replace email
        latex = re.sub(r'\$\{email\}|\{email\}', self._escape_latex(email), latex)
        latex = latex.replace("${email}", self._escape_latex(email))
        
        # Replace phone
        latex = re.sub(r'\$\{phone\}|\{phone\}', self._escape_latex(phone), latex)
        latex = latex.replace("${phone}", self._escape_latex(phone))
        
        # Replace location
        latex = re.sub(r'\$\{location\}|\{location\}', self._escape_latex(location), latex)
        latex = latex.replace("${location}", self._escape_latex(location))
        
        # Replace links
        latex = re.sub(r'\$\{links\}|\{links\}', links_text, latex)
        latex = latex.replace("${links}", links_text)
        
        # Also handle if links are part of contact info (common pattern)
        # Replace patterns like ${email} | ${phone} | ${location} with links
        if links_text and "${links}" not in template:
            # Try to inject links into header if there's a pattern for it
            # Common pattern: email | phone | location | links
            contact_patterns = [
                ("${email} \\textbar{} ${phone} \\textbar{} ${location}", 
                 f"{self._escape_latex(email)} \\textbar{{}} {self._escape_latex(phone)} \\textbar{{}} {self._escape_latex(location)} | {links_text}"),
                ("${email} | ${phone} | ${location}",
                 f"{self._escape_latex(email)} | {self._escape_latex(phone)} | {self._escape_latex(location)} | {links_text}"),
            ]
            for pattern, replacement in contact_patterns:
                if pattern in latex:
                    latex = latex.replace(pattern, replacement)
                    break
        
        # Format summary - handle both ${summary} and {summary} formats
        summary = self._escape_latex(resume_json.get("summary", ""))
        latex = re.sub(r'\$\{summary\}|\{summary\}', summary, latex)
        latex = latex.replace("${summary}", summary)
        
        # Format experience - preserve original structure
        experience_latex = ""
        for exp in resume_json.get("experience", [])[:3]:  # Limit to 3 experiences
            company = exp.get("company", "")
            title = exp.get("title", "")
            start = exp.get("start", "")
            end = exp.get("end", "Present")
            bullets = exp.get("bullets", [])[:3]  # Limit to 3 bullets per role
            
            # Format: Title at Company (Start - End)
            experience_latex += f"\\textbf{{{self._escape_latex(title)}}} at {self._escape_latex(company)} ({start} - {end})\\\\\n"
            experience_latex += "\\begin{itemize}[leftmargin=*,topsep=0pt,itemsep=2pt]\n"
            for bullet in bullets:
                bullet_escaped = self._escape_latex(bullet)
                experience_latex += f"    \\item {bullet_escaped}\n"
            experience_latex += "\\end{itemize}\n\\vspace{4pt}\n"
        
        # Replace experience - handle both formats
        latex = re.sub(r'\$\{experience\}|\{experience\}', experience_latex, latex)
        latex = latex.replace("${experience}", experience_latex)
        
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
                
                edu_line_escaped = self._escape_latex(edu_line)
                education_latex += f"\\textbf{{{edu_line_escaped}}}\\\\\n"
            else:
                edu_escaped = self._escape_latex(str(edu))
                education_latex += f"{edu_escaped}\\\\\n"
        
        latex = latex.replace("${education}", education_latex)
        
        # Format skills
        skills = resume_json.get("skills", [])[:20]  # Limit to 20
        skills_latex = ", ".join([self._escape_latex(s) for s in skills])
        latex = latex.replace("${skills}", skills_latex)
        
        # Format projects
        projects_latex = ""
        if resume_json.get("projects"):
            projects_list = resume_json.get("projects", [])[:3]  # Limit to 3
            for project in projects_list:
                name = project.get("name", "")
                bullets = project.get("bullets", [])[:2]  # Limit to 2 bullets
                projects_latex += f"\\textbf{{{self._escape_latex(name)}}}\n"
                projects_latex += "\\begin{itemize}[leftmargin=*,topsep=0pt,itemsep=2pt]\n"
                for bullet in bullets:
                    bullet_escaped = self._escape_latex(bullet)
                    projects_latex += f"    \\item {bullet_escaped}\n"
                projects_latex += "\\end{itemize}\n\\vspace{4pt}\n"
        
        latex = latex.replace("${projects}", projects_latex)
        
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

