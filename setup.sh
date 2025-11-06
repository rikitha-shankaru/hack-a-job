#!/bin/bash
# Setup script for Hack-A-Job

echo "Setting up Hack-A-Job..."

# Backend setup
echo "Setting up backend..."
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
echo "Backend setup complete. Don't forget to:"
echo "1. Copy .env.example to .env and fill in your API keys"
echo "2. Set up PostgreSQL with pgvector extension"
echo "3. Run: alembic upgrade head"

cd ..

# Frontend setup
echo "Setting up frontend..."
cd frontend
npm install
echo "Frontend setup complete."

cd ..
echo "Setup complete!"

