from app.config import settings
from app.models import User, TailoredAsset
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os

class EmailService:
    def __init__(self):
        self.smtp_host = settings.smtp_host
        self.smtp_port = settings.smtp_port
        self.smtp_user = settings.smtp_user
        self.smtp_pass = settings.smtp_pass
        self.from_email = settings.from_email
    
    async def send_assets_email(self, user: User, assets: TailoredAsset):
        """Send tailored resume and cover letter via email"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = user.email
            msg['Subject'] = f"Tailored Resume and Cover Letter - {assets.job.title if assets.job else 'Job Application'}"
            
            # Email body
            body = f"""
            Hi {user.name or 'there'},
            
            Your tailored resume and cover letter are ready!
            
            Job: {assets.job.title if assets.job else 'N/A'} at {assets.job.company if assets.job else 'N/A'}
            
            Please find the attached files:
            - Tailored Resume
            - Cover Letter
            
            Best regards,
            Hack-A-Job Team
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Attach resume PDF
            if assets.resume_pdf_url:
                resume_path = assets.resume_pdf_url.lstrip('/')
                if os.path.exists(resume_path):
                    with open(resume_path, 'rb') as f:
                        resume_attachment = MIMEBase('application', 'octet-stream')
                        resume_attachment.set_payload(f.read())
                        encoders.encode_base64(resume_attachment)
                        resume_attachment.add_header(
                            'Content-Disposition',
                            f'attachment; filename=resume.pdf'
                        )
                        msg.attach(resume_attachment)
            
            # Attach cover letter PDF
            if assets.cover_pdf_url:
                cover_path = assets.cover_pdf_url.lstrip('/')
                if os.path.exists(cover_path):
                    with open(cover_path, 'rb') as f:
                        cover_attachment = MIMEBase('application', 'octet-stream')
                        cover_attachment.set_payload(f.read())
                        encoders.encode_base64(cover_attachment)
                        cover_attachment.add_header(
                            'Content-Disposition',
                            f'attachment; filename=cover_letter.pdf'
                        )
                        msg.attach(cover_attachment)
            
            # Send email
            server = smtplib.SMTP(self.smtp_host, self.smtp_port)
            server.starttls()
            server.login(self.smtp_user, self.smtp_pass)
            server.send_message(msg)
            server.quit()
            
        except Exception as e:
            # Store assets and show download link instead of crashing
            raise Exception(f"Failed to send email: {str(e)}. Assets are available for download.")
    
    async def send_verification_email(self, user: User, autofill_run) -> str:
        """Send verification email with link to autofilled application"""
        from app.models import AutofillRun, Job
        
        if isinstance(autofill_run, AutofillRun):
            run = autofill_run
        else:
            # If it's a dict, extract the run
            run = autofill_run
        
        # Get job from database
        job = None
        if hasattr(run, 'job') and run.job:
            job = run.job
        elif hasattr(run, 'job_id') and db_session:
            job = db_session.query(Job).filter(Job.id == run.job_id).first()
        
        try:
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = user.email
            msg['Subject'] = f"Verify Your Application - {job.title if job else 'Job Application'}"
            
            verification_url = run.verification_url or f"http://localhost:3000/verify/{run.id}"
            
            # HTML email body
            body_html = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #4F46E5;">🤖 AI Application Ready for Review</h2>
                    
                    <p>Hi {user.name or 'there'},</p>
                    
                    <p>Your job application has been automatically filled using AI! Please review and verify the information before submitting.</p>
                    
                    <div style="background-color: #F3F4F6; padding: 15px; border-radius: 8px; margin: 20px 0;">
                        <p style="margin: 0;"><strong>Job:</strong> {job.title if job else 'N/A'} at {job.company if job else 'N/A'}</p>
                        <p style="margin: 5px 0 0 0;"><strong>Application Status:</strong> Pre-filled and ready for review</p>
                    </div>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{verification_url}" 
                           style="background-color: #4F46E5; color: white; padding: 12px 30px; 
                                  text-decoration: none; border-radius: 6px; display: inline-block; 
                                  font-weight: bold;">
                            ✨ Review & Verify Application
                        </a>
                    </div>
                    
                    <p style="color: #6B7280; font-size: 14px;">
                        <strong>What to check:</strong><br>
                        • All personal information is correct<br>
                        • Resume and cover letter are attached<br>
                        • All questions are answered appropriately<br>
                        • Ready to submit when you're satisfied
                    </p>
                    
                    <p style="color: #6B7280; font-size: 12px; margin-top: 30px;">
                        This link will expire in 24 hours for security purposes.
                    </p>
                    
                    <p>Best regards,<br>Hack-A-Job AI Team</p>
                </div>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(body_html, 'html'))
            
            # Send email
            server = smtplib.SMTP(self.smtp_host, self.smtp_port)
            server.starttls()
            server.login(self.smtp_user, self.smtp_pass)
            server.send_message(msg)
            server.quit()
            
            return verification_url
            
        except Exception as e:
            raise Exception(f"Failed to send verification email: {str(e)}")

