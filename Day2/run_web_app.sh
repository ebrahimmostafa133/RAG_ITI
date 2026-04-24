#!/bin/bash
# Medical AI Agent Web UI Launcher

echo "🏥 Starting Medical AI Agent Web UI..."
echo ""

# Check if .env file exists and has API key
if [ ! -f ".env" ]; then
    echo "❌ .env file not found. Please create it with your OpenAI API key."
    echo "   Copy .env.example to .env and add your key."
    exit 1
fi

if ! grep -q "OPENAI_API_KEY=sk-" .env; then
    echo "⚠️  OpenAI API key not found in .env file."
    echo "   Please add: OPENAI_API_KEY=sk-your-api-key-here"
    echo ""
fi

# Activate virtual environment
if [ -d ".venv" ]; then
    echo "🔧 Activating virtual environment..."
    source .venv/bin/activate
else
    echo "⚠️  Virtual environment not found. Installing dependencies globally..."
fi

# Check if streamlit is installed
if ! command -v streamlit &> /dev/null; then
    echo "📦 Installing Streamlit..."
    pip install streamlit
fi

# Start the application
echo "🚀 Launching web interface..."
echo "   Open http://localhost:8501 in your browser"
echo ""
streamlit run app.py
