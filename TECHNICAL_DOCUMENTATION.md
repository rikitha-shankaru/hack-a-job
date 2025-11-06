# Hack-A-Job Technical Documentation

## Overview

Hack-A-Job is a full-stack web application that helps job seekers find relevant positions and automatically tailor their resumes and cover letters. The system uses AI to parse resumes, search for jobs, customize application materials, and can even pre-fill job application forms.

The tech stack is pretty straightforward: FastAPI for the backend, Next.js 14 for the frontend, PostgreSQL for data storage, and Google Gemini API (with OpenAI as a fallback) for all the AI work. We also use Playwright for browser automation when filling out applications.

## Project Structure

```
Hack-A-Job/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── main.py         # FastAPI app entry point
│   │   ├── config.py       # Configuration & environment variables
│   │   ├── database.py     # SQLAlchemy setup
│   │   ├── models.py       # Database models (SQLAlchemy ORM)
│   │   ├── schemas.py      # Pydantic schemas for API validation
│   │   ├── api/            # API route handlers
│   │   │   ├── profile.py  # Resume upload & parsing endpoints
│   │   │   ├── jobs.py     # Job search endpoints
│   │   │   ├── tailor.py   # Resume tailoring endpoints
│   │   │   ├── email.py    # Email sending endpoints
│   │   │   └── autofill.py # Autofill endpoints
│   │   ├── services/       # Business logic layer
│   │   │   ├── profile_service.py
│   │   │   ├── job_service.py
│   │   │   ├── tailor_service.py
│   │   │   ├── email_service.py
│   │   │   ├── autofill_service.py
│   │   │   └── adapters/   # Portal-specific adapters
│   │   │       ├── greenhouse_adapter.py
│   │   │       └── lever_adapter.py
│   │   ├── utils/          # Utility modules
│   │   │   ├── gemini_client.py    # Google Gemini API client
│   │   │   ├── openai_client.py    # OpenAI API client
│   │   │   ├── job_parser.py       # Job posting parser (JSON-LD/HTML)
│   │   │   ├── pdf_parser.py        # PDF resume parser
│   │   │   ├── pdf_to_latex.py      # PDF to LaTeX converter
│   │   │   ├── latex_generator.py  # LaTeX resume generator
│   │   │   ├── latex_compiler.py    # LaTeX to PDF compiler
│   │   │   └── pdf_generator.py     # ReportLab PDF generator (fallback)
│   │   └── workflows/      # LangGraph workflows
│   │       └── job_application_workflow.py
│   └── requirements.txt
│
└── frontend/                # Next.js frontend
    ├── app/                # Next.js App Router
    │   ├── layout.tsx      # Root layout with metadata
    │   ├── globals.css     # Global styles
    │   ├── page.tsx        # Landing page (collects job info + resume)
    │   ├── jobs/           # Job search & listing pages
    │   │   ├── page.tsx    # Jobs listing with inline tailoring
    │   │   └── [id]/
    │   │       └── tailor/  # Resume tailoring page (legacy)
    │   ├── autofill/       # Autofill verification page
    │   └── verify/         # Application verification page
    ├── components/         # Reusable React components
    │   └── SkeletonLoader.tsx  # Loading skeletons
    ├── lib/
    │   └── api.ts          # API client utilities
    └── next.config.js      # Next.js configuration
```

## Technology Stack

### Backend

**FastAPI** - We chose FastAPI because it's fast, has great async support, and automatically generates API docs. The async/await pattern is crucial for handling multiple job searches and API calls concurrently.

**PostgreSQL + pgvector** - PostgreSQL stores all our structured data. We use JSONB columns for flexible schemas (like resume JSON and job descriptions) and pgvector for future semantic search capabilities. Right now we're using hash-based embeddings as a fallback.

**SQLAlchemy** - Handles all database operations. We use connection pooling (10 base connections, 20 overflow) to handle concurrent requests efficiently. Eager loading prevents N+1 query problems.

**Google Gemini API** - Primary AI service for parsing resumes, tailoring content, and generating cover letters. We use the `gemini-2.0-flash` model for speed and cost efficiency.

**OpenAI API** - Used as a fallback when Gemini fails or isn't configured. We prefer OpenAI for resume tailoring because it tends to produce better quality output, but Gemini is our primary choice for the competition.

**LangGraph** - Orchestrates the complete workflow from resume parsing to application submission. It manages state across multiple steps and makes it easy to add or remove workflow nodes.

**Playwright** - Handles browser automation for pre-filling job applications. It's faster and more reliable than Selenium, and works great in headless mode.

**BeautifulSoup4** - Parses HTML from job postings. We prefer JSON-LD structured data when available, but fall back to HTML parsing when needed.

**pypdf** - Extracts text and structure from PDF resumes. We analyze sections, bullets, and formatting to preserve the original layout.

**LaTeX + pdflatex** - When a user uploads a PDF resume, we convert it to LaTeX to preserve the exact formatting. Then when tailoring, we only replace the content while keeping all the original styling, borders, and spacing.

### Frontend

**Next.js 14** - React framework with App Router. We use it for server-side rendering, file-based routing, and built-in optimizations like image compression and code splitting.

**React + TypeScript** - TypeScript gives us type safety, and React hooks handle all state management. We use memoization (useMemo, useCallback) to prevent unnecessary re-renders.

**Tailwind CSS** - Utility-first CSS framework. Makes it easy to build responsive, modern UIs without writing custom CSS.

## How It Works

### Landing Page and Resume Upload

The user starts on the landing page where they enter their target job role, location (optional), and how recent they want job postings to be. On the same page, they can upload a PDF resume, paste resume text, or skip and let the AI generate a resume for them.

When a resume is uploaded, we parse it using pypdf to extract text and structure. If it's a PDF, we also convert it to a LaTeX template so we can preserve the exact formatting later. Then we send the text to Gemini (or OpenAI) to extract structured data like skills, experience, education, etc.

If the user doesn't provide a resume, we use AI to generate a realistic one based on their target role and level. This is useful for testing or when someone wants to see what a resume for a particular role might look like.

All this data gets stored in PostgreSQL - the user info, the parsed resume JSON, the LaTeX template (if available), and extracted skills/metrics/links.

### Job Search

After the resume is processed, the app automatically searches for jobs. The search uses Google Custom Search API with site restrictions to major job boards like LinkedIn, Indeed, Glassdoor, etc.

We build multiple search queries - a natural language query, keyword-based queries, and individual site-restricted queries for each job board. This mimics how Google's native job search works and gives us better results.

For each search result, we:
1. Filter out non-job URLs (news sites, social media, etc.)
2. Fetch the HTML page
3. Try to extract structured data from JSON-LD first
4. Fall back to HTML parsing if JSON-LD isn't available
5. Extract title, company, location, posting date, job description, and keywords
6. Validate the job (reject future dates, generic titles, etc.)
7. Deduplicate by URL and title+company combination

We cache search results for 5 minutes to avoid hitting the API too frequently. The frontend also stores results in localStorage so they persist when navigating between pages.

### Resume Tailoring

When a user clicks "Tailor" on a job listing, we take their original resume and the job description and use AI to customize it. The key here is that we preserve 95%+ of the original content - we're not rewriting everything, just making strategic edits.

The AI:
- Reorders sections to match job priorities
- Adds relevant keywords from the job description
- Adjusts bullet points to highlight matching experience
- Keeps all original facts (companies, titles, dates, metrics)
- Preserves the user's writing style and voice

We also check if the job description mentions a cover letter requirement. If it does, we generate one automatically.

For PDF generation, we use the LaTeX template from the original resume. We inject the tailored content into the template, preserving all formatting, borders, spacing, and fonts. If LaTeX generation fails, we fall back to ReportLab.

The tailored resume and cover letter are stored in the database, and we return URLs so the user can preview and download them.

### Application Options

After tailoring, users have two options:

**Manual Application** - They download the tailored resume and cover letter PDFs and apply manually through the job board.

**AI Autofill** - The system uses Playwright to navigate to the application form, detect the portal type (Greenhouse, Lever, etc.), fill in basic fields (name, email, phone, links), upload the resume and cover letter, and answer any application questions using AI.

For questions, we use Gemini to generate context-aware answers based on the user's resume and the job description. The answers are truthful and tailored, not generic.

After autofilling, we send the user an email with a verification link. They can review the prefilled form and submit it themselves. This approach respects the "pre-fill then user submits" requirement.

## Database Schema

**users** - Stores basic user info: email, name, target role, target level, creation timestamp.

**profiles** - One-to-one with users. Stores the parsed resume JSON, original PDF URL, LaTeX template, extracted skills/metrics/links, and resume embedding vector.

**jobs** - Stores job postings: company, title, location, posting date, URL, job description, extracted keywords, source (LinkedIn, Indeed, etc.).

**tailored_assets** - Stores tailored resumes and cover letters for specific jobs. Links user and job, stores the tailored resume JSON, PDF URLs, cover letter JSON, PDF URL, and any AI insights/diffs.

**autofill_runs** - Tracks autofill attempts. Stores which portal was used, what fields were filled, confidence scores, screenshots, and the verification URL.

## API Endpoints

**POST /api/profile/ingest** - Upload and parse a resume. Accepts multipart form data with email, name, role target, level target, and either a PDF file or resume text.

**POST /api/jobs/search** - Search for jobs. Takes query, location, and recency parameters. Returns up to 100 jobs. Results are cached for 5 minutes.

**POST /api/tailor** - Generate tailored resume and cover letter for a specific job. Takes userId and jobId, returns PDF URLs and any AI insights.

**POST /api/tailor/complete** - Run the complete workflow: tailor resume, generate cover letter, autofill application, and send verification email. Uses LangGraph to orchestrate all steps.

**POST /api/autofill/run** - Pre-fill a job application form. Detects the portal type, fills fields, uploads files, answers questions. Returns screenshots and verification URL.

**POST /api/email/send** - Send tailored assets via email. Used for verification emails with prefilled application links.

## Performance Optimizations

We've implemented several optimizations to make the app fast and responsive:

**Frontend:**
- Next.js compression and image optimization
- React memoization to prevent unnecessary re-renders
- Skeleton loaders for better perceived performance
- localStorage caching for instant page loads when navigating back

**Backend:**
- GZip compression reduces response sizes by 70-90%
- Database connection pooling (10 base + 20 overflow connections)
- Eager loading prevents N+1 queries
- API response caching (5-minute TTL for job searches)
- Query optimization with joinedload for related data

**Expected improvements:**
- Page load time: 40-60% faster
- Database queries: 50-70% reduction
- API response size: 70-90% smaller
- React re-renders: 60-80% reduction

## Security

API keys are stored in environment variables, never committed to git. CORS is restricted to localhost for development. File uploads are validated (PDF only). SQLAlchemy ORM prevents SQL injection. React automatically escapes user input to prevent XSS. We use exponential backoff for API rate limiting. Security headers are set in Next.js config. Personal PDFs are excluded from git via .gitignore. All API inputs are validated with Pydantic schemas. Error messages don't expose sensitive details.

## Deployment

**Backend:** Runs on Uvicorn ASGI server. Requires PostgreSQL with pgvector extension. Environment variables in .env file. Static files in /uploads directory (should use S3 in production). Connection pooling is configured. GZip compression is enabled.

**Frontend:** Build with `next build`, run with `next start` or deploy to Vercel/Netlify. Set NEXT_PUBLIC_API_URL environment variable. Static assets are cached for 1 year.

**Required Services:**
- PostgreSQL database (with connection pooling)
- Google Custom Search Engine (CSE)
- Google Gemini API key
- OpenAI API key (optional, for better quality)
- SMTP server (Gmail)

For production, consider using Redis for distributed caching instead of in-memory cache, adding database indexes on frequently queried columns, and using a CDN for static assets.

## Error Handling

API errors return proper HTTP status codes with descriptive messages. Validation errors use Pydantic to provide specific field-level feedback. Database errors are caught and converted to user-friendly messages. AI errors use exponential backoff retry logic. File operations are wrapped in try/except blocks. Frontend errors show user-friendly messages instead of technical details.

## Future Enhancements

Some ideas for future improvements:
- Use pgvector for semantic job matching instead of hash-based embeddings
- Add background job processing with RQ/Redis for long-running tasks
- Store PDFs in S3 instead of local filesystem
- Support more application portals beyond Greenhouse and Lever
- Track application success rates and provide analytics
- A/B test different resume versions to see what works best

## Debugging

Backend logs appear in the uvicorn console output. You can query the database directly with psql. API docs are available at http://localhost:8000/docs (Swagger UI). Frontend network requests can be inspected in browser DevTools. For Playwright debugging, set headless=False to see browser actions. Gemini API responses are logged to the console for debugging.

---

This documentation covers the main technical aspects of Hack-A-Job. For specific implementation details, check the source code files mentioned in each section.
