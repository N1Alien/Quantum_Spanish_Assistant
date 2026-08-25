import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ENV_FILE_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(dotenv_path=ENV_FILE_PATH, override=True)


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class Settings(BaseSettings):
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "Quantum Spanish Assistant API")
    VERSION: str = os.getenv("VERSION", "1.0.0")
    API_V1_STR: str = os.getenv("API_V1_STR", "/api/v1")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "ollama")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "llama3")
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://admin:secret@localhost:5432/quantum_spanish_db",
    )

    VECTOR_DB_PROVIDER: str = os.getenv("VECTOR_DB_PROVIDER", "chroma")
    PGVECTOR_CONNECTION_STRING: str = os.getenv("PGVECTOR_CONNECTION_STRING", "")
    PGVECTOR_COLLECTION: str = os.getenv("PGVECTOR_COLLECTION", "quantum_spanish_docs")
    CHROMA_PERSIST_DIRECTORY: str = os.getenv("CHROMA_PERSIST_DIRECTORY", os.path.join(BASE_DIR, "chroma_db"))

    ENABLE_WEB_INGESTION: bool = _env_bool("ENABLE_WEB_INGESTION", True)

    model_config = SettingsConfigDict(extra="ignore")


settings = Settings()
