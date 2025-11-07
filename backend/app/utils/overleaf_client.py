"""
Overleaf CLSI (Common LaTeX Service Interface) client for compiling LaTeX to PDF
CLSI is Overleaf's open-source LaTeX compilation service
"""
import httpx
import base64
import json
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class OverleafClient:
    """
    Client for Overleaf CLSI (Common LaTeX Service Interface)
    CLSI is Overleaf's open-source LaTeX compilation service that can be self-hosted
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
        project_id: str = "resume_project",
        compiler: str = "pdflatex"
    ) -> bytes:
        """
        Compile LaTeX content to PDF using Overleaf CLSI
        
        Args:
            latex_content: LaTeX source code
            project_id: Unique project identifier
            compiler: LaTeX compiler to use (pdflatex, xelatex, lualatex)
            
        Returns:
            PDF file content as bytes
        """
        # CLSI API endpoint
        url = f"{self.clsi_url}/project/{project_id}/compile"
        
        # Prepare request payload
        # CLSI expects files in a specific format
        files = {
            "main.tex": latex_content.encode('utf-8')
        }
        
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        # Compile request
        compile_params = {
            "compiler": compiler,
            "timeout": 60
        }
        
        try:
            # Send compilation request
            response = await self.client.post(
                url,
                json={
                    "compile": compile_params,
                    "files": {name: base64.b64encode(content).decode('utf-8') 
                             for name, content in files.items()}
                },
                headers=headers
            )
            
            if response.status_code != 200:
                raise RuntimeError(f"CLSI compilation failed: {response.text}")
            
            result = response.json()
            
            # Check if compilation was successful
            if result.get("status") != "success":
                error_log = result.get("output", "")
                raise RuntimeError(f"LaTeX compilation failed: {error_log[:500]}")
            
            # Get PDF content
            pdf_base64 = result.get("pdf")
            if not pdf_base64:
                raise RuntimeError("No PDF returned from CLSI")
            
            # Decode base64 PDF
            pdf_bytes = base64.b64decode(pdf_base64)
            return pdf_bytes
            
        except httpx.HTTPError as e:
            raise RuntimeError(f"CLSI request failed: {str(e)}")
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

