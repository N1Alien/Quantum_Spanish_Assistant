import os
import sys
import logging
from fastapi import FastAPI, UploadFile, File, HTTPException
from groq import Groq, RateLimitError
from starlette.concurrency import run_in_threadpool
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
    description="Spanish learning API with Groq Whisper speech transcription.",
)

app.include_router(api_router, prefix=settings.API_V1_STR)

logger = logging.getLogger(__name__)
MAX_AUDIO_SIZE = 25 * 1024 * 1024

@app.post("/api/v1/transcribe", tags=["Audio core"])
async def transcribe_audio(file: UploadFile = File(...)):
    """Transcribe Spanish audio through Groq Whisper."""
    groq_key = settings.GROQ_API_KEY.strip()
    if not groq_key:
        raise HTTPException(status_code=503, detail="Transcription is not configured: GROQ_API_KEY is missing.")

    try:
        audio_bytes = await file.read(MAX_AUDIO_SIZE + 1)
        if not audio_bytes:
            raise HTTPException(status_code=400, detail="The audio recording is empty.")
        if len(audio_bytes) > MAX_AUDIO_SIZE:
            raise HTTPException(status_code=413, detail="Audio file is too large. Maximum size is 25 MB.")

        def transcribe():
            with Groq(api_key=groq_key) as client:
                return client.audio.transcriptions.create(
                    file=(file.filename or "audio.webm", audio_bytes),
                    model="whisper-large-v3-turbo",
                    language="es",
                    response_format="json",
                )

        transcription = await run_in_threadpool(transcribe)
        text = transcription.text.strip()
        if not text:
            raise HTTPException(status_code=422, detail="No Spanish speech was detected. Please try recording again.")
        return {"text": text}
    except RateLimitError as e:
        raise HTTPException(
            status_code=429,
            detail="The transcription service is busy or its request limit was reached. Please wait briefly and try again.",
        ) from e
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Audio transcription failed")
        raise HTTPException(status_code=502, detail="Audio transcription failed. Please try again shortly.") from e
    finally:
        await file.close()

@app.get("/", tags=["Health Check"])
def read_root():
    return {"status": "online", "app_name": settings.PROJECT_NAME, "version": settings.VERSION}
