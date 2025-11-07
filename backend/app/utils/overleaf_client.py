"""
Overleaf CLSI (Common LaTeX Service Interface) client for compiling LaTeX to PDF
CLSI is Overleaf's open-source LaTeX compilation service

To use Overleaf CLSI:
1. Self-host CLSI using Docker: docker run -d -p 3013:3013 overleaf/clsi
2. Set OVERLEAF_CLSI_URL=http://localhost:3013 in .env
3. Optionally set OVERLEAF_CLSI_KEY if your CLSI instance requires authentication
"""
import httpx
import base64
import json
import uuid
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)


class OverleafClient:
    """
    Client for Overleaf CLSI (Common LaTeX Service Interface)
    CLSI is Overleaf's open-source LaTeX compilation service that can be self-hosted
    
    CLSI API Documentation: https://github.com/overleaf/clsi
    """
    
    def __init__(self, clsi_url: str, api_key: Optional[str] = None):
        """
        Initialize Overleaf CLSI client
        
        Args:
            clsi_url: URL of the CLSI service (e.g., "http://localhost:3013")
            api_key: Optional API key for authentication
        """
        self.clsi_url = clsi_url.rstrip('/')
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=120.0)  # Longer timeout for compilation
    
    async def compile_latex(
        self,
        latex_content: str,
        project_id: Optional[str] = None,
        compiler: str = "pdflatex"
    ) -> bytes:
        """
        Compile LaTeX content to PDF using Overleaf CLSI
        
        Args:
            latex_content: LaTeX source code
            project_id: Unique project identifier (auto-generated if not provided)
            compiler: LaTeX compiler to use (pdflatex, xelatex, lualatex)
            
        Returns:
            PDF file content as bytes
        """
        if not project_id:
            project_id = f"resume_{uuid.uuid4().hex[:8]}"
        
        # CLSI API endpoint format: POST /project/:project_id/compile
        url = f"{self.clsi_url}/project/{project_id}/compile"
        
        # CLSI expects files as base64-encoded content
        # Format: { "files": { "filename.tex": "base64_content" } }
        files_dict = {
            "main.tex": base64.b64encode(latex_content.encode('utf-8')).decode('utf-8')
        }
        
        # Prepare request payload according to CLSI API spec
        # CLSI expects: { "compile": { "options": {...}, "files": {...}, "rootResourcePath": "..." } }
        payload = {
            "compile": {
                "options": {
                    "compiler": compiler,
                    "timeout": 60,
                    "imageName": "texlive/texlive:latest"  # Use standard TeX Live image
                },
                "files": files_dict,
                "rootResourcePath": "main.tex"
            }
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        try:
            logger.info(f"Compiling LaTeX via Overleaf CLSI at {url}")
            
            # Send compilation request
            response = await self.client.post(
                url,
                json=payload,
                headers=headers
            )
            
            if response.status_code != 200:
                error_text = response.text[:500]
                raise RuntimeError(f"CLSI compilation failed (HTTP {response.status_code}): {error_text}")
            
            result = response.json()
            
            # CLSI returns compilation status and output files
            status = result.get("status", "error")
            if status != "success":
                # Get error log from output
                output = result.get("output", {})
                log_output = output.get("main.log", "")
                if not log_output:
                    log_output = str(result)
                raise RuntimeError(f"LaTeX compilation failed: {log_output[:500]}")
            
            # Get PDF from output files
            output = result.get("output", {})
            pdf_base64 = output.get("main.pdf")
            
            if not pdf_base64:
                # Try alternative format
                pdf_base64 = result.get("pdf")
            
            if not pdf_base64:
                raise RuntimeError("No PDF returned from CLSI. Compilation may have failed.")
            
            # Decode base64 PDF
            try:
                pdf_bytes = base64.b64decode(pdf_base64)
            except Exception as e:
                raise RuntimeError(f"Failed to decode PDF from CLSI: {str(e)}")
            
            logger.info(f"Successfully compiled LaTeX to PDF ({len(pdf_bytes)} bytes)")
            return pdf_bytes
            
        except httpx.HTTPError as e:
            raise RuntimeError(f"CLSI request failed: {str(e)}")
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Invalid JSON response from CLSI: {str(e)}")
        finally:
            await self.client.aclose()
    
    async def compile_latex_to_file(
        self,
        latex_content: str,
        output_path: str,
        project_id: Optional[str] = None,
        compiler: str = "pdflatex"
    ) -> str:
        """
        Compile LaTeX to PDF and save to file
        
        Args:
            latex_content: LaTeX source code
            output_path: Path to save PDF file
            project_id: Optional project ID (auto-generated if not provided)
            compiler: LaTeX compiler to use
            
        Returns:
            Path to generated PDF file
        """
        import os
        import uuid
        
        if not project_id:
            project_id = f"resume_{uuid.uuid4().hex[:8]}"
        
        # Compile LaTeX
        pdf_bytes = await self.compile_latex(latex_content, project_id, compiler)
        
        # Save to file
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
        with open(output_path, 'wb') as f:
            f.write(pdf_bytes)
        
        return output_path

