import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:

    sys.path.insert(0, BASE_DIR)
import threading
from fastapi import FastAPI
from app.core.config import settings
from app.core.database import engine, Base
from app.api.endpoints import router as api_router
from app.services.vector_service import vector_service

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
