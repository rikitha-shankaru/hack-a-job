import subprocess
import os
import tempfile
import shutil
import uuid
from typing import Optional
import logging
from app.config import settings

logger = logging.getLogger(__name__)

class LaTeXCompiler:
    """
    Compile LaTeX documents to PDF
    Supports multiple methods in priority order:
    1. Docker TeX Live (recommended - official, reliable, no setup needed)
    2. Local pdflatex (if installed)
    3. Overleaf CLSI (legacy support, if configured)
    4. ReportLab fallback (last resort, handled by caller)
    """
    
    def __init__(self):
        # Check Docker availability for TeX Live (BEST METHOD)
        self.docker_client = None
        self.use_docker_latex = False
        try:
            import docker
            self.docker_client = docker.from_env()
            # Test Docker connection
            self.docker_client.ping()
            self.use_docker_latex = True
            logger.info("Docker available - will use Docker TeX Live for LaTeX compilation")
        except ImportError:
            logger.info("Docker Python library not installed. Install with: pip install docker")
            self.use_docker_latex = False
        except (Exception, AttributeError) as e:
            logger.info(f"Docker not available: {e}. Will use local pdflatex or fallback.")
            self.use_docker_latex = False
        
        # Check if pdflatex is available locally
        self.has_pdflatex = self._check_pdflatex()
        
        # Check if Overleaf CLSI is configured (legacy support)
        self.use_overleaf = bool(settings.overleaf_clsi_url)
        if self.use_overleaf:
            try:
                from app.utils.overleaf_client import OverleafClient
                self.overleaf_client = OverleafClient(
                    settings.overleaf_clsi_url,
                    settings.overleaf_clsi_key
                )
            except Exception as e:
                logger.warning(f"Overleaf CLSI not available: {e}")
                self.overleaf_client = None
                self.use_overleaf = False
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
        Priority: Docker TeX Live > Local pdflatex > Overleaf CLSI > ReportLab fallback
        """
        # Method 1: Try Docker TeX Live (BEST - official, reliable, no setup needed)
        if self.use_docker_latex and self.docker_client:
            try:
                logger.info("Using Docker TeX Live for LaTeX compilation")
                return await self._compile_with_docker_texlive(latex_content, output_filename)
            except Exception as e:
                logger.warning(f"Docker TeX Live compilation failed: {e}. Trying next method.")
        
        # Method 2: Try local pdflatex
        if self.has_pdflatex:
            try:
                logger.info("Using local pdflatex for LaTeX compilation")
                return await self._compile_with_local_pdflatex(latex_content, output_filename)
            except Exception as e:
                logger.warning(f"Local pdflatex compilation failed: {e}. Trying next method.")
        
        # Method 3: Try Overleaf CLSI (legacy support)
        if self.use_overleaf and self.overleaf_client:
            try:
                logger.info("Using Overleaf CLSI for LaTeX compilation")
                pdf_bytes = await self.overleaf_client.compile_latex(latex_content)
                
                if not output_filename:
                    output_filename = os.path.join(tempfile.gettempdir(), f"resume_{uuid.uuid4().hex[:8]}.pdf")
                
                os.makedirs(os.path.dirname(output_filename) if os.path.dirname(output_filename) else '.', exist_ok=True)
                with open(output_filename, 'wb') as f:
                    f.write(pdf_bytes)
                
                logger.info(f"Successfully compiled LaTeX to PDF using Overleaf CLSI: {output_filename}")
                return output_filename
            except Exception as e:
                logger.warning(f"Overleaf CLSI compilation failed: {e}. All LaTeX methods failed.")
        
        # All methods failed
        raise RuntimeError(
            "LaTeX compilation failed. No working LaTeX compiler found. "
            "Options: 1) Install Docker and run 'docker-compose -f docker-compose.latex.yml up -d', "
            "2) Install TeX Live locally (brew install --cask mactex), or "
            "3) Configure Overleaf CLSI (legacy)."
        )
    
    async def _compile_with_docker_texlive(
        self,
        latex_content: str,
        output_filename: Optional[str] = None
    ) -> str:
        """Compile LaTeX using Docker TeX Live container (official, reliable method)"""
        import asyncio
        
        if not output_filename:
            output_filename = os.path.join(tempfile.gettempdir(), f"resume_{uuid.uuid4().hex[:8]}.pdf")
        
        # Ensure output directory exists
        output_dir = os.path.dirname(output_filename) or '.'
        os.makedirs(output_dir, exist_ok=True)
        
        # Create temporary directory for LaTeX files
        temp_dir = tempfile.mkdtemp()
        latex_file = os.path.join(temp_dir, "resume.tex")
        
        try:
            # Write LaTeX content to file
            with open(latex_file, 'w', encoding='utf-8') as f:
                f.write(latex_content)
            
            # Get absolute paths for Docker volume mounting
            temp_dir_abs = os.path.abspath(temp_dir)
            output_dir_abs = os.path.abspath(output_dir)
            output_filename_basename = os.path.basename(output_filename)
            
            # Run pdflatex in Docker container
            # Use official TeX Live image - it's reliable and has all packages
            try:
                # Try to pull image if not exists
                try:
                    self.docker_client.images.get('texlive/texlive:latest')
                except docker.errors.ImageNotFound:
                    logger.info("Pulling TeX Live Docker image (first time, may take a minute)...")
                    self.docker_client.images.pull('texlive/texlive:latest')
                
                # Run compilation in container
                container = self.docker_client.containers.run(
                    image='texlive/texlive:latest',
                    command=f'sh -c "cd /workspace && pdflatex -interaction=nonstopmode resume.tex && pdflatex -interaction=nonstopmode resume.tex && cp resume.pdf /output/{output_filename_basename}"',
                    volumes={
                        temp_dir_abs: {'bind': '/workspace', 'mode': 'rw'},
                        output_dir_abs: {'bind': '/output', 'mode': 'rw'}
                    },
                    remove=True,  # Auto-remove container after execution
                    detach=False
                )
                
                # Check if PDF was generated
                output_path = os.path.join(output_dir, output_filename_basename)
                if os.path.exists(output_path):
                    logger.info(f"Successfully compiled LaTeX to PDF using Docker TeX Live: {output_filename}")
                    return output_path
                else:
                    raise RuntimeError("Docker TeX Live compilation completed but no PDF was generated")
                    
            except docker.errors.ImageNotFound:
                # Pull the image and retry
                logger.info("Pulling TeX Live Docker image...")
                self.docker_client.images.pull('texlive/texlive:latest')
                return await self._compile_with_docker_texlive(latex_content, output_filename)
            except Exception as e:
                raise RuntimeError(f"Docker TeX Live compilation failed: {str(e)}")
        finally:
            # Clean up temp directory
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
    
    async def _compile_with_local_pdflatex(
        self,
        latex_content: str,
        output_filename: Optional[str] = None
    ) -> str:
        """Compile LaTeX using local pdflatex installation"""
        if not output_filename:
            output_filename = os.path.join(tempfile.gettempdir(), f"resume_{uuid.uuid4().hex[:8]}.pdf")
        
        # Ensure output directory exists
        output_dir = os.path.dirname(output_filename) or '.'
        os.makedirs(output_dir, exist_ok=True)
        
        # Create temporary directory
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Write LaTeX file
            latex_file = os.path.join(temp_dir, "resume.tex")
            with open(latex_file, 'w', encoding='utf-8') as f:
                f.write(latex_content)
            
            # Compile LaTeX to PDF (two passes for references)
            result = subprocess.run(
                ['pdflatex', '-interaction=nonstopmode', '-output-directory', temp_dir, latex_file],
                cwd=temp_dir,
                capture_output=True,
                timeout=60,
                text=True
            )
            
            if result.returncode != 0:
                error_output = result.stderr[:500] if result.stderr else result.stdout[:500]
                raise RuntimeError(f"pdflatex compilation failed: {error_output}")
            
            # Second pass for references
            subprocess.run(
                ['pdflatex', '-interaction=nonstopmode', '-output-directory', temp_dir, latex_file],
                cwd=temp_dir,
                capture_output=True,
                timeout=60,
                text=True
            )
            
            # Find the generated PDF
            pdf_file = os.path.join(temp_dir, "resume.pdf")
            if not os.path.exists(pdf_file):
                raise RuntimeError("pdflatex compilation completed but no PDF was generated")
            
            # Copy PDF to output location
            shutil.copy2(pdf_file, output_filename)
            logger.info(f"Successfully compiled LaTeX to PDF using local pdflatex: {output_filename}")
            return output_filename
                
        finally:
            # Clean up temp directory
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
