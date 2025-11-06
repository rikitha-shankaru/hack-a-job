#!/bin/bash

echo "🔍 Checking PostgreSQL setup..."

# Check if Docker is available
if command -v docker &> /dev/null; then
    echo "✅ Docker found"
    
    # Check if container already exists
    if docker ps -a | grep -q postgres-hackajob; then
        echo "📦 PostgreSQL container exists"
        docker start postgres-hackajob
        echo "✅ Started existing PostgreSQL container"
    else
        echo "📦 Creating new PostgreSQL container..."
        docker run -d \
            --name postgres-hackajob \
            -e POSTGRES_PASSWORD=password \
            -e POSTGRES_DB=hackajob \
            -e POSTGRES_USER=postgres \
            -p 5432:5432 \
            pgvector/pgvector:pg14
        
        echo "⏳ Waiting for PostgreSQL to start..."
        sleep 5
        
        echo "✅ PostgreSQL container created and started"
    fi
    
    echo ""
    echo "📝 Update your backend/.env file:"
    echo "DATABASE_URL=postgresql+psycopg2://postgres:password@localhost:5432/hackajob"
    
elif command -v psql &> /dev/null; then
    echo "✅ PostgreSQL (psql) found"
    echo "📝 Make sure PostgreSQL is running and create database:"
    echo "   createdb hackajob"
    echo "   psql hackajob -c 'CREATE EXTENSION vector;'"
else
    echo "⚠️  PostgreSQL not found. Install it:"
    echo "   macOS: brew install postgresql@14"
    echo "   Or use Docker: brew install docker"
fi
