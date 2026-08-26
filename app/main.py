import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:

    sys.path.insert(0, BASE_DIR)
import threading
from app.core.config import settings
from app.core.database import engine, Base
from app.api.endpoints import router as api_router
from app.services.vector_service import vector_service
from fastapi import FastAPI, UploadFile, File, HTTPException
from groq import Groq
import io

# 1. Najpierw tworzymy tabele relacyjne w Neon.tech
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Produkcyjny backend obsługujący hybrydowego asystenta językowego.",
)

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.on_event("startup")
def startup_event():
    # 1. Natychmiast inicjalizujemy podstawową konfigurację bazy wektorowej
    vector_service.initialize_vector_db()
    
    # 2. Uruchamiamy pobieranie wiedzy www w osobnym wątku tła.
    # Dzięki temu serwer uvicorn wystartuje natychmiast, a port otworzy się bez czekania na sieć!
    if settings.ENABLE_WEB_INGESTION:
        thread = threading.Thread(target=vector_service.auto_fetch_web_knowledge)
        thread.daemon = True  # Wątek zamknie się automatycznie przy wyłączeniu aplikacji
        thread.start()

@app.get("/", tags=["Health Check"])
def read_root():
    return {
        "status": "online",
        "app_name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT
    }

@app.post("/api/v1/transcribe", tags=["Audio core"])
async def transcribe_audio(file: UploadFile = File(...)):
    """
    Bezpieczny endpoint pośredniczący. Przyjmuje plik audio ze Streamlita,
    wykorzystuje oficjalnego klienta Groq i zwraca czysty tekst (0 błędu 500).
    """
    if not settings.GROQ_API_KEY:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY is not configured on the backend.")
        
    try:
        # Odczytujemy surowe bajty przesłane przez sieć
        audio_bytes = await file.read()
        
        # Inicjalizacja oficjalnego klienta Groq
        client = Groq(api_key=settings.GROQ_API_KEY)
        
        # Oficjalna metoda SDK Groq automatycznie mapuje i naprawia strukturę pliku audio
        transcription = client.audio.transcriptions.create(
            file=("audio.webm", io.BytesIO(audio_bytes)),
            model="whisper-large-v3",
            language="es",
            response_format="json"
        )
        
        return {"text": transcription.text}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Groq Whisper transcription failed: {str(e)}")