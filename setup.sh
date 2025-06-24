#!/bin/bash

# FastAPI Task Management System Setup Script

echo "🚀 Setting up FastAPI Task Management System..."

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "⚡ Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "📈 Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Copy environment file
echo "⚙️ Setting up environment configuration..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✅ Created .env file from .env.example"
    echo "⚠️  Please update .env with your configuration"
else
    echo "⚠️  .env file already exists"
fi

# Create uploads directory
echo "📁 Creating uploads directory..."
mkdir -p uploads

# Initialize Alembic (if not already done)
if [ ! -d "alembic" ]; then
    echo "🗄️ Initializing database migrations..."
    alembic init alembic
    echo "✅ Alembic initialized"
else
    echo "⚠️  Alembic already initialized"
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Update .env file with your database and other configurations"
echo "2. Start PostgreSQL and Redis (or use Docker Compose)"
echo "3. Run database migrations: alembic upgrade head"
echo "4. Start the application: uvicorn app.main:app --reload"
echo ""
echo "Or use Docker:"
echo "docker-compose up -d"
echo ""
echo "API Documentation will be available at: http://localhost:8000/docs"
