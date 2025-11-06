from typing import TypedDict, Optional, Any
from langgraph.graph import StateGraph, END
from app.models import User, Job, TailoredAsset, AutofillRun
from sqlalchemy.orm import Session
from typing import Dict
import uuid

class WorkflowState(TypedDict):
    """State for the LangGraph workflow"""
    user_id: str
    job_id: str
    resume_pdf_path: str
    parsed_resume: Dict[str, Any]
    jobs: list
    selected_job: Optional[Any]  # Job object
    tailored_resume: Dict[str, Any]
    cover_letter: Dict[str, Any]
    autofill_run: Optional[Any]  # AutofillRun object
    verification_url: str
    db: Optional[Any]  # Session object

class JobApplicationWorkflow:
    """LangGraph workflow for complete job application process"""
    
    def __init__(self, db: Session):
        self.db = db
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow"""
        workflow = StateGraph(WorkflowState)
        
        # Add nodes
        workflow.add_node("parse_resume", self._parse_resume)
        workflow.add_node("search_jobs", self._search_jobs)
        workflow.add_node("tailor_resume", self._tailor_resume)
        workflow.add_node("generate_cover_letter", self._generate_cover_letter)
        workflow.add_node("autofill_application", self._autofill_application)
        workflow.add_node("send_verification_email", self._send_verification_email)
        
        # Define edges
        workflow.set_entry_point("parse_resume")
        workflow.add_edge("parse_resume", "search_jobs")
        workflow.add_edge("search_jobs", "tailor_resume")
        workflow.add_edge("tailor_resume", "generate_cover_letter")
        workflow.add_edge("generate_cover_letter", "autofill_application")
        workflow.add_edge("autofill_application", "send_verification_email")
        workflow.add_edge("send_verification_email", END)
        
        return workflow.compile()
    
    async def _parse_resume(self, state: WorkflowState) -> WorkflowState:
        """Parse uploaded resume"""
        # Resume already parsed during upload, just get it from profile
        user = self.db.query(User).filter(User.id == state["user_id"]).first()
        if user and user.profile:
            state["parsed_resume"] = user.profile.resume_json
        else:
            # Fallback: parse from PDF if needed
            from app.services.profile_service import ProfileService
            service = ProfileService()
            resume_data = await service.parse_resume(
                resume_pdf_path=state["resume_pdf_path"]
            )
            state["parsed_resume"] = resume_data["resume_json"]
        return state
    
    async def _search_jobs(self, state: WorkflowState) -> WorkflowState:
        """Search for jobs using Google Custom Search"""
        # Job already selected, skip search
        # In full workflow, this would search, but for now we use the provided job_id
        return state
    
    async def _tailor_resume(self, state: WorkflowState) -> WorkflowState:
        """Tailor resume for selected job"""
        from app.services.tailor_service import TailorService
        
        user = self.db.query(User).filter(User.id == state["user_id"]).first()
        job = self.db.query(Job).filter(Job.id == state["job_id"]).first()
        
        # Use TailorService which handles Gemini + LaTeX
        service = TailorService()
        assets = await service.generate_tailored_assets(
            user=user,
            job=job,
            db=self.db
        )
        
        state["tailored_resume"] = assets.resume_json
        state["selected_job"] = job
        return state
    
    async def _generate_cover_letter(self, state: WorkflowState) -> WorkflowState:
        """Generate cover letter"""
        # Cover letter already generated in tailor step
        # Get it from the tailored assets
        from app.models import TailoredAsset
        
        user = self.db.query(User).filter(User.id == state["user_id"]).first()
        job = state["selected_job"]
        
        assets = self.db.query(TailoredAsset).filter(
            TailoredAsset.user_id == user.id,
            TailoredAsset.job_id == job.id
        ).order_by(TailoredAsset.created_at.desc()).first()
        
        if assets:
            state["cover_letter"] = assets.cover_json
        return state
    
    async def _autofill_application(self, state: WorkflowState) -> WorkflowState:
        """Autofill job application including questions"""
        from app.services.autofill_service import AutofillService
        
        user = self.db.query(User).filter(User.id == state["user_id"]).first()
        job = state["selected_job"]
        
        service = AutofillService()
        autofill_run = await service.run_autofill_with_questions(
            user=user,
            job=job,
            resume_json=state["tailored_resume"],
            cover_letter=state["cover_letter"],
            db=self.db
        )
        
        state["autofill_run"] = autofill_run
        return state
    
    async def _send_verification_email(self, state: WorkflowState) -> WorkflowState:
        """Send verification email with link"""
        from app.services.email_service import EmailService
        
        user = self.db.query(User).filter(User.id == state["user_id"]).first()
        autofill_run = state["autofill_run"]
        
        if autofill_run:
            service = EmailService()
            verification_url = await service.send_verification_email(
                user=user,
                autofill_run=autofill_run,
                db_session=self.db
            )
            state["verification_url"] = verification_url
        else:
            state["verification_url"] = ""
        return state
    
    async def run(self, user_id: str, job_id: str, resume_pdf_path: str) -> Dict[str, Any]:
        """Run the complete workflow"""
        initial_state: WorkflowState = {
            "user_id": user_id,
            "job_id": job_id,
            "resume_pdf_path": resume_pdf_path,
            "parsed_resume": {},
            "jobs": [],
            "selected_job": None,
            "tailored_resume": {},
            "cover_letter": {},
            "autofill_run": None,
            "verification_url": "",
            "db": self.db
        }
        
        result = await self.graph.ainvoke(initial_state)
        return result

