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
    description="Backend oparty w 100% o darmowe Google Gemini API.",
)

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.post("/api/v1/transcribe", tags=["Audio core"])
async def transcribe_audio(file: UploadFile = File(...)):
    """
    Bezpieczny endpoint transkrypcji oparty o Google Gemini 2.5 Flash.
    Izoluje klucz API w parametrach query, aby kropki w kluczu nie niszczyły domeny.
    """
    gemini_key = os.getenv("GEMINI_API_KEY", "")
    if not gemini_key:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY is not configured on the backend.")
        
    try:
        audio_bytes = await file.read()
        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
        
        # POPRAWKA: Czysty URL domeny bez wstrzykiwania zmiennej f-stringiem
        url = "https://googleapis.com"
        
        # Przekazujemy klucz jako wydzielony słownik - requests sam zadba o bezpieczne kodowanie URL
        query_params = {"key": gemini_key}
        headers = {"Content-Type": "application/json"}
        
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
                        "text": "Transcribe this audio file accurately. Return ONLY the transcribed Spanish text, with no extra commentary."
                    }
                ]
            }]
        }
        
        # Wywołanie z jawnym parametrem params=query_params
        response = requests.post(url, headers=headers, json=payload_data, params=query_params, timeout=20)
        
        if response.status_code == 200:
            transcribed_text = response.json()["candidates"]["content"]["parts"]["text"].strip()
            return {"text": transcribed_text}
        else:
            raise HTTPException(status_code=response.status_code, detail=response.text)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gemini Audio Transcribe failed: {str(e)}")

@app.get("/", tags=["Health Check"])
def read_root():
    return {"status": "online", "app_name": settings.PROJECT_NAME, "version": settings.VERSION}
