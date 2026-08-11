from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

# Inicjalizacja silnika bazy danych PostgreSQL
engine = create_engine(settings.DATABASE_URL)

# Fabryka sesji (zarządza transakcjami w bazie)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Klasa bazowa dla naszych modeli (tabel) ORM
Base = declarative_base()

# Profesjonalny generator sesji (Dependency Injection pattern)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
