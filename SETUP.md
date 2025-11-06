# Quick Start Guide

## Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 14+ with pgvector extension
- Redis (optional, for background jobs)

## Setup

### 1. Backend Setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and fill in your API keys:

```bash
cp .env.example .env
# Edit .env with your credentials
```

Set up PostgreSQL database:
```sql
CREATE DATABASE hackajob;
CREATE EXTENSION vector;
```

Run migrations:
```bash
alembic upgrade head
```

Start the server:
```bash
uvicorn app.main:app --reload
```

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The app will be available at `http://localhost:3000`

## API Endpoints

- `POST /api/profile/ingest` - Upload and parse resume
- `POST /api/jobs/search` - Search for jobs
- `POST /api/tailor` - Generate tailored resume and cover letter
- `POST /api/email/send` - Send assets via email
- `POST /api/autofill/run` - Pre-fill application portal (Phase-2)
- `POST /api/autofill/approve` - Approve and submit (Phase-2)

## Getting API Keys

1. **Google Custom Search API**:
   - Go to https://console.cloud.google.com/
   - Create a Custom Search Engine at https://programmablesearchengine.google.com/
   - Get API key from Google Cloud Console

2. **OpenAI API**:
   - Sign up at https://platform.openai.com/
   - Get API key from dashboard

3. **SMTP** (for email):
   - Use Gmail with App Password or any SMTP server

## Features

- ✅ Resume parsing and storage
- ✅ Job search via Google Custom Search
- ✅ JSON-LD and HTML parsing
- ✅ Resume tailoring with OpenAI
- ✅ Cover letter generation
- ✅ PDF generation
- ✅ Email delivery
- ✅ Phase-2 autofill scaffold (Greenhouse/Lever)

## Notes

- PDFs are stored locally in `uploads/pdfs/` directory
- In production, consider using S3 or similar for file storage
- Playwright browsers need to be installed: `playwright install chromium`

