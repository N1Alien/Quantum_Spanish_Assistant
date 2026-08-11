#!/bin/bash

# Definiujemy ścieżkę do katalogu głównego projektu
PROJECT_DIR="/home/bond/Documents/Quantum_Spanish_Assistant"
cd "$PROJECT_DIR" || exit 1

echo "⚛️ [System Start] Inicjalizacja Hybrydowego Kwantowego Asystenta..."

# 1. Czyszczenie starych plików tymczasowych i audio
rm -f web_response.mp3
find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null

# 2. Bezpieczne zamykanie zablokowanych procesów z poprzednich uruchomień
echo "🧹 Czyszczenie starych procesów portów 8000 i 8501..."
pkill -f "uvicorn app.main:app"
pkill -f "streamlit run app.py"
sleep 0.5

# 3. Weryfikacja i automatyczny start infrastruktury PostgreSQL w Dockerze
echo "🐳 Sprawdzanie kontenera Docker..."
if ! sudo docker ps | grep -q "postgres_quantum_container"; then
    echo "📥 Uruchamianie bazy PostgreSQL w Dockerze na porcie 5433..."
    sudo docker-compose up -d
    sleep 2
fi

# 4. Funkcja sprzątająca (Wywoływana AUTOMATYCZNIE przy Ctrl+C lub zamknięciu skryptu)
# Rekruterzy DevOps uwielbiają ten mechanizm zabezpieczający przed procesami-zombie!
cleanup() {
    echo -e "\n⚛️ [System Stop] Zamykanie wszystkich procesów i sprzątanie środowiska..."
    kill "$BACKEND_PID" 2>/dev/null
    kill "$FRONTEND_PID" 2>/dev/null
    exit 0
}
# Rejestrujemy przechwytywanie sygnałów systemowych (SIGINT = Ctrl+C, SIGTERM = zamknięcie)
trap cleanup SIGINT SIGTERM EXIT

# 5. Uruchomienie profesjonalnego produkcyjnego Backendu FastAPI w tle (&)
echo "🧠 Uruchamianie Backendu FastAPI (Port 8000)..."
"$PROJECT_DIR/.venv/bin/python" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 > /dev/null 2>&1 &
BACKEND_PID=$! # Zapamiętujemy ID procesu backendu

# Czekamy chwilę na zasilenie bazy wektorowej ChromaDB z internetu
sleep 3

# 6. Uruchomienie Głosowego Frontendu Streamlit w tle (&)
# Flaga --server.headless=true wyłącza pytania o e-mail i blokady w konsoli
echo "🎨 Uruchamianie Frontendu Streamlit (Port 8501)..."
"$PROJECT_DIR/.venv/bin/python" -m streamlit run app.py --server.headless true > /dev/null 2>&1 &
FRONTEND_PID=$! # Zapamiętujemy ID procesu frontendu

sleep 2

# 7. Automatyczne i bezpieczne otwarcie asystenta w Twojej domyślnej przeglądarce Opera
echo "🚀 Otwieranie aplikacji w przeglądarce..."
xdg-open http://localhost:8501

echo "🟢 System działa prawidłowo! Wciśnij Ctrl+C w tym terminalu, aby go wyłączyć."

# Podtrzymujemy działanie głównego skryptu, aby trap cały czas czuwał w tle
wait "$FRONTEND_PID"
