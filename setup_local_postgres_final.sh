#!/bin/bash

# Final setup for local PostgreSQL 16
export PATH="/Library/PostgreSQL/16/bin:$PATH"

echo "🔍 Checking PostgreSQL status..."
if pg_isready >/dev/null 2>&1; then
    echo "✅ PostgreSQL is running!"
    
    # Try to create database with current user first
    CURRENT_USER=$(whoami)
    echo ""
    echo "📦 Creating database 'hackajob'..."
    
    if createdb hackajob 2>/dev/null; then
        echo "✅ Database created as user: $CURRENT_USER"
        DB_USER=$CURRENT_USER
    elif createdb -U postgres hackajob 2>/dev/null; then
        echo "✅ Database created as user: postgres"
        DB_USER=postgres
    else
        echo "⚠️  Database might already exist, continuing..."
        # Try to determine which user can connect
        if psql -d hackajob -c "SELECT 1;" >/dev/null 2>&1; then
            DB_USER=$CURRENT_USER
        else
            DB_USER=postgres
        fi
    fi
    
    echo ""
    echo "📦 Installing pgvector extension..."
    if psql -d hackajob -c "CREATE EXTENSION IF NOT EXISTS vector;" 2>/dev/null; then
        echo "✅ pgvector extension installed"
    elif psql -U postgres -d hackajob -c "CREATE EXTENSION IF NOT EXISTS vector;" 2>/dev/null; then
        echo "✅ pgvector extension installed (as postgres user)"
    else
        echo "⚠️  Could not install extension - might need superuser privileges"
    fi
    
    echo ""
    echo "✅ Setup complete!"
    echo ""
    echo "📝 Update backend/.env DATABASE_URL to:"
    echo "DATABASE_URL=postgresql+psycopg2://$DB_USER@localhost:5432/hackajob"
    
else
    echo "❌ PostgreSQL is not running!"
    echo ""
    echo "Please start PostgreSQL using one of these methods:"
    echo "1. Open pgAdmin 4 from Applications and connect to server"
    echo "2. Or run: sudo /Library/PostgreSQL/16/bin/pg_ctl -D /Library/PostgreSQL/16/data start"
    echo ""
    echo "Then run this script again: ./setup_local_postgres_final.sh"
fi
