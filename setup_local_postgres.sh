#!/bin/bash

# Setup script for local PostgreSQL 16

echo "🔍 Setting up local PostgreSQL 16..."

# Add PostgreSQL to PATH
export PATH="/Library/PostgreSQL/16/bin:$PATH"

# Check if PostgreSQL is running
if pg_isready -U postgres >/dev/null 2>&1; then
    echo "✅ PostgreSQL is running"
else
    echo "⚠️  PostgreSQL might not be running"
    echo "   Try starting it with: sudo /Library/PostgreSQL/16/bin/pg_ctl -D /Library/PostgreSQL/16/data start"
    echo "   Or use pgAdmin 4 to start the service"
fi

# Create database
echo "📦 Creating database 'hackajob'..."
createdb -U postgres hackajob 2>/dev/null && echo "✅ Database created" || echo "⚠️  Database might already exist or need different user"

# Create pgvector extension
echo "📦 Installing pgvector extension..."
psql -U postgres -d hackajob -c "CREATE EXTENSION IF NOT EXISTS vector;" && echo "✅ pgvector extension installed"

# Get current user for DATABASE_URL
CURRENT_USER=$(whoami)
echo ""
echo "✅ Setup complete!"
echo ""
echo "📝 Update backend/.env with:"
echo "DATABASE_URL=postgresql+psycopg2://$CURRENT_USER@localhost:5432/hackajob"
echo ""
echo "Or if using postgres user:"
echo "DATABASE_URL=postgresql+psycopg2://postgres@localhost:5432/hackajob"
