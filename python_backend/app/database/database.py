from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Criar engine do SQLAlchemy
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False}  # Necessário apenas para SQLite
)

# Criar sessão local
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Criar base para os modelos
Base = declarative_base()

def get_db():
    """Função para obter uma sessão do banco de dados."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 