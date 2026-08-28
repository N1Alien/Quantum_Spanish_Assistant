import os
import sys
from fastapi import FastAPI, UploadFile, File, HTTPException
import google.generativeai as genai
from app.core.config import settings
from app.core.database import engine, Base
from app.api.endpoints import router as api_router

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Backend oparty w 100% o oficjalne Google Gemini SDK.",
)

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.post("/api/v1/transcribe", tags=["Audio core"])
async def transcribe_audio(file: UploadFile = File(...)):
    """
    Bezpieczny endpoint transkrypcji oparty o oficjalne Google GenerativeAI SDK.
    Używa najnowszego, aktywnego modelu gemini-3.6-flash.
    """
    gemini_key = os.getenv("GEMINI_API_KEY", "")
    if not gemini_key:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY is not configured on the backend.")
        
    try:
        genai.configure(api_key=gemini_key.strip())
        audio_bytes = await file.read()
        
        # POPRAWKA: Przejście na aktualny, wspierany model produkcyjny
        model = genai.GenerativeModel("gemini-3.6-flash")
        
        response = model.generate_content([
            {
                "mime_type": "audio/webm",
                "data": audio_bytes
            },
            "Transcribe this audio file accurately. Return ONLY the transcribed Spanish text, with no extra commentary or translation."
        ])
        
        return {"text": response.text.strip()}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Google Gemini Audio SDK failed: {str(e)}")

@app.get("/", tags=["Health Check"])
def read_root():
    return {"status": "online", "app_name": settings.PROJECT_NAME, "version": settings.VERSION}
