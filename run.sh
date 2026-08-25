#!/bin/bash

# Definiujemy ścieżkę do katalogu głównego projektu
PROJECT_DIR="/home/bond/Documents/Quantum_Spanish_Assistant"
cd "$PROJECT_DIR" || exit 1

echo "⚛️ [System Start] Initializing the Hybrid Quantum Assistant..."

# 1. Clean up old temporary and audio files
rm -f web_response.mp3
find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null

# 2. Safely stop stale processes from previous runs
echo "🧹 Cleaning old processes on ports 8000 and 8501..."
pkill -f "uvicorn app.main:app"
pkill -f "streamlit run frontend.py"
sleep 0.5

# 3. Verify and start PostgreSQL in Docker
echo "🐳 Checking Docker container..."
if ! sudo docker ps | grep -q "postgres_quantum_container"; then
    echo "📥 Starting PostgreSQL in Docker on port 5433..."
    sudo docker-compose up -d
    sleep 2
fi

# 4. Cleanup function (runs automatically on Ctrl+C or script shutdown)
cleanup() {
    echo -e "\n⚛️ [System Stop] Closing all processes and cleaning up..."
    kill "$BACKEND_PID" 2>/dev/null
    kill "$FRONTEND_PID" 2>/dev/null
    exit 0
}
# Register signal handlers for Ctrl+C and termination
trap cleanup SIGINT SIGTERM EXIT

# 5. Start the FastAPI backend in the background
# Port 8000 is occupied by another process, so we use 8001.
echo "🧠 Starting FastAPI backend (Port 8001)..."
"$PROJECT_DIR/.venv/bin/python" -m uvicorn app.main:app --host 127.0.0.1 --port 8001 > /dev/null 2>&1 &
BACKEND_PID=$! # Save backend PID

# Give the vector database time to load web knowledge
sleep 3

# 6. Start the Streamlit frontend in the background
echo "🎨 Starting Streamlit frontend (Port 8501)..."
"$PROJECT_DIR/.venv/bin/python" -m streamlit run frontend.py --server.headless true > /dev/null 2>&1 &
FRONTEND_PID=$! # Save frontend PID

sleep 2

# 7. Open the app in the default browser
echo "🚀 Opening the application in the browser..."
xdg-open http://localhost:8501

echo "🟢 System is running correctly! Press Ctrl+C in this terminal to shut it down."

# Keep the main script alive so the trap continues to monitor background processes
wait "$FRONTEND_PID"
