from app.config import settings
from app.utils.gemini_client import GeminiClient
from app.utils.latex_generator import LaTeXGenerator
from app.utils.latex_compiler import LaTeXCompiler
from app.utils.pdf_generator import PDFGenerator
from app.models import User, Job, TailoredAsset
from sqlalchemy.orm import Session
from typing import Dict, Any
import uuid
import json
import os

class TailorService:
    def __init__(self):
        self.gemini_client = GeminiClient()
        self.latex_generator = LaTeXGenerator()
        self.latex_compiler = LaTeXCompiler()
        self.pdf_generator = PDFGenerator()  # Still used for cover letter
    
    async def generate_tailored_assets(
        self,
        user: User,
        job: Job,
        db: Session
    ) -> TailoredAsset:
        """Generate tailored resume and cover letter for a job"""
        base_resume_json = user.profile.resume_json
        job_description = job.jd_text or ""
        jd_keywords = job.jd_keywords or []
        
        # Generate tailored resume using Gemini
        tailored_resume = await self.gemini_client.tailor_resume(
            base_resume_json=base_resume_json,
            job_description=job_description,
            jd_keywords=jd_keywords,
            role_target=user.role_target,
            level_target=user.level_target
        )
        
        # Generate cover letter using Gemini
        cover_letter = await self.gemini_client.generate_cover_letter(
            resume_json=tailored_resume,
            job_description=job_description,
            company=job.company,
            jd_keywords=jd_keywords
        )
        
        # Generate resume PDF using LaTeX (preserving original formatting)
        original_latex_template = user.profile.resume_latex_template if user.profile else None
        
        # Generate LaTeX from tailored resume
        latex_content = await self.latex_generator.generate_latex(
            resume_json=tailored_resume,
            original_latex_template=original_latex_template
        )
        
        # Compile LaTeX to PDF
        uploads_dir = "uploads/pdfs"
        os.makedirs(uploads_dir, exist_ok=True)
        resume_pdf_output = os.path.join(uploads_dir, f"resume_{user.id}_{job.id}.pdf")
        
        try:
            resume_pdf_path = await self.latex_compiler.compile_latex_to_pdf(
                latex_content=latex_content,
                output_filename=resume_pdf_output
            )
        except RuntimeError as e:
            # Fallback to ReportLab if LaTeX compilation fails
            resume_pdf_path = await self.pdf_generator.generate_resume_pdf(tailored_resume)
            resume_pdf_output = os.path.join(uploads_dir, f"resume_{user.id}_{job.id}.pdf")
            import shutil
            shutil.copy2(resume_pdf_path, resume_pdf_output)
        
        # Generate cover letter PDF (using ReportLab for now)
        cover_pdf_path = await self.pdf_generator.generate_cover_letter_pdf(cover_letter)
        
        # Store PDFs and get URLs
        resume_pdf_url = self._store_pdf(resume_pdf_output, f"resume_{user.id}_{job.id}.pdf")
        cover_pdf_url = self._store_pdf(cover_pdf_path, f"cover_{user.id}_{job.id}.pdf")
        
        # Calculate diffs
        diffs = self._calculate_diffs(base_resume_json, tailored_resume)
        
        # Generate AI explanations and insights using Gemini
        ai_explanation = await self.gemini_client.generate_ai_explanation(
            base_resume_json,
            tailored_resume,
            job_description,
            jd_keywords
        )
        
        ai_recommendations = await self.gemini_client.generate_ai_recommendations(
            tailored_resume,
            job_description
        )
        
        match_score = await self.gemini_client.calculate_job_match_score(
            tailored_resume,
            job_description,
            jd_keywords
        )
        
        # Add AI insights to diffs
        diffs["ai_explanation"] = ai_explanation
        diffs["ai_recommendations"] = ai_recommendations
        diffs["match_score"] = match_score
        tailored_resume["diffs"] = diffs
        
        # Create tailored asset record
        asset = TailoredAsset(
            id=uuid.uuid4(),
            user_id=user.id,
            job_id=job.id,
            resume_json=tailored_resume,
            resume_pdf_url=resume_pdf_url,
            cover_json=cover_letter,
            cover_pdf_url=cover_pdf_url,
            status="draft"
        )
        
        db.add(asset)
        db.commit()
        db.refresh(asset)
        
        return asset
    
    def _calculate_diffs(self, base: Dict[str, Any], tailored: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate differences between base and tailored resume"""
        diffs = {
            "bullets_changed": [],
            "sections_reordered": False
        }
        
        # Compare experience bullets
        base_exp = base.get("experience", [])
        tailored_exp = tailored.get("experience", [])
        
        for i, (base_job, tailored_job) in enumerate(zip(base_exp, tailored_exp)):
            base_bullets = base_job.get("bullets", [])
            tailored_bullets = tailored_job.get("bullets", [])
            
            if base_bullets != tailored_bullets:
                diffs["bullets_changed"].append({
                    "job_index": i,
                    "company": base_job.get("company"),
                    "base_bullets": base_bullets,
                    "tailored_bullets": tailored_bullets
                })
        
        # Check if sections were reordered
        base_keys = list(base.keys())
        tailored_keys = list(tailored.keys())
        if base_keys != tailored_keys:
            diffs["sections_reordered"] = True
        
        return diffs
    
    def _store_pdf(self, pdf_path: str, filename: str) -> str:
        """Store PDF and return URL (simplified - in production use S3)"""
        # For MVP, store in uploads directory
        uploads_dir = "uploads/pdfs"
        os.makedirs(uploads_dir, exist_ok=True)
        
        dest_path = os.path.join(uploads_dir, filename)
        import shutil
        shutil.copy2(pdf_path, dest_path)
        
        # Return relative URL (in production, return S3 URL)
        return f"/uploads/pdfs/{filename}"

