import os
import sys
import base64
import requests
from fastapi import FastAPI, UploadFile, File, HTTPException
from app.core.config import settings
from app.core.database import engine, Base
from app.api.endpoints import router as api_router

# Dynamiczne wstrzyknięcie ścieżki projektu do pamięci Pythona
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Automatyczne tworzenie tabel PostgreSQL w Neon.tech przy starcie
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Produkcyjny backend obsługujący asystenta językowego opartego o Gemini API.",
)

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.post("/api/v1/transcribe", tags=["Audio core"])
async def transcribe_audio(file: UploadFile = File(...)):
    """
    Bezpieczny endpoint transkrypcji oparty o Google Gemini 2.5 Flash.
    Całkowicie omija Groqa i bezbłędnie zamienia audio na tekst.
    """
    gemini_key = os.getenv("GEMINI_API_KEY", "")
    if not gemini_key:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY is not configured on the backend.")
        
    try:
        # Odczytujemy surowe bajty przesłane ze Streamlita
        audio_bytes = await file.read()
        
        # Kodujemy audio do formatu Base64 wymaganego przez Google REST API
        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
        
        # Endpoint dla Gemini 2.5 Flash
        url = f"https://googleapis.com{gemini_key}"
        headers = {"Content-Type": "application/json"}
        
        # Konstruujemy strukturę multimodalną: przekazujemy plik audio oraz prompt z prośbą o transkrypcję
        payload_data = {
            "contents": [{
                "parts": [
                    {
                        "inlineData": {
                            "mimeType": "audio/webm",
                            "data": audio_b64
                        }
                    },
                    {
                        "text": "Transcribe the audio accurately. Output only the transcribed Spanish text, nothing else."
                    }
                ]
            }]
        }
        
        response = requests.post(url, headers=headers, json=payload_data, timeout=20)
        
        if response.status_code == 200:
            transcribed_text = response.json()["candidates"]["content"]["parts"][0]["text"].strip()
            return {"text": transcribed_text}
        else:
            raise HTTPException(status_code=response.status_code, detail=response.text)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gemini Audio Transcribe failed: {str(e)}")

@app.get("/", tags=["Health Check"])
def read_root():
    return {
        "status": "online",
        "app_name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT
    }
