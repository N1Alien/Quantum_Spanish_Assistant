import os
import sys
from fastapi import FastAPI
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
    description="Zoptymalizowany, szybki backend chmurowy dla Gemini API.",
)

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/", tags=["Health Check"])
def read_root():
    return {"status": "online", "app_name": settings.PROJECT_NAME, "version": settings.VERSION}
