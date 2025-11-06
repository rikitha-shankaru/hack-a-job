# Updated: Resume Writing with LaTeX and Formatting Preservation

## Overview

The system now supports PDF resume uploads and uses LaTeX-based formatting to preserve the original resume's structure and styling when tailoring resumes for specific jobs.

## How It Works

1. **PDF Upload**: Users can upload their resume as a PDF file
2. **PDF Parsing**: The system extracts text and analyzes structure from the PDF
3. **LaTeX Template Generation**: A LaTeX template is created based on the original PDF's structure
4. **Content Rewriting**: OpenAI/ChatGPT rewrites the resume content while preserving structure
5. **LaTeX Compilation**: The tailored content is compiled to PDF using LaTeX (pdflatex), maintaining formatting

## Components

### Backend

- **PDFParser** (`app/utils/pdf_parser.py`): Extracts text and structure from PDF resumes
- **LaTeXGenerator** (`app/utils/latex_generator.py`): Generates LaTeX from resume JSON, optionally using original template
- **LaTeXCompiler** (`app/utils/latex_compiler.py`): Compiles LaTeX documents to PDF using pdflatex

### Updated Services

- **ProfileService**: Now handles PDF uploads and extracts LaTeX templates
- **TailorService**: Uses LaTeX compilation for resume PDFs (with ReportLab fallback)

## Prerequisites

Install LaTeX distribution:
- **macOS**: `brew install --cask mactex` or `brew install basictex`
- **Linux**: `sudo apt-get install texlive-latex-base texlive-latex-extra`
- **Windows**: Install MiKTeX or TeX Live

Or use Docker:
```bash
docker pull texlive/texlive:latest
```

## Setup

1. Install LaTeX compiler (see above)
2. Verify installation:
   ```bash
   pdflatex --version
   ```

3. The system will automatically:
   - Use LaTeX compilation when pdflatex is available
   - Fall back to ReportLab PDF generation if LaTeX is not available

## Usage

### Upload PDF Resume

Users can upload a PDF resume through the frontend. The system will:
1. Extract text and structure
2. Generate a LaTeX template
3. Store the original PDF and template

### Tailor Resume

When tailoring a resume:
1. OpenAI rewrites the content
2. LaTeX template is used to maintain formatting
3. New PDF is compiled using LaTeX
4. Formatting from original resume is preserved

## Benefits

- ✅ Preserves original resume formatting
- ✅ Professional LaTeX-based output
- ✅ ATS-friendly PDFs
- ✅ Maintains document structure
- ✅ Fallback to ReportLab if LaTeX unavailable

## Notes

- LaTeX compilation requires pdflatex to be installed
- Original PDF structure analysis is simplified - can be enhanced for better preservation
- Cover letters still use ReportLab (can be upgraded to LaTeX later)

