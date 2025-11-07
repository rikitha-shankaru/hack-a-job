import subprocess
import os
import tempfile
import shutil
from typing import Optional
import logging
from app.config import settings

logger = logging.getLogger(__name__)

class LaTeXCompiler:
    """
    Compile LaTeX documents to PDF
    Supports both local pdflatex and Overleaf CLSI
    """
    
    def __init__(self):
        # Check if pdflatex is available locally
        self.has_pdflatex = self._check_pdflatex()
        
        # Check if Overleaf CLSI is configured
        self.use_overleaf = bool(settings.overleaf_clsi_url)
        if self.use_overleaf:
            from app.utils.overleaf_client import OverleafClient
            self.overleaf_client = OverleafClient(
                settings.overleaf_clsi_url,
                settings.overleaf_clsi_key
            )
        else:
            self.overleaf_client = None
    
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
        """
        Compile LaTeX content to PDF
        Uses Overleaf CLSI if configured, otherwise falls back to local pdflatex
        """
        # Try Overleaf CLSI first if configured (PREFERRED METHOD)
        if self.use_overleaf and self.overleaf_client:
            try:
                logger.info("Using Overleaf CLSI for LaTeX compilation")
                pdf_bytes = await self.overleaf_client.compile_latex(latex_content)
                
                # Save PDF to file
                if not output_filename:
                    output_filename = os.path.join(tempfile.gettempdir(), f"resume_{uuid.uuid4().hex[:8]}.pdf")
                
                os.makedirs(os.path.dirname(output_filename) if os.path.dirname(output_filename) else '.', exist_ok=True)
                with open(output_filename, 'wb') as f:
                    f.write(pdf_bytes)
                
                logger.info(f"Successfully compiled LaTeX to PDF using Overleaf CLSI: {output_filename}")
                return output_filename
            except Exception as e:
                logger.warning(f"Overleaf CLSI compilation failed: {e}. Falling back to local pdflatex.")
                # Fall through to local compilation
        
        # Fall back to local pdflatex
        if not self.has_pdflatex:
            raise RuntimeError(
                "pdflatex is not installed and Overleaf CLSI is not configured. "
                "Install TeX Live or MikTeX, or set OVERLEAF_CLSI_URL in environment variables."
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

