import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Dynamiczne wyliczenie ścieżki do pliku .env
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ENV_FILE_PATH = os.path.join(BASE_DIR, ".env")

# Jawne załadowanie zmiennych do os.environ
load_dotenv(dotenv_path=ENV_FILE_PATH, override=True)

class Settings(BaseSettings):
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "Quantum Spanish Assistant API")
    VERSION: str = os.getenv("VERSION", "1.0.0")
    API_V1_STR: str = os.getenv("API_V1_STR", "/api/v1")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "llama3")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://admin:secret@localhost:5432/quantum_spanish_db")

    model_config = SettingsConfigDict(extra="ignore")

settings = Settings()
