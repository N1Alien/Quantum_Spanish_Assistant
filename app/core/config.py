import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Quantum Spanish Assistant API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "production"

    # Dostawca modeli - domyślnie pusty, wymuszany przez zmienne środowiskowe
    LLM_PROVIDER: str = "groq"
    LLM_MODEL: str = "llama3"
    OLLAMA_BASE_URL: str = "http://localhost:11434"

    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.1-8b-instant"

    DATABASE_URL: str = "postgresql://admin:secret@localhost:5432/quantum_spanish_db"

    VECTOR_DB_PROVIDER: str = "pgvector"
    PGVECTOR_CONNECTION_STRING: str = ""
    PGVECTOR_COLLECTION: str = "quantum_spanish_docs"
    CHROMA_PERSIST_DIRECTORY: str = "./chroma_db"

    ENABLE_WEB_INGESTION: bool = False

    # Ta linijka to absolutny klucz - informuje Pydantic, aby automatycznie
    # czytał systemowe zmienne środowiskowe (case-insensitive) i nadpisywał nimi powyższe pola
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8", 
        extra="ignore"
    )

settings = Settings()
