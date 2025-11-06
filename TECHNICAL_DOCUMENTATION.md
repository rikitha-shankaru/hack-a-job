# Hack-A-Job: Complete Technical Documentation

## 🏗️ Architecture Overview

Hack-A-Job is a full-stack AI-powered job application assistant built with:
- **Backend**: FastAPI (Python) with PostgreSQL + pgvector
- **Frontend**: Next.js 14 + React + TypeScript + Tailwind CSS
- **AI**: Google Gemini API for LLM tasks
- **Automation**: Playwright for browser automation
- **Workflow**: LangGraph for orchestration

---

## 📁 Project Structure

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
│   │   │   ├── job_parser.py       # Job posting parser (JSON-LD/HTML)
│   │   │   ├── pdf_parser.py        # PDF resume parser
│   │   │   ├── latex_generator.py  # LaTeX resume generator
│   │   │   ├── latex_compiler.py    # LaTeX to PDF compiler
│   │   │   └── pdf_generator.py     # ReportLab PDF generator (fallback)
│   │   └── workflows/      # LangGraph workflows
│   │       └── job_application_workflow.py
│   └── requirements.txt
│
└── frontend/                # Next.js frontend
    ├── app/                # Next.js App Router
    │   ├── page.tsx        # Landing page (collects target role, location, recency)
    │   ├── upload/         # Resume upload page (drag-and-drop, file upload, paste)
    │   ├── jobs/           # Job search & listing pages (auto-searches after upload)
    │   │   └── [id]/
    │   │       └── tailor/  # Resume tailoring page (with apply options)
    │   ├── autofill/       # Autofill verification page
    │   └── verify/         # Application verification page
    └── lib/
        └── api.ts          # API client utilities
```

---

## 🔧 Technology Stack Details

### Backend Stack

#### 1. **FastAPI** (v0.104.1)
- **Purpose**: Modern, fast Python web framework
- **Features Used**:
  - Async/await support for concurrent operations
  - Automatic API documentation (OpenAPI/Swagger)
  - Dependency injection for database sessions
  - CORS middleware for frontend communication
  - Static file serving for PDFs

#### 2. **PostgreSQL + pgvector**
- **Database**: PostgreSQL with pgvector extension
- **Purpose**: Store structured data + vector embeddings
- **Key Features**:
  - `JSONB` columns for flexible schema (resume JSON, job descriptions)
  - `Vector(1536)` for resume embeddings (semantic search)
  - Foreign keys with cascade deletes
  - UUID primary keys

#### 3. **SQLAlchemy** (v2.0.23)
- **ORM**: Object-Relational Mapping
- **Features**:
  - Declarative models
  - Relationship management (one-to-one, one-to-many)
  - Session management with dependency injection
  - Database migrations via Alembic

#### 4. **Google Gemini API** (v0.3.2)
- **Model**: `gemini-2.0-flash`
- **Uses**:
  - Resume parsing (text → structured JSON)
  - Resume tailoring (match job descriptions)
  - Cover letter generation
  - Application question answering
  - AI explanations & recommendations
  - Job match scoring

#### 5. **LangGraph** (v0.0.26)
- **Purpose**: Workflow orchestration
- **Workflow**: Collect Info → Upload → Auto-Search → Tailor → Cover Letter → Autofill → Email
- **State Management**: TypedDict for type-safe state

#### 6. **Playwright** (v1.40.0)
- **Purpose**: Browser automation for autofill
- **Features**:
  - Headless Chromium browser
  - Form field detection & filling
  - File uploads (resume/cover letter)
  - Screenshot capture
  - Question detection & AI answering

#### 7. **BeautifulSoup4** (v4.12.2)
- **Purpose**: HTML parsing for job postings
- **Features**:
  - Extract JSON-LD structured data
  - Fallback HTML parsing
  - Job description extraction

#### 8. **pypdf** (v3.17.1)
- **Purpose**: PDF resume parsing
- **Features**:
  - Extract text from PDFs
  - Structure analysis (sections, bullets)

#### 9. **LaTeX + pdflatex**
- **Purpose**: Preserve resume formatting
- **Flow**: PDF → Parse → LaTeX Template → Tailor → Compile → PDF

### Frontend Stack

#### 1. **Next.js 14** (App Router)
- **Framework**: React framework with App Router
- **Features**:
  - Server-side rendering (SSR)
  - File-based routing
  - API route proxying (optional)

#### 2. **React + TypeScript**
- **UI Library**: React with TypeScript
- **State Management**: React hooks (useState, useEffect)
- **Type Safety**: TypeScript for type checking

#### 3. **Tailwind CSS**
- **Styling**: Utility-first CSS framework
- **Features**: Responsive design, custom gradients

---

## 🔄 Complete Data Flow

### 0. **Landing Page - Collect Job Search Preferences**

```
User visits landing page
    ↓
AI collects:
  - Target job role (required)
  - Location (optional)
  - Job posting recency (d7/w2/m1)
    ↓
Data stored in localStorage
    ↓
Redirect to /upload
```

### 1. **Resume Upload & Parsing**

```
User uploads resume via:
  - Drag-and-drop PDF
  - File upload
  - Paste resume text
    ↓
[Frontend] POST /api/profile/ingest (multipart/form-data)
  - Includes: email, name, roleTarget (from landing page), levelTarget
    ↓
[Backend] profile.py → ProfileService.parse_resume()
    ↓
PDFParser.parse_pdf() → Extract text & structure (if PDF)
    ↓
GeminiClient.parse_resume() → Structured JSON
    ↓
Extract: skills, metrics, links, generate embedding
    ↓
Store in PostgreSQL:
  - User (email, name, role_target, level_target)
  - Profile (resume_json, resume_pdf_url, resume_latex_template, skills, metrics, links, resume_vector)
    ↓
[Frontend] Automatically triggers job search with stored preferences
    ↓
Redirect to /jobs?autoSearch=true&query=...&location=...&recency=...
```

**Key Files**:
- `backend/app/api/profile.py`: API endpoint
- `backend/app/services/profile_service.py`: Business logic
- `backend/app/utils/pdf_parser.py`: PDF parsing
- `backend/app/utils/gemini_client.py`: AI parsing

**Technical Details**:
- **PDF Parsing**: Uses `pypdf` to extract text, analyzes structure (sections, bullets)
- **AI Parsing**: Gemini API with JSON schema enforcement
- **LaTeX Template**: Generated from PDF structure to preserve formatting
- **Embedding**: 1536-dim vector for semantic search (currently hash-based fallback)

---

### 2. **Job Search (Auto-Triggered)**

```
After resume upload OR manual search:
    ↓
[Frontend] POST /api/jobs/search
  - Query: target role from landing page
  - Location: from landing page (if provided)
  - Recency: from landing page
    ↓
[Backend] jobs.py → JobService.search_and_store_jobs()
    ↓
Build Google CSE Query:
  "software engineer jobs in california (site:linkedin.com/jobs OR site:indeed.com ...)"
    ↓
Google Custom Search API (paginated: 4 pages, 10 results/page)
    ↓
For each result:
  - Filter non-job URLs (news, social media, .gov, .edu)
  - Fetch HTML with httpx
  - Pre-check for "no longer available" indicators
    ↓
JobParser.parse_job_posting():
  - Try JSON-LD extraction (schema.org/JobPosting)
  - Fallback to HTML parsing
  - Extract: title, company, location, date_posted, jd_text, keywords
    ↓
Validate Job:
  - Reject future dates
  - Reject generic titles ("Jobs JOBS FOUND", "Powered by people")
  - Reject career pages vs actual postings
  - Require job keywords in description
    ↓
Deduplicate by URL + title+company
    ↓
Store in PostgreSQL: Job table
    ↓
Return JobResponse[] to frontend
```

**Key Files**:
- `backend/app/api/jobs.py`: API endpoint
- `backend/app/services/job_service.py`: Search logic & filtering
- `backend/app/utils/job_parser.py`: HTML/JSON-LD parsing

**Technical Details**:
- **Google CSE**: Custom Search Engine with site restrictions
- **Date Parsing**: Multiple format support, rejects future dates
- **Filtering**: Multi-layer validation (URL, title, description, date)
- **Deduplication**: By URL and title+company combination

---

### 3. **Resume Tailoring**

```
User views job list → Clicks "Tailor" on a job
    ↓
[Frontend] Navigate to /jobs/[id]/tailor
    ↓
User clicks "Generate AI-Tailored Resume & Cover Letter"
    ↓
[Frontend] POST /api/tailor (userId, jobId)
    ↓
[Backend] tailor.py → TailorService.generate_tailored_assets()
    ↓
Get base resume from Profile.resume_json
Get job description from Job.jd_text
    ↓
GeminiClient.tailor_resume():
  - Input: base_resume_json, job_description, jd_keywords
  - Prompt: "Intelligently rewrite resume, match job description, preserve facts"
  - Output: Tailored resume JSON
    ↓
GeminiClient.generate_cover_letter():
  - Input: tailored_resume, job_description, company
  - Output: Cover letter JSON (opening, mapping bullets, closing)
    ↓
Generate Resume PDF:
  - Get original LaTeX template (if available)
  - LaTeXGenerator.generate_latex() → LaTeX content
  - LaTeXCompiler.compile_latex_to_pdf() → PDF (pdflatex)
  - Fallback: PDFGenerator (ReportLab) if LaTeX fails
    ↓
Generate Cover Letter PDF:
  - PDFGenerator.generate_cover_letter_pdf() → PDF
    ↓
AI Insights:
  - GeminiClient.generate_ai_explanation() → Why changes were made
  - GeminiClient.generate_ai_recommendations() → Improvement suggestions
  - GeminiClient.calculate_job_match_score() → Match score (0-100)
    ↓
Store in PostgreSQL:
  - TailoredAsset (resume_json, resume_pdf_url, cover_json, cover_pdf_url, diffs)
    ↓
Return TailorResponse with PDF URLs
```

**Key Files**:
- `backend/app/api/tailor.py`: API endpoint
- `backend/app/services/tailor_service.py`: Tailoring orchestration
- `backend/app/utils/gemini_client.py`: AI operations
- `backend/app/utils/latex_generator.py`: LaTeX generation
- `backend/app/utils/latex_compiler.py`: PDF compilation

**Technical Details**:
- **Resume Tailoring**: Gemini rewrites bullets, reorders sections, matches keywords
- **Fact Preservation**: Validation ensures no invented companies/titles/dates
- **LaTeX Preservation**: Maintains original formatting from uploaded PDF
- **AI Insights**: Explanation, recommendations, match score in diffs

---

### 4. **Apply Options (After Tailoring)**

```
After tailoring completes, user sees two options:

Option A: Manual Application
    ↓
User downloads tailored resume and cover letter PDFs
    ↓
User clicks "View Job Posting" → Opens job URL in new tab
    ↓
User manually applies using downloaded documents

Option B: AI Autofill Application
    ↓
User clicks "Start AI Autofill"
    ↓
[Frontend] POST /api/tailor/complete (userId, jobId)
    ↓
[Backend] tailor.py → JobApplicationWorkflow.run()
    ↓
LangGraph Workflow:
  
  Node 1: parse_resume
    - Get parsed resume from Profile.resume_json
    ↓
  Node 2: search_jobs
    - Skip (job already selected)
    ↓
  Node 3: tailor_resume
    - TailorService.generate_tailored_assets()
    - Store TailoredAsset
    ↓
  Node 4: generate_cover_letter
    - Get cover letter from TailoredAsset.cover_json
    ↓
  Node 5: autofill_application
    - AutofillService.run_autofill_with_questions()
    - Detect portal (greenhouse/lever)
    - Playwright: Fill form fields, upload files, answer questions with AI
    - Store AutofillRun with verification_url
    ↓
  Node 6: send_verification_email
    - EmailService.send_verification_email()
    - SMTP: Send HTML email with verification link
    ↓
Return: { verification_url, autofill_run_id }
```

**Key Files**:
- `backend/app/workflows/job_application_workflow.py`: LangGraph workflow
- `backend/app/services/autofill_service.py`: Autofill orchestration
- `backend/app/services/adapters/greenhouse_adapter.py`: Greenhouse-specific logic
- `backend/app/services/adapters/lever_adapter.py`: Lever-specific logic

**Technical Details**:
- **LangGraph**: State-based workflow with TypedDict
- **State**: user_id, job_id, parsed_resume, tailored_resume, cover_letter, autofill_run, verification_url
- **Nodes**: Each node is an async function that modifies state

---

### 5. **Autofill Application**

```
AutofillService.run_autofill_with_questions()
    ↓
Detect Portal: greenhouse.io or lever.co
    ↓
GreenhouseAdapter.autofill_with_questions():
  - Launch Playwright (headless Chromium)
  - Navigate to job URL
  - Take screenshot (before)
    ↓
Fill Basic Fields:
  - Name: User.name
  - Email: User.email
  - Phone: Extract from resume_json
  - Links: GitHub, LinkedIn from resume_json
    ↓
Upload Files:
  - Resume: TailoredAsset.resume_pdf_url
  - Cover Letter: TailoredAsset.cover_pdf_url
    ↓
Detect Questions:
  - Find textarea/input fields with question indicators
  - Extract question text (label, placeholder, aria-label)
    ↓
Answer Questions with AI:
  - GeminiClient.answer_application_question()
  - Input: question, resume_json, job_description
  - Output: Tailored answer
  - Fill field with answer
    ↓
Take screenshot (after)
    ↓
Store AutofillRun:
  - filled_fields: { field_name: value }
  - confidence: { field_name: 0.0-1.0 }
  - screenshots: [base64 encoded]
  - verification_url: Link to prefilled form
    ↓
Return AutofillRun
```

**Key Files**:
- `backend/app/services/autofill_service.py`: Portal detection & orchestration
- `backend/app/services/adapters/greenhouse_adapter.py`: Greenhouse form filling
- `backend/app/services/adapters/lever_adapter.py`: Lever form filling
- `backend/app/utils/gemini_client.py`: Question answering

**Technical Details**:
- **Playwright**: Headless browser automation
- **Field Detection**: CSS selectors, ARIA labels, placeholders
- **AI Question Answering**: Gemini generates context-aware answers
- **Confidence Scoring**: Per-field confidence (0.0-1.0)
- **Verification URL**: Link to prefilled form for user review

---

### 6. **Email Sending**

```
EmailService.send_verification_email()
    ↓
Build HTML Email:
  - Subject: "Verify Your Application - {job.title}"
  - Body: HTML with verification link, job details, instructions
    ↓
SMTP Connection:
  - Host: smtp.gmail.com:587
  - Auth: smtp_user, smtp_pass
  - TLS: starttls()
    ↓
Send Email:
  - From: from_email
  - To: user.email
  - Attach: HTML body
    ↓
Return verification_url
```

**Key Files**:
- `backend/app/services/email_service.py`: SMTP email sending

**Technical Details**:
- **SMTP**: Gmail SMTP server
- **HTML Email**: Formatted with inline CSS
- **Verification Link**: Points to prefilled application form

---

## 🗄️ Database Schema

### Tables

#### 1. **users**
```sql
- id: UUID (PK)
- email: String (unique)
- name: String
- role_target: String (e.g., "Software Engineer")
- level_target: String (e.g., "Senior")
- created_at: DateTime
```

#### 2. **profiles**
```sql
- user_id: UUID (PK, FK → users.id)
- resume_json: JSONB (structured resume data)
- resume_pdf_url: String (path to uploaded PDF)
- resume_latex_template: Text (LaTeX template)
- skills: JSONB (array of skills)
- metrics: JSONB (quantitative achievements)
- links: JSONB (GitHub, LinkedIn, etc.)
- resume_vector: Vector(1536) (embedding)
```

#### 3. **jobs**
```sql
- id: UUID (PK)
- company: String
- title: String
- location: String
- region: String
- remote: Boolean
- date_posted: Date
- valid_through: Date
- salary: JSONB
- url: String (unique)
- source: String (greenhouse/lever/linkedin/etc.)
- jd_text: Text (job description)
- jd_keywords: JSONB (extracted keywords)
- created_at: DateTime
```

#### 4. **tailored_assets**
```sql
- id: UUID (PK)
- user_id: UUID (FK → users.id)
- job_id: UUID (FK → jobs.id)
- resume_json: JSONB (tailored resume)
- resume_pdf_url: String
- cover_json: JSONB (cover letter)
- cover_pdf_url: String
- status: String ('draft' | 'emailed')
- created_at: DateTime
```

#### 5. **autofill_runs**
```sql
- id: UUID (PK)
- user_id: UUID (FK → users.id)
- job_id: UUID (FK → jobs.id)
- portal: String (greenhouse/lever/other)
- status: String ('prefilled' | 'needs_input' | 'submitted' | 'error')
- filled_fields: JSONB (field_name → value)
- confidence: JSONB (field_name → 0.0-1.0)
- screenshots: JSONB (array of base64 images)
- verification_url: String
- created_at: DateTime
```

---

## 🔐 API Endpoints

### Profile Endpoints

#### `POST /api/profile/ingest`
- **Purpose**: Upload and parse resume
- **Request**: `multipart/form-data`
  - `email`: String (required)
  - `name`: String (optional)
  - `roleTarget`: String (optional)
  - `levelTarget`: String (optional)
  - `resumeFile`: File (PDF, optional)
  - `resumeText`: String (optional)
- **Response**: `ProfileIngestResponse`
  - `userId`: UUID
  - `parsed`: { skills, metrics, links }
  - `resumeJson`: Object
  - `resumeVector`: Array[float]

### Job Endpoints

#### `POST /api/jobs/search`
- **Purpose**: Search for jobs
- **Request**: `JobSearchRequest`
  - `query`: String (required)
  - `location`: String (optional)
  - `recency`: String ('d7' | 'w2' | 'm1')
  - `roleTarget`: String (optional)
  - `levelTarget`: String (optional)
- **Response**: `JobSearchResponse`
  - `jobs`: Array[JobResponse]

### Tailor Endpoints

#### `POST /api/tailor`
- **Purpose**: Generate tailored resume and cover letter
- **Request**: `TailorRequest`
  - `userId`: UUID
  - `jobId`: UUID
- **Response**: `TailorResponse`
  - `assetsId`: UUID
  - `resumePdfUrl`: String
  - `coverPdfUrl`: String
  - `diffs`: Object (changes, AI insights)

#### `POST /api/tailor/complete`
- **Purpose**: Run complete workflow (tailor + autofill + email)
- **Request**: `TailorRequest`
- **Response**: `{ status, verification_url, autofill_run_id }`

### Autofill Endpoints

#### `POST /api/autofill/run`
- **Purpose**: Pre-fill job application form
- **Request**: `AutofillRunRequest`
  - `userId`: UUID
  - `jobId`: UUID
- **Response**: `AutofillRunResponse`
  - `runId`: UUID
  - `status`: String
  - `screenshots`: Array[String] (base64)
  - `confidence`: Object
  - `verification_url`: String

#### `POST /api/autofill/approve`
- **Purpose**: Approve/submit autofilled form
- **Request**: `AutofillApproveRequest`
  - `runId`: UUID
  - `submit`: Boolean
- **Response**: `AutofillApproveResponse`
  - `status`: String

### Email Endpoints

#### `POST /api/email/send`
- **Purpose**: Send tailored assets via email
- **Request**: `EmailSendRequest`
  - `userId`: UUID
  - `jobId`: UUID
  - `assetsId`: UUID
- **Response**: `EmailSendResponse`
  - `status`: String

---

## 🤖 AI Integration Details

### Google Gemini API Usage

#### 1. **Resume Parsing**
```python
prompt = f"Parse this resume text into structured JSON..."
response = gemini.generate_content(prompt)
# Returns: { summary, skills, experience, projects, education }
```

#### 2. **Resume Tailoring**
```python
prompt = f"""
You are an expert AI resume writer...
Base Resume: {base_resume_json}
Job Description: {job_description}
Output ONLY valid JSON with same structure...
"""
# Returns: Tailored resume JSON (rephrased, reordered, keyword-matched)
```

#### 3. **Cover Letter Generation**
```python
prompt = f"""
Write a concise cover letter...
Resume: {resume_json}
Company: {company}
Job Description: {job_description}
"""
# Returns: { opening, mapping: [bullets], closing }
```

#### 4. **Question Answering**
```python
prompt = f"""
Answer this job application question truthfully...
Question: {question}
Resume: {resume_json}
Job Description: {job_description}
"""
# Returns: Tailored answer string
```

#### 5. **AI Insights**
- **Explanation**: Why changes were made
- **Recommendations**: Improvement suggestions
- **Match Score**: 0-100 score with breakdown (skills, experience, keywords)

### Rate Limiting & Retry Logic

```python
async def _generate_with_retry(self, prompt: str, max_retries: int = 3):
    for attempt in range(max_retries):
        try:
            response = self.model.generate_content(prompt)
            return response
        except Exception as e:
            if "429" in str(e) or "Resource exhausted" in str(e):
                wait_time = (2 ** attempt) * 2  # Exponential backoff
                await asyncio.sleep(wait_time)
                continue
            raise
```

---

## 🎨 Frontend Architecture

### Next.js App Router Structure

```
app/
├── layout.tsx          # Root layout (providers, metadata)
├── page.tsx            # Home page
├── upload/
│   └── page.tsx        # Resume upload form
├── jobs/
│   ├── page.tsx         # Job search & listing
│   └── [id]/
│       └── tailor/
│           └── page.tsx  # Resume tailoring page
├── autofill/
│   └── [id]/
│       └── page.tsx     # Autofill verification
└── verify/
    └── [id]/
        └── page.tsx     # Application verification
```

### API Client (`lib/api.ts`)

```typescript
const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  headers: { 'Content-Type': 'application/json' }
});
```

### State Management

- **Local State**: React `useState` for form data
- **API Calls**: Axios with async/await
- **Error Handling**: Try/catch with user-friendly messages
- **Loading States**: Loading indicators during API calls

---

## 🔄 Request/Response Flow Example

### Complete User Journey

```
1. User visits landing page (/)
   → GET / (Next.js renders page.tsx)
   → User enters: target role, location (optional), job posting recency
   → Data stored in localStorage
   → Redirect to /upload

2. User uploads resume (/upload)
   → Drag-and-drop, file upload, or paste resume text
   → POST /api/profile/ingest (multipart/form-data)
   → Backend: Parse PDF → Gemini → Store in DB
   → Response: { userId, parsed, resumeJson }
   → Frontend: Store userId in localStorage
   → Automatically triggers job search with stored preferences
   → Redirect to /jobs?autoSearch=true&query=...&location=...&recency=...

3. Jobs auto-search (/jobs)
   → GET /jobs?autoSearch=true&query=...&location=...&recency=...
   → Frontend: Auto-triggers POST /api/jobs/search
   → Backend: Google CSE search → Parse → Filter → Store
   → Response: { jobs: [...] }
   → Frontend: Display job list
   → User clicks "Tailor" on a job → Navigate to /jobs/[id]/tailor

4. User tailors resume (/jobs/[id]/tailor)
   → User clicks "Generate AI-Tailored Resume & Cover Letter"
   → POST /api/tailor { userId, jobId }
   → Backend: Google CSE → Parse → Filter → Store → Return
   → Response: { jobs: [...] }
   → Frontend: Display job cards

4. User selects job → Clicks "Tailor"
   → POST /api/tailor { userId, jobId }
   → Backend: Gemini tailoring → LaTeX → PDF → Store
   → Response: { assetsId, resumePdfUrl, coverPdfUrl, diffs }
   → Frontend: Display tailored resume, cover letter, AI insights

5. User clicks "Run Complete Workflow"
   → POST /api/tailor/complete { userId, jobId }
   → Backend: LangGraph workflow
     - Tailor resume
     - Generate cover letter
     - Autofill application (Playwright)
     - Send verification email
   → Response: { verification_url }
   → Frontend: Show success message

6. User receives email
   → Email contains verification link
   → User clicks link → Opens prefilled application form
   → User reviews → Submits application
```

---

## 🛠️ Key Technical Decisions

### 1. **Why FastAPI?**
- Async/await for concurrent operations (job parsing, API calls)
- Automatic OpenAPI documentation
- Type validation with Pydantic
- High performance (comparable to Node.js)

### 2. **Why PostgreSQL + pgvector?**
- Structured data (users, jobs, assets)
- JSONB for flexible schema (resume JSON, job descriptions)
- Vector embeddings for semantic search (future enhancement)
- ACID compliance for data integrity

### 3. **Why Google Gemini?**
- User preference (wins prize!)
- Fast inference with `gemini-2.0-flash`
- Good JSON schema support
- Competitive pricing

### 4. **Why LangGraph?**
- Complex multi-step workflows
- State management across steps
- Easy to add/remove steps
- Type-safe state with TypedDict

### 5. **Why Playwright?**
- Modern browser automation
- Better than Selenium (faster, more reliable)
- Headless mode for server deployment
- Screenshot capture for verification

### 6. **Why LaTeX for Resumes?**
- Preserves original formatting
- Professional PDF output
- ATS-friendly (text-based)
- Template-based customization

---

## 🔒 Security Considerations

1. **API Keys**: Stored in `.env` file (not committed)
2. **CORS**: Restricted to localhost:3000, localhost:3001
3. **File Uploads**: Validated file types (PDF only)
4. **SQL Injection**: SQLAlchemy ORM prevents SQL injection
5. **XSS**: React escapes user input automatically
6. **Rate Limiting**: Exponential backoff for Gemini API

---

## 🚀 Deployment Considerations

### Backend
- **Server**: Uvicorn ASGI server
- **Database**: PostgreSQL with pgvector extension
- **Environment Variables**: `.env` file
- **Static Files**: `/uploads` directory (should use S3 in production)

### Frontend
- **Build**: `next build`
- **Server**: `next start` or Vercel/Netlify
- **Environment**: `NEXT_PUBLIC_API_URL` for API endpoint

### Required Services
- PostgreSQL database
- Google Custom Search Engine (CSE)
- Google Gemini API key
- SMTP server (Gmail)

---

## 📊 Performance Optimizations

1. **Async Operations**: All I/O operations are async
2. **Database Indexing**: UUID primary keys, unique constraints
3. **Caching**: Resume parsing cached in database
4. **Pagination**: Job search paginated (4 pages)
5. **Filtering**: Pre-filtering before parsing (saves time)
6. **Retry Logic**: Exponential backoff for API rate limits

---

## 🐛 Error Handling

1. **API Errors**: HTTPException with status codes
2. **Validation Errors**: Pydantic validation
3. **Database Errors**: SQLAlchemy exception handling
4. **AI Errors**: Retry logic with exponential backoff
5. **File Errors**: Try/except for file operations
6. **Frontend Errors**: Try/catch with user-friendly messages

---

## 📝 Future Enhancements

1. **Vector Search**: Use pgvector for semantic job matching
2. **Background Jobs**: RQ/Redis for async processing
3. **S3 Storage**: Store PDFs in S3 instead of local filesystem
4. **More Portals**: Add support for more application portals
5. **Analytics**: Track application success rates
6. **A/B Testing**: Test different resume versions

---

## 🔍 Debugging Tips

1. **Backend Logs**: Check uvicorn console output
2. **Database**: Use `psql` to query tables directly
3. **API Docs**: Visit `http://localhost:8000/docs` for Swagger UI
4. **Frontend**: Browser DevTools for network requests
5. **Playwright**: Set `headless=False` to see browser actions
6. **Gemini**: Check API response in console logs

---

This documentation covers all technical aspects of the Hack-A-Job project. For specific implementation details, refer to the source code files mentioned in each section.

