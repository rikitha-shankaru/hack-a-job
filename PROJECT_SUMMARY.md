# Hack-A-Job - Project Summary

## ✅ Completed Features

### Backend (FastAPI)
- **Database Models**: All tables with PostgreSQL + pgvector support
- **API Endpoints**: All 6 endpoints implemented
  - Profile ingestion with resume parsing
  - Job search with Google Custom Search API
  - Resume tailoring and cover letter generation
  - Email sending with SMTP
  - Autofill run and approve (Phase-2 scaffold)

### Services Layer
- **ProfileService**: Resume parsing with OpenAI, skills/metrics extraction, embedding generation
- **JobService**: Google CSE integration, pagination, deduplication, job storage
- **TailorService**: Resume tailoring with validation, PDF generation, diff calculation
- **EmailService**: SMTP email sending with PDF attachments
- **AutofillService**: Portal detection, adapter routing, confidence scoring

### Utilities
- **JobParser**: JSON-LD extraction with BeautifulSoup HTML fallback
- **OpenAIClient**: Resume parsing, tailoring, cover letter generation with strict schemas
- **PDFGenerator**: ATS-friendly PDF generation for resumes and cover letters

### Adapters (Phase-2)
- **GreenhouseAdapter**: Form field detection, file uploads, confidence scoring
- **LeverAdapter**: Scaffold for Lever portal support

### Frontend (Next.js 14)
- **Home Page**: Landing page with navigation
- **Upload Page**: Resume upload form with role/level selection
- **Jobs Page**: Job search interface with filters
- **Tailor Page**: Resume tailoring interface with diff display
- **Autofill Page**: Form preview with confidence scores and screenshots

## 📁 Project Structure

```
backend/
  app/
    api/          # API route handlers
    models.py     # SQLAlchemy models
    schemas.py    # Pydantic schemas
    services/     # Business logic
    utils/        # Utilities (parsing, PDF, OpenAI)
  alembic/       # Database migrations

frontend/
  app/            # Next.js app directory
  lib/            # API client utilities
```

## 🔧 Setup Required

1. **Environment Variables**: Copy `.env.example` to `.env` and fill in:
   - Google Custom Search API key and CX
   - OpenAI API key
   - PostgreSQL connection string
   - SMTP credentials

2. **Database Setup**:
   ```sql
   CREATE DATABASE hackajob;
   CREATE EXTENSION vector;
   ```

3. **Install Dependencies**:
   ```bash
   # Backend
   cd backend
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   
   # Frontend
   cd frontend
   npm install
   ```

4. **Run Migrations**:
   ```bash
   alembic upgrade head
   ```

5. **Install Playwright** (for Phase-2):
   ```bash
   playwright install chromium
   ```

## 🚀 Running the Application

```bash
# Backend (port 8000)
cd backend
uvicorn app.main:app --reload

# Frontend (port 3000)
cd frontend
npm run dev
```

## 📝 Important Notes

1. **PDF Storage**: PDFs are stored locally in `uploads/pdfs/`. For production, use S3 or similar.

2. **Validation**: Resume tailoring includes strict validation to prevent fabricating employers, titles, dates, or metrics.

3. **Error Handling**: 
   - Email failures fall back to download links
   - LLM failures retry with stricter prompts
   - Low confidence autofill blocks submission

4. **Phase-2 Autofill**: 
   - Currently scaffolded with Greenhouse adapter
   - Requires manual testing with actual forms
   - Confidence thresholds: < 0.6 = error, < 0.85 = needs_input

## 🧪 Testing TODO

- Unit tests for JSON-LD parser variants
- Unit tests for tailoring validation
- Integration tests for Google CSE pagination
- E2E tests for Playwright autofill

## 🎯 Next Steps

1. Add unit tests for core services
2. Enhance HTML parsing fallback
3. Implement S3 storage for PDFs
4. Add user authentication
5. Complete Lever adapter implementation
6. Add more portal adapters (Workday, etc.)
7. Implement background job queue with RQ

