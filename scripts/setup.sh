#!/bin/bash

# VidyaVani IVR Learning System - Setup Script

echo "🚀 Setting up VidyaVani IVR Learning System..."

# Check Python version
python_version=$(python3 --version 2>&1 | grep -o '[0-9]\+\.[0-9]\+')
required_version="3.9"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python 3.9 or higher is required. Current version: $python_version"
    exit 1
fi

echo "✅ Python version check passed: $python_version"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p logs
mkdir -p data/ncert/processed
mkdir -p data/faiss
mkdir -p audio_cache
mkdir -p tmp

# Copy environment template
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your Exotel, OpenAI, and Google Cloud API keys before running the application"
else
    echo "✅ .env file already exists"
fi

# Set permissions for scripts
chmod +x scripts/*.sh

echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your API keys"
echo "2. Activate virtual environment: source venv/bin/activate"
echo "3. Run the application: python app.py"
echo "4. Test health endpoint: curl http://localhost:5000/health"