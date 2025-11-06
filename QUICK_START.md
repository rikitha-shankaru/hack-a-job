# 🚀 Quick Start Guide

## ✅ Completed Setup

- ✅ Python virtual environment created
- ✅ Backend dependencies installed  
- ✅ Frontend dependencies installed
- ✅ .env.example created

## 📋 Next Steps to Run

### 1. Create .env File

```bash
cd backend
cp .env.example .env
```

Then edit `.env` and add your API keys:
- `GOOGLE_GEMINI_API_KEY` - Get from https://makersuite.google.com/app/apikey
- `GOOGLE_CSE_KEY` - Google Custom Search API key
- `GOOGLE_CSE_CX` - Google Custom Search Engine ID
- `DATABASE_URL` - PostgreSQL connection string

### 2. Set Up PostgreSQL Database

**Option A: Using Homebrew (macOS)**
```bash
brew install postgresql@14
brew services start postgresql@14
createdb hackajob
psql hackajob -c 'CREATE EXTENSION vector;'
```

**Option B: Using Docker**
```bash
docker run -d \
  --name postgres-hackajob \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=hackajob \
  -p 5432:5432 \
  pgvector/pgvector:pg14
```

Then update `.env`:
```
DATABASE_URL=postgresql+psycopg://postgres:password@localhost:5432/hackajob
```

### 3. Run Database Migrations

```bash
cd backend
source venv/bin/activate
alembic upgrade head
```

### 4. Start Backend Server

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

Backend will run on: http://localhost:8000

### 5. Start Frontend Server (New Terminal)

```bash
cd frontend
npm run dev
```

Frontend will run on: http://localhost:3000

## 🎯 Quick Test

1. Open http://localhost:3000
2. Upload a PDF resume
3. Search for jobs
4. Try the complete workflow!

## ⚠️ Troubleshooting

- **Database errors**: Make sure PostgreSQL is running and pgvector extension is installed
- **API errors**: Check your `.env` file has correct API keys
- **Port conflicts**: Change ports in uvicorn/npm commands if 8000/3000 are taken
