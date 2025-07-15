#!/bin/bash

# Astranauts API Quick Start Script
echo "🚀 Starting Astranauts API Server..."
echo "=================================="

# Check if we're in the right directory
if [ ! -f "app/main.py" ]; then
    echo "❌ Error: Please run this script from the astranauts project root directory"
    exit 1
fi

# Check if requirements are installed
echo "🔍 Checking dependencies..."
python -c "import fastapi, uvicorn" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  Installing dependencies..."
    pip install -r requirements.txt
fi

# Start the server
echo "🌟 Starting API server on http://localhost:8080"
echo ""
echo "📖 Available endpoints:"
echo "   • API Docs: http://localhost:8080/docs"
echo "   • Health Check: http://localhost:8080/health"
echo "   • Sarana Health: http://localhost:8080/api/v1/sarana/health"
echo ""
echo "🛑 Press Ctrl+C to stop the server"
echo "=================================="

# Run the server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
