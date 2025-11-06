from playwright.async_api import async_playwright, Page
from app.models import User, TailoredAsset, AutofillRun
from app.utils.gemini_client import GeminiClient
from typing import Dict, Any, List
import base64
import os
import uuid

class GreenhouseAdapter:
    """Adapter for Greenhouse application portals"""
    
    async def autofill(
        self,
        job_url: str,
        user: User,
        assets: TailoredAsset
    ) -> Dict[str, Any]:
        """Autofill Greenhouse form"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                await page.goto(job_url)
                
                filled_fields = {}
                confidence = {}
                screenshots = []
                
                # Wait for form to load
                await page.wait_for_load_state("networkidle")
                
                # Take initial screenshot
                screenshot = await page.screenshot()
                screenshots.append(base64.b64encode(screenshot).decode())
                
                # Fill basic fields
                await self._fill_name(page, user, filled_fields, confidence)
                await self._fill_email(page, user, filled_fields, confidence)
                await self._fill_phone(page, user, filled_fields, confidence)
                await self._fill_links(page, user, filled_fields, confidence)
                
                # Upload resume
                await self._upload_resume(page, assets, filled_fields, confidence)
                
                # Upload cover letter if available
                await self._upload_cover_letter(page, assets, filled_fields, confidence)
                
                # Fill additional information with tailored bullets
                await self._fill_additional_info(page, assets, filled_fields, confidence)
                
                # Take final screenshot
                screenshot = await page.screenshot()
                screenshots.append(base64.b64encode(screenshot).decode())
                
                await browser.close()
                
                return {
                    "filled_fields": filled_fields,
                    "confidence": confidence,
                    "screenshots": screenshots
                }
            except Exception as e:
                await browser.close()
                raise Exception(f"Autofill failed: {str(e)}")
    
    async def _fill_name(self, page: Page, user: User, filled: Dict, confidence: Dict):
        """Fill name field"""
        selectors = [
            'input[name*="name"]',
            'input[aria-label*="name" i]',
            'input[id*="name"]',
            'input[data-testid*="name"]'
        ]
        
        for selector in selectors:
            try:
                field = await page.query_selector(selector)
                if field:
                    await field.fill(user.name or "")
                    filled["name"] = user.name
                    confidence["name"] = 0.9
                    return
            except:
                continue
        
        confidence["name"] = 0.0
    
    async def _fill_email(self, page: Page, user: User, filled: Dict, confidence: Dict):
        """Fill email field"""
        selectors = [
            'input[type="email"]',
            'input[name*="email"]',
            'input[aria-label*="email" i]'
        ]
        
        for selector in selectors:
            try:
                field = await page.query_selector(selector)
                if field:
                    await field.fill(user.email)
                    filled["email"] = user.email
                    confidence["email"] = 0.95
                    return
            except:
                continue
        
        confidence["email"] = 0.0
    
    async def _fill_phone(self, page: Page, user: User, filled: Dict, confidence: Dict):
        """Fill phone field"""
        selectors = [
            'input[type="tel"]',
            'input[name*="phone"]',
            'input[aria-label*="phone" i]'
        ]
        
        for selector in selectors:
            try:
                field = await page.query_selector(selector)
                if field:
                    # Phone number from profile links if available
                    phone = user.profile.links.get("phone") if user.profile and user.profile.links else None
                    if phone:
                        await field.fill(phone)
                        filled["phone"] = phone
                        confidence["phone"] = 0.8
                        return
            except:
                continue
        
        confidence["phone"] = 0.0
    
    async def _fill_links(self, page: Page, user: User, filled: Dict, confidence: Dict):
        """Fill portfolio/LinkedIn links"""
        if not user.profile or not user.profile.links:
            return
        
        links = user.profile.links
        link_selectors = [
            'input[name*="portfolio"]',
            'input[name*="linkedin"]',
            'input[name*="url"]',
            'input[aria-label*="url" i]'
        ]
        
        for selector in link_selectors:
            try:
                field = await page.query_selector(selector)
                if field:
                    label = await field.evaluate("el => el.getAttribute('aria-label') or el.getAttribute('name') or ''")
                    if "linkedin" in label.lower() and "linkedin" in links:
                        await field.fill(links["linkedin"])
                        filled["linkedin"] = links["linkedin"]
                        confidence["linkedin"] = 0.85
                    elif "portfolio" in label.lower() and "portfolio" in links:
                        await field.fill(links["portfolio"])
                        filled["portfolio"] = links["portfolio"]
                        confidence["portfolio"] = 0.85
            except:
                continue
    
    async def _upload_resume(self, page: Page, assets: TailoredAsset, filled: Dict, confidence: Dict):
        """Upload resume PDF"""
        selectors = [
            'input[type="file"]',
            'input[accept*="pdf"]',
            'input[name*="resume"]',
            'input[name*="cv"]'
        ]
        
        for selector in selectors:
            try:
                field = await page.query_selector(selector)
                if field:
                    pdf_path = assets.resume_pdf_url.lstrip('/')
                    if os.path.exists(pdf_path):
                        await field.set_input_files(pdf_path)
                        filled["resume"] = pdf_path
                        confidence["resume"] = 0.9
                        return
            except:
                continue
        
        confidence["resume"] = 0.0
    
    async def _upload_cover_letter(self, page: Page, assets: TailoredAsset, filled: Dict, confidence: Dict):
        """Upload cover letter PDF"""
        selectors = [
            'input[type="file"][name*="cover"]',
            'input[type="file"][name*="letter"]'
        ]
        
        for selector in selectors:
            try:
                field = await page.query_selector(selector)
                if field:
                    pdf_path = assets.cover_pdf_url.lstrip('/')
                    if os.path.exists(pdf_path):
                        await field.set_input_files(pdf_path)
                        filled["cover_letter"] = pdf_path
                        confidence["cover_letter"] = 0.85
                        return
            except:
                continue
        
        confidence["cover_letter"] = 0.0
    
    async def _fill_additional_info(self, page: Page, assets: TailoredAsset, filled: Dict, confidence: Dict):
        """Fill additional information textarea with tailored bullets"""
        selectors = [
            'textarea[name*="additional"]',
            'textarea[name*="other"]',
            'textarea[aria-label*="additional" i]'
        ]
        
        # Extract key bullets from tailored resume
        resume_json = assets.resume_json
        bullets = []
        for exp in resume_json.get("experience", [])[:2]:  # Top 2 experiences
            bullets.extend(exp.get("bullets", [])[:2])  # Top 2 bullets each
        
        if bullets:
            text = "\n".join(bullets)
            for selector in selectors:
                try:
                    field = await page.query_selector(selector)
                    if field:
                        await field.fill(text)
                        filled["additional_info"] = text[:200]
                        confidence["additional_info"] = 0.7
                        return
                except:
                    continue
        
        confidence["additional_info"] = 0.0
    
    async def autofill_with_questions(
        self,
        job_url: str,
        user: User,
        assets: TailoredAsset,
        resume_json: Dict[str, Any],
        cover_letter: Dict[str, Any],
        job_description: str
    ) -> Dict[str, Any]:
        """Autofill Greenhouse form including AI-powered question answering"""
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
                
                # Take initial screenshot
                screenshot = await page.screenshot()
                screenshots.append(base64.b64encode(screenshot).decode())
                
                # Fill basic fields
                await self._fill_name(page, user, filled_fields, confidence)
                await self._fill_email(page, user, filled_fields, confidence)
                await self._fill_phone(page, user, filled_fields, confidence)
                await self._fill_links(page, user, filled_fields, confidence)
                
                # Upload resume
                await self._upload_resume(page, assets, filled_fields, confidence)
                
                # Upload cover letter
                await self._upload_cover_letter(page, assets, filled_fields, confidence)
                
                # Fill additional information
                await self._fill_additional_info(page, assets, filled_fields, confidence)
                
                # Handle questions using Gemini AI
                await self._fill_questions_with_ai(
                    page, gemini, resume_json, job_description, filled_fields, confidence
                )
                
                # Take final screenshot
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
        # Find all textarea and input fields that might be questions
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
                    # Get the question text (from label, placeholder, or nearby text)
                    question_text = await self._extract_question_text(page, field)
                    
                    if question_text and len(question_text) > 10:  # Valid question
                        # Use Gemini to answer
                        answer = await gemini.answer_application_question(
                            question=question_text,
                            resume_json=resume_json,
                            job_description=job_description
                        )
                        
                        # Fill the field
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
        # Try to get label text
        field_id = await field.get_attribute("id")
        if field_id:
            label = await page.query_selector(f'label[for="{field_id}"]')
            if label:
                label_text = await label.inner_text()
                if label_text:
                    return label_text.strip()
        
        # Try placeholder
        placeholder = await field.get_attribute("placeholder")
        if placeholder:
            return placeholder.strip()
        
        # Try aria-label
        aria_label = await field.get_attribute("aria-label")
        if aria_label:
            return aria_label.strip()
        
        # Try to find nearby text
        try:
            parent = await field.evaluate_handle("el => el.parentElement")
            if parent:
                text = await parent.inner_text()
                if text and len(text) < 200:
                    return text.strip()
        except:
            pass
        
        return ""
    
    async def submit(self, run: AutofillRun):
        """Submit the form"""
        # This would navigate to the form and submit
        # For MVP, we'll leave this as a placeholder
        pass

