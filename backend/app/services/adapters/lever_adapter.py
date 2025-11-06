from playwright.async_api import async_playwright, Page
from app.models import User, TailoredAsset, AutofillRun
from typing import Dict, Any
import base64
import uuid

class LeverAdapter:
    """Adapter for Lever application portals"""
    
    async def autofill_with_questions(
        self,
        job_url: str,
        user: User,
        assets: TailoredAsset,
        resume_json: Dict[str, Any],
        cover_letter: Dict[str, Any],
        job_description: str
    ) -> Dict[str, Any]:
        """Autofill Lever form including AI-powered question answering"""
        from app.utils.gemini_client import GeminiClient
        
        gemini = GeminiClient()
        session_id = str(uuid.uuid4())
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                await page.goto(job_url)
                await page.wait_for_load_state("networkidle")
                
                filled_fields = {}
                confidence = {}
                screenshots = []
                
                screenshot = await page.screenshot()
                screenshots.append(base64.b64encode(screenshot).decode())
                
                # Lever-specific field filling (similar to Greenhouse)
                # Fill basic fields, upload files, etc.
                
                # Handle questions using Gemini AI
                await self._fill_questions_with_ai(
                    page, gemini, resume_json, job_description, filled_fields, confidence
                )
                
                screenshot = await page.screenshot()
                screenshots.append(base64.b64encode(screenshot).decode())
                
                await browser.close()
                
                return {
                    "filled_fields": filled_fields,
                    "confidence": confidence,
                    "screenshots": screenshots,
                    "session_id": session_id
                }
            except Exception as e:
                await browser.close()
                raise Exception(f"Autofill failed: {str(e)}")
    
    async def _fill_questions_with_ai(
        self,
        page: Page,
        gemini: GeminiClient,
        resume_json: Dict[str, Any],
        job_description: str,
        filled_fields: Dict,
        confidence: Dict
    ):
        """Use Gemini AI to answer application questions"""
        question_selectors = [
            'textarea[placeholder*="?"]',
            'textarea[aria-label*="?"]',
            'textarea[id*="question"]',
            'textarea[name*="question"]',
            'textarea[class*="question"]',
            'input[type="text"][placeholder*="?"]',
            'textarea:not([value]):not([disabled])'
        ]
        
        for selector in question_selectors:
            try:
                fields = await page.query_selector_all(selector)
                for field in fields:
                    question_text = await self._extract_question_text(page, field)
                    
                    if question_text and len(question_text) > 10:
                        answer = await gemini.answer_application_question(
                            question=question_text,
                            resume_json=resume_json,
                            job_description=job_description
                        )
                        
                        await field.fill(answer)
                        filled_fields[f"question_{len(filled_fields)}"] = {
                            "question": question_text,
                            "answer": answer
                        }
                        confidence[f"question_{len(confidence)}"] = 0.85
            except Exception as e:
                continue
    
    async def _extract_question_text(self, page: Page, field) -> str:
        """Extract question text from form field"""
        field_id = await field.get_attribute("id")
        if field_id:
            label = await page.query_selector(f'label[for="{field_id}"]')
            if label:
                label_text = await label.inner_text()
                if label_text:
                    return label_text.strip()
        
        placeholder = await field.get_attribute("placeholder")
        if placeholder:
            return placeholder.strip()
        
        aria_label = await field.get_attribute("aria-label")
        if aria_label:
            return aria_label.strip()
        
        return ""
    
    async def autofill(
        self,
        job_url: str,
        user: User,
        assets: TailoredAsset
    ) -> Dict[str, Any]:
        """Legacy autofill method (for backward compatibility)"""
        return await self.autofill_with_questions(
            job_url, user, assets, assets.resume_json, assets.cover_json, ""
        )
    
    async def submit(self, run: AutofillRun):
        """Submit the form"""
        pass

