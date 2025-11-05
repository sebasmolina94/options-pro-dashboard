#!/bin/bash

# EzOptions Enhanced - Easy Startup Script
# This script makes it super easy to launch your options analysis platform

echo "🚀 EzOptions Enhanced - Professional Options Flow Analysis"
echo "========================================================="
echo ""

# Check if we're in the right directory
if [ ! -f "app_enhanced.py" ]; then
    echo "❌ Error: Please run this script from the EzOptions-Enhanced directory"
    echo "   cd ~/Desktop/EzOptions-Enhanced"
    echo "   ./start_app.sh"
    exit 1
fi

echo "📊 Available Options:"
echo "1. Enhanced App (RECOMMENDED) - 4-tab interface with OI + Volume analysis"
echo "2. Original App - Single-mode interface"
echo "3. Both Apps - Run both simultaneously"
echo ""

read -p "Choose option (1-3): " choice

case $choice in
    1)
        echo ""
        echo "🚀 Starting Enhanced App..."
        echo "📍 Access at: http://localhost:8502"
        echo "🔥 Features: 4 analysis tabs, Volume + OI trading plans"
        echo ""
        echo "Press Ctrl+C to stop the app"
        echo "========================================="
        streamlit run app_enhanced.py --server.port 8502
        ;;
    2)
        echo ""
        echo "🚀 Starting Original App..."
        echo "📍 Access at: http://localhost:8501"
        echo "🔥 Features: Classic GEX/VEX toggle interface"
        echo ""
        echo "Press Ctrl+C to stop the app"
        echo "======================================="
        streamlit run app.py --server.port 8501
        ;;
    3)
        echo ""
        echo "🚀 Starting Both Apps..."
        echo "📍 Enhanced App: http://localhost:8502"
        echo "📍 Original App: http://localhost:8501"
        echo ""
        echo "Press Ctrl+C to stop both apps"
        echo "=================================="
        
        # Start both apps in background
        streamlit run app_enhanced.py --server.port 8502 &
        PID1=$!
        streamlit run app.py --server.port 8501 &
        PID2=$!
        
        echo "✅ Both apps started!"
        echo "🌐 Opening browsers..."
        
        # Wait a moment for apps to start
        sleep 3
        
        # Open both in browser (macOS)
        if command -v open &> /dev/null; then
            open http://localhost:8502
            sleep 1
            open http://localhost:8501
        fi
        
        # Wait for user to stop
        echo ""
        echo "Press Enter to stop both apps..."
        read
        
        # Kill both processes
        kill $PID1 $PID2
        echo "✅ Both apps stopped."
        ;;
    *)
        echo "❌ Invalid choice. Please run the script again and choose 1, 2, or 3."
        exit 1
        ;;
esac
