"""
Модуль для управления подключениями к базе данных.
"""

from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from ..config import settings

# Создаем движок SQLAlchemy
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,  # Проверка соединения перед использованием
    pool_recycle=300,    # Переподключение каждые 5 минут
)

# Создаем фабрику сессий
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency для получения сессии базы данных в FastAPI.
    Используется для dependency injection.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables() -> None:
    """Создает все таблицы в базе данных."""
    from .models import Base
    Base.metadata.create_all(bind=engine)


def drop_tables() -> None:
    """Удаляет все таблицы из базы данных. ИСПОЛЬЗУЙТЕ ОСТОРОЖНО!"""
    from .models import Base
    Base.metadata.drop_all(bind=engine) 