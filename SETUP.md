# 🚀 Quick Start Guide - Cross-Platform

## ✅ Prerequisites

### macOS
- Python 3.11+ (`brew install python3` or download from python.org)
- Node.js 18+ (`brew install node` or download from nodejs.org)
- Docker Desktop (recommended) OR PostgreSQL 16+
- Git

### Windows
- Python 3.11+ (download from python.org)
- Node.js 18+ (download from nodejs.org)
- Docker Desktop (recommended) OR PostgreSQL 16+
- Git for Windows

## 📦 Setup Steps

### 1. Clone Repository

```bash
git clone https://github.com/rikitha-shankaru/hack-a-job.git
cd hack-a-job
```

### 2. Backend Setup

**macOS/Linux:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

**Windows:**
```bash
cd backend
python -m venv venv
venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configure Environment Variables

**macOS/Linux:**
```bash
cd backend
cp .env.example .env
# Edit .env with your API keys
```

**Windows:**
```bash
cd backend
copy .env.example .env
# Edit .env with your API keys (use Notepad or any text editor)
```

Required API keys:
- `GOOGLE_GEMINI_API_KEY` - Get from https://makersuite.google.com/app/apikey
- `GOOGLE_CSE_KEY` - Google Custom Search API key
- `GOOGLE_CSE_CX` - Custom Search Engine ID
- `DATABASE_URL` - PostgreSQL connection string

### 4. Database Setup

#### Option A: Docker (Recommended - Works on Both Platforms)

**macOS/Linux/Windows:**
```bash
docker run -d \
  --name postgres-hackajob \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=hackajob \
  -e POSTGRES_USER=postgres \
  -p 5432:5432 \
  pgvector/pgvector:pg14
```

Update `.env`:
```
DATABASE_URL=postgresql+psycopg2://postgres:password@localhost:5432/hackajob
```

#### Option B: Local PostgreSQL

**macOS:**
```bash
brew install postgresql@14
brew services start postgresql@14
createdb hackajob
psql hackajob -c "CREATE EXTENSION vector;"
```

**Windows:**
1. Download PostgreSQL from https://www.postgresql.org/download/windows/
2. Install PostgreSQL 14+
3. Open pgAdmin 4
4. Create database "hackajob"
5. Run: `CREATE EXTENSION vector;`

Update `.env`:
```
DATABASE_URL=postgresql+psycopg2://YOUR_USERNAME@localhost:5432/hackajob
```

### 5. Run Database Migrations

**macOS/Linux:**
```bash
cd backend
source venv/bin/activate
alembic upgrade head
```

**Windows:**
```bash
cd backend
venv\Scripts\activate
alembic upgrade head
```

### 6. Frontend Setup

**macOS/Linux/Windows:**
```bash
cd frontend
npm install
```

### 7. Start Servers

**Terminal 1 - Backend:**

**macOS/Linux:**
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

**Windows:**
```bash
cd backend
venv\Scripts\activate
uvicorn app.main:app --reload
```

**Terminal 2 - Frontend:**

**macOS/Linux/Windows:**
```bash
cd frontend
npm run dev
```

### 8. Open Application

Open your browser and go to: **http://localhost:3000**

## 🔧 Troubleshooting

### Common Issues

**Port Already in Use:**
- Backend (8000): Change port with `--port 8001`
- Frontend (3000): Change port with `npm run dev -- -p 3001`

**Database Connection Error:**
- Make sure PostgreSQL/Docker is running
- Check DATABASE_URL in `.env` is correct
- Verify pgvector extension is installed

**API Key Errors:**
- Verify API keys in `.env` are correct
- Check Gemini API key starts with "AIza" (not "gAIza")
- Ensure Custom Search Engine ID (CX) is correct

**Python/Node Not Found:**
- macOS: Add to PATH or use full paths
- Windows: Add Python and Node to system PATH during installation

### Windows-Specific Notes

- Use `\` instead of `/` for paths in commands
- Use `venv\Scripts\activate` instead of `source venv/bin/activate`
- Use `copy` instead of `cp` for copying files
- PowerShell may need different syntax for some commands

### macOS-Specific Notes

- May need `python3` instead of `python`
- PostgreSQL via Homebrew: `/opt/homebrew/bin/psql` or `/usr/local/bin/psql`
- Docker Desktop must be running for Docker commands

## 📝 Environment Variables Reference

```env
# Google APIs
GOOGLE_GEMINI_API_KEY=your_gemini_api_key
GOOGLE_CSE_KEY=your_cse_api_key
GOOGLE_CSE_CX=your_search_engine_id

# Database (Docker)
DATABASE_URL=postgresql+psycopg2://postgres:password@localhost:5432/hackajob

# Database (Local PostgreSQL)
DATABASE_URL=postgresql+psycopg2://username@localhost:5432/hackajob

# Email (Optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASS=your_app_password
FROM_EMAIL=your_email@gmail.com
```

## 🎯 Quick Test

1. Open http://localhost:3000
2. Upload a PDF resume
3. Search for jobs
4. Try the complete workflow!

## 🆘 Need Help?

- Check the main README.md for more details
- Review WORKFLOW_DETAILED.md for workflow explanation
- Check AI_FEATURES.md for AI features documentation
