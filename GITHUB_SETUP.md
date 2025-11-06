# GitHub Repository Setup

## Steps to Create GitHub Repo

1. **Go to GitHub**: https://github.com/new

2. **Create Repository**:
   - Repository name: `hack-a-job` (or your preferred name)
   - Description: "AI-powered job application assistant with LangGraph workflow and Google Gemini API"
   - Visibility: Public (or Private)
   - **DO NOT** initialize with README, .gitignore, or license (we already have these)

3. **Push to GitHub**:
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/hack-a-job.git
   git branch -M main
   git push -u origin main
   ```

## Repository Structure

```
hack-a-job/
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── api/         # API endpoints
│   │   ├── services/    # Business logic
│   │   ├── utils/       # Utilities (Gemini, LaTeX, etc.)
│   │   ├── workflows/   # LangGraph workflows
│   │   └── models.py    # Database models
│   ├── alembic/         # Database migrations
│   └── requirements.txt
├── frontend/            # Next.js frontend
│   ├── app/             # Next.js app directory
│   └── package.json
├── README.md            # Main documentation
├── .gitignore           # Git ignore rules
└── .env.example         # Environment template
```

## What's Included

✅ Complete backend with FastAPI + LangGraph  
✅ Google Gemini API integration  
✅ Frontend with Next.js  
✅ Database models and migrations  
✅ Documentation files  
✅ Environment template  

## What's Excluded (via .gitignore)

❌ `.env` files (contains secrets)  
❌ `node_modules/`  
❌ `venv/` and Python cache  
❌ `uploads/` directory  
❌ IDE files  

## Next Steps After Pushing

1. Add repository description on GitHub
2. Add topics: `ai`, `langgraph`, `gemini`, `job-application`, `fastapi`, `nextjs`
3. Update README with badges if desired
4. Set up GitHub Actions for CI/CD (optional)

