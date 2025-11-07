#!/bin/bash

# Quick Start Script for Hack-A-Job
# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "🚀 Starting Hack-A-Job Application..."
echo ""

# Check if Docker TeX Live is available (BEST METHOD - official, reliable)
if command -v docker &> /dev/null; then
    if docker ps 2>/dev/null | grep -q hack-a-job-latex-compiler; then
        echo "✅ Docker TeX Live compiler is running"
    else
        echo "🚀 Starting Docker TeX Live compiler (best LaTeX compilation method)..."
        # Try docker compose (newer) or docker-compose (older)
        if docker compose version &> /dev/null 2>&1; then
            docker compose -f "$SCRIPT_DIR/docker-compose.latex.yml" up -d 2>&1 | grep -v "Creating\|Starting\|Pulling" || true
            if [ $? -eq 0 ]; then
                echo "✅ Docker TeX Live started successfully"
            else
                echo "⚠️  Failed to start Docker TeX Live. Will use local pdflatex or other fallbacks."
            fi
        elif command -v docker-compose &> /dev/null; then
            docker-compose -f "$SCRIPT_DIR/docker-compose.latex.yml" up -d 2>&1 | grep -v "Creating\|Starting\|Pulling" || true
            if [ $? -eq 0 ]; then
                echo "✅ Docker TeX Live started successfully"
            else
                echo "⚠️  Failed to start Docker TeX Live. Will use local pdflatex or other fallbacks."
            fi
        else
            echo "⚠️  Docker Compose not found. LaTeX will use local pdflatex if available."
        fi
        
        # Wait a moment for container to start
        sleep 2
        
        # Verify it started
        if docker ps 2>/dev/null | grep -q hack-a-job-latex-compiler; then
            echo "✅ Docker TeX Live compiler is running"
        fi
    fi
else
    echo "ℹ️  Docker not found. LaTeX will use local pdflatex if available."
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
cd "$SCRIPT_DIR/backend"
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
else
    echo "⚠️  Virtual environment not found in backend/venv"
    echo "   Please create it with: cd backend && python3 -m venv venv"
fi

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
cd "$SCRIPT_DIR/backend"
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
    BACKEND_PID=$!
else
    echo "⚠️  Backend virtual environment not found. Skipping backend startup."
    BACKEND_PID=""
fi

# Wait a bit for backend to start
sleep 3

# Start frontend
cd "$SCRIPT_DIR/frontend"
if [ -f "package.json" ]; then
    npm run dev &
    FRONTEND_PID=$!
else
    echo "⚠️  Frontend not found. Skipping frontend startup."
    FRONTEND_PID=""
fi

# Wait for both processes
if [ -n "$BACKEND_PID" ] && [ -n "$FRONTEND_PID" ]; then
    wait $BACKEND_PID $FRONTEND_PID
elif [ -n "$BACKEND_PID" ]; then
    wait $BACKEND_PID
elif [ -n "$FRONTEND_PID" ]; then
    wait $FRONTEND_PID
fi

