# LangGraph Workflow with Google Gemini API

## Complete Workflow

```
Upload Resume → Parse → Search Jobs → Tailor Resume → Generate Cover Letter → 
Autofill Application (with AI question answering) → Send Verification Email
```

## Key Features

### 1. **LangGraph Orchestration**
- State management across workflow steps
- Error handling and retries
- Conditional logic and branching
- Parallel processing capabilities

### 2. **Google Gemini API Integration**
- Resume parsing
- Resume tailoring
- Cover letter generation
- AI explanations and recommendations
- Job match scoring
- **Question answering** for application forms

### 3. **AI-Powered Question Answering**
- Detects questions in application forms
- Uses Gemini to generate intelligent answers
- Based on resume and job description
- Maintains factual accuracy

### 4. **Verification Email**
- Sends link to review autofilled application
- HTML email with clear instructions
- Secure verification URL
- 24-hour expiration

## Workflow Steps

1. **Parse Resume**: Extract structured data from PDF using Gemini
2. **Search Jobs**: Use Google Custom Search to find relevant positions
3. **Tailor Resume**: Gemini rewrites resume for job match (preserves format via Overleaf/LaTeX)
4. **Generate Cover Letter**: Gemini creates personalized cover letter
5. **Autofill Application**: 
   - Fill basic fields (name, email, phone, links)
   - Upload resume and cover letter PDFs
   - **Answer questions using Gemini AI**
6. **Send Verification Email**: Email with link to verify and submit

## Environment Variables

```env
GOOGLE_GEMINI_API_KEY=your_gemini_api_key
GOOGLE_CSE_KEY=your_cse_key
GOOGLE_CSE_CX=your_cse_cx
```

## Benefits of LangGraph + Gemini

- **Scalable**: Handles complex multi-step workflows
- **Maintainable**: Clear state management and error handling
- **Intelligent**: Gemini provides better question answering
- **Cost-effective**: Gemini API pricing
- **Prize eligible**: Uses Google Gemini API! 🏆

