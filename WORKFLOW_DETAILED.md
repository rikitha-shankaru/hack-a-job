# 🔄 Hack-A-Job Complete Workflow

## 📊 High-Level User Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER JOURNEY                                  │
└─────────────────────────────────────────────────────────────────┘

1. 📤 UPLOAD RESUME
   └─> User uploads PDF resume via frontend
       └─> Backend saves PDF and extracts text
           └─> Gemini parses resume → Structured JSON
               └─> Stored in database (User + Profile)

2. 🔍 SEARCH JOBS
   └─> User enters search query (role, location, etc.)
       └─> Google Custom Search API finds job postings
           └─> Parse job descriptions (JSON-LD or HTML)
               └─> Store jobs in database
                   └─> Display results to user

3. 🎯 SELECT JOB
   └─> User clicks on a job posting
       └─> User can either:
           ├─> Option A: Tailor resume only
           └─> Option B: Run complete workflow ⭐

4. 🚀 COMPLETE WORKFLOW (LangGraph Orchestration)
   │
   ├─> STEP 1: Parse Resume (if not already done)
   │   └─> Extract structured data using Gemini
   │
   ├─> STEP 2: Tailor Resume
   │   ├─> Gemini analyzes job description
   │   ├─> Rewrites resume bullets for ATS optimization
   │   ├─> Preserves format using LaTeX/Overleaf
   │   ├─> Generates AI explanations & match score
   │   └─> Creates tailored resume PDF
   │
   ├─> STEP 3: Generate Cover Letter
   │   ├─> Gemini creates personalized cover letter
   │   ├─> Maps candidate experience to job requirements
   │   └─> Generates cover letter PDF
   │
   ├─> STEP 4: Autofill Application
   │   ├─> Playwright opens job application page
   │   ├─> Fills basic fields (name, email, phone, links)
   │   ├─> Uploads resume and cover letter PDFs
   │   ├─> 🤖 AI Question Answering:
   │   │   ├─> Detects questions in form
   │   │   ├─> Uses Gemini to generate answers
   │   │   └─> Based on resume + job description
   │   ├─> Takes screenshots for verification
   │   └─> Stores autofill run with verification URL
   │
   └─> STEP 5: Send Verification Email
       ├─> Generates secure verification link
       ├─> Sends HTML email to user
       └─> User clicks link → Reviews application → Submits

5. ✅ VERIFICATION & SUBMISSION
   └─> User receives email with verification link
       └─> Reviews autofilled application
           └─> Approves and submits (or edits if needed)
```

## 🔧 Technical Implementation Flow

### LangGraph Workflow State Machine

```
┌─────────────────────────────────────────────────────────────┐
│              LANGGRAPH WORKFLOW STATE                       │
└─────────────────────────────────────────────────────────────┘

Entry Point: parse_resume
    │
    ├─> State: {user_id, job_id, resume_pdf_path, ...}
    │
    ▼
parse_resume_node
    │
    ├─> Load resume from profile OR parse PDF
    ├─> Use Gemini to extract structured data
    └─> Update state: parsed_resume
    │
    ▼
search_jobs_node (optional - job already selected)
    │
    ├─> Skip if job_id provided
    └─> Update state: jobs list
    │
    ▼
tailor_resume_node
    │
    ├─> Get user profile and job details
    ├─> Call TailorService:
    │   ├─> Gemini tailors resume JSON
    │   ├─> Generate LaTeX from tailored resume
    │   ├─> Compile LaTeX → PDF (preserves format)
    │   ├─> Generate AI explanations & match score
    │   └─> Store TailoredAsset in database
    ├─> Update state: tailored_resume, selected_job
    │
    ▼
generate_cover_letter_node
    │
    ├─> Get cover letter from TailoredAsset
    │   (already generated in tailor step)
    └─> Update state: cover_letter
    │
    ▼
autofill_application_node
    │
    ├─> Call AutofillService:
    │   ├─> Detect portal type (Greenhouse/Lever)
    │   ├─> Launch Playwright browser
    │   ├─> Navigate to job application URL
    │   ├─> Fill basic fields (name, email, phone)
    │   ├─> Upload resume PDF
    │   ├─> Upload cover letter PDF
    │   ├─> 🤖 AI Question Answering:
    │   │   ├─> Find question fields (textarea, inputs)
    │   │   ├─> Extract question text (label, placeholder)
    │   │   ├─> Call Gemini with:
    │   │   │   ├─> Question text
    │   │   │   ├─> Resume JSON
    │   │   │   └─> Job description
    │   │   └─> Fill answer in form field
    │   ├─> Take screenshots (before/after)
    │   ├─> Calculate confidence scores
    │   └─> Generate verification URL
    ├─> Store AutofillRun in database
    └─> Update state: autofill_run
    │
    ▼
send_verification_email_node
    │
    ├─> Call EmailService:
    │   ├─> Create HTML email template
    │   ├─> Include verification link
    │   ├─> Send via SMTP
    │   └─> Return verification URL
    └─> Update state: verification_url
    │
    ▼
END
    │
    └─> Return final state with verification_url
```

## 🎯 Step-by-Step Detailed Flow

### 1. **Resume Upload & Parsing**
```python
User uploads PDF
    ↓
POST /api/profile/ingest
    ↓
ProfileService.parse_resume()
    ├─> PDFParser extracts text
    ├─> GeminiClient.parse_resume() → Structured JSON
    │   └─> Extracts: summary, skills, experience, projects, education
    ├─> Generate LaTeX template (for format preservation)
    └─> Store in database (User + Profile)
```

### 2. **Job Search**
```python
User searches for jobs
    ↓
POST /api/jobs/search
    ↓
JobService.search_and_store_jobs()
    ├─> Google Custom Search API
    ├─> Fetch job posting HTML
    ├─> JobParser extracts:
    │   ├─> JSON-LD (preferred)
    │   └─> HTML fallback
    └─> Store jobs in database
```

### 3. **Complete Workflow Trigger**
```python
User clicks "Run Complete Workflow"
    ↓
POST /api/tailor/complete
    ↓
JobApplicationWorkflow.run()
    ├─> Initialize LangGraph state
    └─> Execute workflow graph
```

### 4. **Resume Tailoring**
```python
tailor_resume_node()
    ↓
TailorService.generate_tailored_assets()
    ├─> GeminiClient.tailor_resume()
    │   ├─> Analyze job description
    │   ├─> Rewrite bullets for ATS
    │   ├─> Reorder sections by relevance
    │   └─> Never invent facts (validation)
    ├─> GeminiClient.generate_ai_explanation()
    ├─> GeminiClient.calculate_job_match_score()
    ├─> LaTeXGenerator.generate_latex()
    ├─> LaTeXCompiler.compile_latex_to_pdf()
    └─> Store TailoredAsset
```

### 5. **Cover Letter Generation**
```python
generate_cover_letter_node()
    ↓
Get cover letter from TailoredAsset
    (already generated in tailor step)
    ├─> GeminiClient.generate_cover_letter()
    │   ├─> Opening (1-2 sentences)
    │   ├─> Mapping bullets (3 points)
    │   └─> Closing (availability + links)
    └─> PDFGenerator generates PDF
```

### 6. **Autofill Application**
```python
autofill_application_node()
    ↓
AutofillService.run_autofill_with_questions()
    ├─> Detect portal (Greenhouse/Lever)
    ├─> Launch Playwright browser
    ├─> Navigate to application URL
    ├─> Fill basic fields:
    │   ├─> Name, email, phone
    │   └─> Links (LinkedIn, GitHub, etc.)
    ├─> Upload files:
    │   ├─> Resume PDF
    │   └─> Cover letter PDF
    └─> 🤖 AI Question Answering:
        ├─> Find question fields
        ├─> Extract question text
        ├─> GeminiClient.answer_application_question()
        │   ├─> Input: question + resume + job description
        │   └─> Output: intelligent answer
        └─> Fill answer in form
```

### 7. **Verification Email**
```python
send_verification_email_node()
    ↓
EmailService.send_verification_email()
    ├─> Generate verification URL
    ├─> Create HTML email template
    ├─> Include:
    │   ├─> Job details
    │   ├─> Verification link
    │   └─> Review instructions
    └─> Send via SMTP
```

## 🔑 Key Technologies at Each Step

| Step | Technology | Purpose |
|------|-----------|---------|
| Parse Resume | **Gemini API** | Extract structured data from PDF |
| Search Jobs | **Google CSE** | Find relevant job postings |
| Tailor Resume | **Gemini API** + **LaTeX** | Rewrite resume, preserve format |
| Cover Letter | **Gemini API** | Generate personalized letter |
| Autofill | **Playwright** + **Gemini API** | Fill forms + answer questions |
| Email | **SMTP** | Send verification links |

## 🎯 State Management

The LangGraph workflow maintains state across all steps:

```python
WorkflowState = {
    "user_id": str,
    "job_id": str,
    "resume_pdf_path": str,
    "parsed_resume": Dict,      # From Gemini parsing
    "selected_job": Job,         # Database object
    "tailored_resume": Dict,     # Tailored JSON
    "cover_letter": Dict,        # Cover letter JSON
    "autofill_run": AutofillRun, # Autofill results
    "verification_url": str      # Final output
}
```

## 🚀 Benefits of This Workflow

✅ **Automated**: End-to-end automation  
✅ **Intelligent**: AI handles complex tasks  
✅ **Reliable**: LangGraph manages state & errors  
✅ **Scalable**: Can handle multiple applications  
✅ **User-Friendly**: Verification step for safety  

This workflow ensures every job application is:
- Properly tailored for the role
- Formatted correctly (LaTeX preservation)
- Intelligently filled (AI question answering)
- Ready for user review before submission

