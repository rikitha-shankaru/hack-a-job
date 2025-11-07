#!/bin/bash

# Quick Start Script for Hack-A-Job

echo "🚀 Starting Hack-A-Job Application..."
echo ""

# Check if Overleaf CLSI is running (optional)
if docker ps | grep -q hack-a-job-overleaf-clsi; then
    echo "✅ Overleaf CLSI is running"
else
    echo "🚀 Starting Overleaf CLSI..."
    if command -v docker-compose &> /dev/null || command -v docker &> /dev/null; then
        # Try docker compose (newer) or docker-compose (older)
        if docker compose version &> /dev/null; then
            docker compose -f docker-compose.overleaf.yml up -d 2>/dev/null || echo "⚠️  Failed to start Overleaf CLSI with docker compose"
        elif command -v docker-compose &> /dev/null; then
            docker-compose -f docker-compose.overleaf.yml up -d 2>/dev/null || echo "⚠️  Failed to start Overleaf CLSI with docker-compose"
        else
            echo "⚠️  Docker not found. Overleaf CLSI will not start."
            echo "   LaTeX will use local pdflatex if available."
        fi
        
        # Wait a moment for CLSI to start
        sleep 2
        
        # Verify it started
        if docker ps | grep -q hack-a-job-overleaf-clsi; then
            echo "✅ Overleaf CLSI started successfully"
        else
            echo "⚠️  Overleaf CLSI may not have started. LaTeX will use local pdflatex if available."
        fi
    else
        echo "⚠️  Docker not found. Overleaf CLSI will not start."
        echo "   LaTeX will use local pdflatex if available."
    fi
fi
echo ""

# Check if .env exists
if [ ! -f "backend/.env" ]; then
    echo "⚠️  .env file not found!"
    echo "📝 Creating .env from template..."
    cp backend/.env.example backend/.env
    echo ""
    echo "⚠️  IMPORTANT: Edit backend/.env and add your API keys:"
    echo "   - GOOGLE_GEMINI_API_KEY"
    echo "   - GOOGLE_CSE_KEY"
    echo "   - GOOGLE_CSE_CX"
    echo "   - DATABASE_URL"
    echo ""
    read -p "Press Enter after you've added your API keys..."
fi

# Check database connection
echo "🔍 Checking database connection..."
cd backend
source venv/bin/activate

# Try to run a simple check
python3 -c "
from app.config import settings
try:
    print(f'✅ Database URL configured: {settings.database_url[:30]}...')
except Exception as e:
    print(f'⚠️  Database config error: {e}')
" 2>/dev/null || echo "⚠️  Could not verify database config"

echo ""
echo "📋 Starting servers..."
echo ""
echo "Backend will start on: http://localhost:8000"
echo "Frontend will start on: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop both servers"
echo ""

# Start backend in background
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Wait a bit for backend to start
sleep 3

# Start frontend
cd ../frontend
npm run dev &
FRONTEND_PID=$!

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID

