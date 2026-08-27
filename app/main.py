import os
import sys
import uuid
from fastapi import FastAPI, UploadFile, File, HTTPException
from groq import Groq
from app.core.config import settings
from app.core.database import engine, Base
from app.api.endpoints import router as api_router

# Dynamiczne wstrzyknięcie ścieżki projektu
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Automatyczne tworzenie tabel PostgreSQL w Neon.tech przy starcie
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Produkcyjny backend obsługujący hybrydowego asystenta językowego.",
)

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.post("/api/v1/transcribe", tags=["Audio core"])
async def transcribe_audio(file: UploadFile = File(...)):
    """
    Bezpieczny i stabilny endpoint pośredniczący dla Groq Whisper.
    Zapisuje plik tymczasowo w /tmp i wysyła go przez oficjalne SDK,
    co gwarantuje ominięcie błędu 500 HTML.
    """
    if not settings.GROQ_API_KEY:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY is not configured on the backend.")
        
    # Tworzymy unikalną nazwę pliku w folderze tymczasowym, który Render pozwala zapisywać
    temp_file_path = f"/tmp/{uuid.uuid4()}.webm"
    
    try:
        # Odczytujemy surowe bajty przesłane ze Streamlita
        audio_bytes = await file.read()
        
        # Zapisujemy fizycznie plik w /tmp, aby oficjalne SDK mogło go odczytać jako plik dyskowy
        with open(temp_file_path, "wb") as temp_file:
            temp_file.write(audio_bytes)
            
        # Inicjalizacja oficjalnego klienta Groq SDK
        client = Groq(api_key=settings.GROQ_API_KEY)
        
        # Wywołanie oficjalnego potoku Whisper - SDK samo dba o idealny format multipart
        with open(temp_file_path, "rb") as audio_file_obj:
            transcription = client.audio.transcriptions.create(
                file=("audio.webm", audio_file_obj),
                model="whisper-large-v3",
                language="es",
                response_format="json"
            )
            
        return {"text": transcription.text.strip()}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Groq Whisper integration failed: {str(e)}")
        
    finally:
        # Kategorycznie usuwamy plik z folderu /tmp po zakończeniu operacji, by nie zapychać RAM-u kontenera
        if os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except Exception:
                pass

@app.get("/", tags=["Health Check"])
def read_root():
    return {
        "status": "online",
        "app_name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT
    }
