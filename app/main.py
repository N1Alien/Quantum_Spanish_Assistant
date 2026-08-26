import os
import sys
import io
import requests

# Dynamiczne wstrzyknięcie ścieżki projektu
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from fastapi import FastAPI, UploadFile, File, HTTPException
from app.core.config import settings
from app.core.database import engine, Base
from app.api.endpoints import router as api_router

# Automatyczne tworzenie tabel PostgreSQL w Neon.tech przy starcie
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Produkcyjny backend obsługujący hybrydowego asystenta językowego.",
)

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.post("/api/v1/transcribe", tags=["Audio core"])
def transcribe_audio(file: UploadFile = File(...)):
    """
    Bezpieczny i stabilny endpoint pośredniczący dla Groq Whisper.
    Omija błędy bibliotek i blokady 405/500 serwera proxy Render.
    """
    if not settings.GROQ_API_KEY:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY is not configured on the backend.")
        
    try:
        # Odczytujemy surowe bajty przesłane przez sieć ze Streamlita
        audio_bytes = file.file.read()
        
        # Oficjalny URL Groq Whisper dla transkrypcji audio
        url = "https://groq.com"
        headers = {"Authorization": f"Bearer {settings.GROQ_API_KEY}"}
        
        # Przygotowujemy formularz binarny akceptowany przez OpenAI/Groq API
        files = {
            "file": ("audio.webm", audio_bytes, "audio/webm")
        }
        data = {
            "model": "whisper-large-v3",
            "language": "es"
        }
        
        # Wysyłamy bezpośrednie żądanie POST do serwerów Groq
        response = requests.post(url, headers=headers, files=files, data=data, timeout=20)
        
        if response.status_code == 200:
            return {"text": response.json().get("text", "").strip()}
        else:
            raise HTTPException(status_code=response.status_code, detail=response.text)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Groq Whisper integration failed: {str(e)}")

@app.get("/", tags=["Health Check"])
def read_root():
    return {
        "status": "online",
        "app_name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT
    }
