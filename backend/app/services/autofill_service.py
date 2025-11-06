from app.models import User, Job, AutofillRun
from app.services.adapters.greenhouse_adapter import GreenhouseAdapter
from app.services.adapters.lever_adapter import LeverAdapter
from sqlalchemy.orm import Session
from typing import Dict, Any
import uuid

class AutofillService:
    def __init__(self):
        self.greenhouse_adapter = GreenhouseAdapter()
        self.lever_adapter = LeverAdapter()
    
    async def run_autofill_with_questions(
        self,
        user: User,
        job: Job,
        resume_json: Dict[str, Any],
        cover_letter: Dict[str, Any],
        db: Session
    ) -> AutofillRun:
        """Run autofill including AI-powered question answering"""
        portal = self._detect_portal(job.url)
        
        # Get tailored assets
        from app.models import TailoredAsset
        assets = db.query(TailoredAsset).filter(
            TailoredAsset.user_id == user.id,
            TailoredAsset.job_id == job.id
        ).first()
        
        if not assets:
            raise ValueError("Tailored assets not found. Please generate them first.")
        
        # Run adapter with question handling
        if portal == "greenhouse":
            result = await self.greenhouse_adapter.autofill_with_questions(
                job_url=job.url,
                user=user,
                assets=assets,
                resume_json=resume_json,
                cover_letter=cover_letter,
                job_description=job.jd_text or ""
            )
        elif portal == "lever":
            result = await self.lever_adapter.autofill_with_questions(
                job_url=job.url,
                user=user,
                assets=assets,
                resume_json=resume_json,
                cover_letter=cover_letter,
                job_description=job.jd_text or ""
            )
        else:
            raise ValueError(f"Unsupported portal: {portal}")
        
        # Generate verification URL (in production, this would be a secure link)
        verification_url = f"http://localhost:3000/verify/{result.get('session_id', '')}"
        
        status = "prefilled"
        if result["confidence"]:
            min_confidence = min(result["confidence"].values())
            if min_confidence < 0.6:
                status = "error"
            elif min_confidence < 0.85:
                status = "needs_input"
        
        run = AutofillRun(
            id=uuid.uuid4(),
            user_id=user.id,
            job_id=job.id,
            portal=portal,
            status=status,
            filled_fields=result.get("filled_fields", {}),
            confidence=result.get("confidence", {}),
            screenshots=result.get("screenshots", []),
            verification_url=verification_url
        )
        
        db.add(run)
        db.commit()
        db.refresh(run)
        
        return run
    
    async def run_autofill(self, user: User, job: Job, db: Session) -> AutofillRun:
        """Run autofill for a job application portal"""
        # Detect portal type from URL
        portal = self._detect_portal(job.url)
        
        # Get tailored assets
        from app.models import TailoredAsset
        assets = db.query(TailoredAsset).filter(
            TailoredAsset.user_id == user.id,
            TailoredAsset.job_id == job.id
        ).first()
        
        if not assets:
            raise ValueError("Tailored assets not found. Please generate them first.")
        
        # Run adapter based on portal type
        if portal == "greenhouse":
            result = await self.greenhouse_adapter.autofill(
                job_url=job.url,
                user=user,
                assets=assets
            )
        elif portal == "lever":
            result = await self.lever_adapter.autofill(
                job_url=job.url,
                user=user,
                assets=assets
            )
        else:
            raise ValueError(f"Unsupported portal: {portal}")
        
        # Determine status based on confidence
        status = "prefilled"
        if result["confidence"]:
            min_confidence = min(result["confidence"].values())
            if min_confidence < 0.6:
                status = "error"
            elif min_confidence < 0.85:
                status = "needs_input"
        
        # Create autofill run record
        run = AutofillRun(
            id=uuid.uuid4(),
            user_id=user.id,
            job_id=job.id,
            portal=portal,
            status=status,
            filled_fields=result.get("filled_fields", {}),
            confidence=result.get("confidence", {}),
            screenshots=result.get("screenshots", [])
        )
        
        db.add(run)
        db.commit()
        db.refresh(run)
        
        return run
    
    async def submit_form(self, run: AutofillRun, db: Session):
        """Submit the autofilled form"""
        # Check confidence thresholds
        if run.confidence:
            min_confidence = min(run.confidence.values())
            if min_confidence < 0.6:
                raise ValueError("Cannot submit: confidence too low (< 0.6) for required fields")
        
        # Use adapter to submit
        if run.portal == "greenhouse":
            await self.greenhouse_adapter.submit(run)
        elif run.portal == "lever":
            await self.lever_adapter.submit(run)
        else:
            raise ValueError(f"Unsupported portal: {run.portal}")
    
    def _detect_portal(self, url: str) -> str:
        """Detect portal type from URL"""
        url_lower = url.lower()
        if "greenhouse.io" in url_lower or "boards.greenhouse.io" in url_lower:
            return "greenhouse"
        elif "lever.co" in url_lower or "jobs.lever.co" in url_lower:
            return "lever"
        else:
            return "other"

