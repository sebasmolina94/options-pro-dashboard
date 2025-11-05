#!/bin/bash

echo "🚀 Options Pro - Installation Script"
echo "=========================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+ first."
    exit 1
fi

echo "✅ Python 3 found"

# Install requirements
echo "📦 Installing Python dependencies..."
pip3 install -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✅ Dependencies installed successfully"
else
    echo "❌ Failed to install dependencies"
    exit 1
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚙️ Setting up environment file..."
    cp .env.template .env
    echo "📝 Please edit .env file with your Schwab API credentials"
    echo "   Get credentials from: https://developer.schwab.com/"
else
    echo "✅ .env file already exists"
fi

echo ""
echo "🎉 Installation complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your Schwab API credentials"
echo "2. Run: streamlit run app_enhanced.py --server.port 8502"
echo "3. Open: http://localhost:8502"
echo ""
echo "For mobile access, use your computer's IP address instead of localhost"
echo ""
