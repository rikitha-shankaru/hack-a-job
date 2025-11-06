import subprocess
import os
import tempfile
import shutil
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class LaTeXCompiler:
    """Compile LaTeX documents to PDF"""
    
    def __init__(self):
        # Check if pdflatex is available
        self.has_pdflatex = self._check_pdflatex()
    
    def _check_pdflatex(self) -> bool:
        """Check if pdflatex is installed"""
        try:
            result = subprocess.run(
                ['pdflatex', '--version'],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    async def compile_latex_to_pdf(
        self,
        latex_content: str,
        output_filename: Optional[str] = None
    ) -> str:
        """Compile LaTeX content to PDF"""
        if not self.has_pdflatex:
            raise RuntimeError(
                "pdflatex is not installed. "
                "Install TeX Live or MikTeX, or use Docker image 'texlive/texlive:latest'"
            )
        
        # Create temporary directory
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Write LaTeX file
            latex_file = os.path.join(temp_dir, "resume.tex")
            with open(latex_file, 'w', encoding='utf-8') as f:
                f.write(latex_content)
            
            # Compile LaTeX to PDF
            result = subprocess.run(
                ['pdflatex', '-interaction=nonstopmode', '-output-directory', temp_dir, latex_file],
                cwd=temp_dir,
                capture_output=True,
                timeout=60,
                text=True
            )
            
            if result.returncode != 0:
                logger.error(f"LaTeX compilation error: {result.stderr}")
                raise RuntimeError(f"LaTeX compilation failed: {result.stderr[:500]}")
            
            # Second pass for references
            subprocess.run(
                ['pdflatex', '-interaction=nonstopmode', '-output-directory', temp_dir, latex_file],
                cwd=temp_dir,
                capture_output=True,
                timeout=60,
                text=True
            )
            
            # Find generated PDF
            pdf_path = os.path.join(temp_dir, "resume.pdf")
            if not os.path.exists(pdf_path):
                raise RuntimeError("PDF file was not generated")
            
            # Move to final location if specified
            if output_filename:
                final_path = output_filename
                shutil.move(pdf_path, final_path)
                return final_path
            
            return pdf_path
            
        finally:
            # Cleanup (keep PDF if output_filename not specified)
            if output_filename and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)

