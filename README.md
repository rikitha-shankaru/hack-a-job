# 🤖 Hack-A-Job

**AI-Powered Job Application Assistant** - Automated resume tailoring, cover letter generation, and intelligent application form filling.

## ✨ Features

- **🤖 AI Resume Parsing**: Extract structured data from PDF resumes using Google Gemini
- **🔍 Job Discovery**: Search for jobs using Google Custom Search API
- **📝 Intelligent Parsing**: Extract job postings from JSON-LD or HTML
- **🎯 AI Resume Tailoring**: Gemini-powered resume customization per job (preserves format via LaTeX)
- **✉️ AI Cover Letter Generation**: Automated, personalized cover letters
- **📄 PDF Generation**: ATS-friendly resumes and cover letters with format preservation
- **🤖 AI Question Answering**: Automatically answers application form questions using Gemini
- **📧 Email Delivery**: Send verification links for autofilled applications
- **🚀 Complete Automation**: LangGraph workflow orchestrates entire process

## 🛠️ Tech Stack

- **Frontend**: Next.js 14, React, Tailwind CSS
- **Backend**: FastAPI (Python)
- **Workflow**: LangGraph for orchestration
- **AI**: Google Gemini API (Gemini Pro)
- **Database**: PostgreSQL with pgvector
- **Search**: Google Custom Search JSON API
- **Formatting**: LaTeX/Overleaf for resume preservation
- **Autofill**: Playwright + Gemini for intelligent form filling

## Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 14+ with pgvector extension (or Docker)
- Redis (optional, for background jobs)

**macOS:**
- PostgreSQL can be installed via Homebrew or Docker
- Docker Desktop recommended for easiest setup

**Windows:**
- PostgreSQL can be installed via installer or Docker
- Docker Desktop recommended for easiest setup

### Backend Setup

**macOS/Linux:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Windows:**
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys:
# - GOOGLE_GEMINI_API_KEY (required)
# - GOOGLE_CSE_KEY (required)
# - GOOGLE_CSE_CX (required)
# - DATABASE_URL (required)
# - SMTP credentials (for email)
```

Run migrations:
```bash
alembic upgrade head
```

Start the server:
```bash
uvicorn app.main:app --reload
```

### Frontend Setup

```bash
cd frontend
npm install
```

Start the dev server:
```bash
npm run dev
```

## 🚀 Complete Workflow

```
Upload PDF Resume → Parse (Gemini) → Search Jobs → 
Tailor Resume (Gemini + LaTeX) → Generate Cover Letter (Gemini) → 
Autofill Application (Playwright + Gemini Questions) → 
Send Verification Email
```

## 📡 API Endpoints

- `POST /api/profile/ingest` - Upload and parse resume (PDF or text)
- `POST /api/jobs/search` - Search for jobs using Google Custom Search
- `POST /api/tailor` - Generate tailored resume and cover letter
- `POST /api/tailor/complete` - **Run complete LangGraph workflow** ⭐
- `POST /api/autofill/run` - Pre-fill application portal with AI question answering
- `POST /api/autofill/approve` - Approve and submit application
- `POST /api/email/send` - Send assets via email

## Project Structure

```
backend/
  app/
    main.py          # FastAPI app
    models.py        # SQLAlchemy models
    schemas.py       # Pydantic schemas
    api/             # API routes
    services/        # Business logic
    utils/           # Utilities
  alembic/           # Database migrations

frontend/
  app/               # Next.js app directory
  components/        # React components
  lib/               # Utilities
  public/            # Static assets
```

