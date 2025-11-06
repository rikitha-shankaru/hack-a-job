from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Google Custom Search
    google_cse_key: str
    google_cse_cx: str
    
    # Google Gemini
    google_gemini_api_key: str
    
    # OpenAI (optional - falls back to Gemini if not provided)
    openai_api_key: Optional[str] = None
    
    # Database
    database_url: str
    
    # SMTP
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str
    smtp_pass: str
    from_email: str
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()

