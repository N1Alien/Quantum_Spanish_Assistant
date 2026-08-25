import os
import sys

# Dynamiczne wstrzyknięcie ścieżki projektu do pamięci Pythona
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from fastapi import FastAPI
from app.core.config import settings
from app.core.database import engine, Base
from app.api.endpoints import router as api_router
from app.services.vector_service import vector_service

# Automatyczna migracja i tworzenie tabel PostgreSQL w Dockerze przy starcie
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Produkcyjny backend obsługujący hybrydowego asystenta językowego.",
)

# Podłączamy router z punktami końcowymi API
app.include_router(api_router, prefix=settings.API_V1_STR)

# Automatyczne uruchomienie pobierania wiedzy z internetu na startupie
@app.on_event("startup")
def startup_event():
    vector_service.auto_fetch_web_knowledge()

@app.get("/", tags=["Health Check"])
def read_root():
    return {
        "status": "online",
        "app_name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT
    }
