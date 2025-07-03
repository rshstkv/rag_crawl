"""
Основное FastAPI приложение для RAG Crawl.
"""

import logging
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from .config import settings
from .database.connection import create_tables
from .api import chat, documents, health

# Настройка логирования
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения."""
    # Startup
    logger.info("Запуск RAG Crawl сервиса...")
    
    # Создание таблиц БД
    create_tables()
    logger.info("Таблицы базы данных созданы")
    
    logger.info(f"Сервис запущен на http://{settings.app_host}:{settings.app_port}")
    logger.info(f"API документация доступна на http://{settings.app_host}:{settings.app_port}/docs")
    logger.info(f"Frontend доступен на http://localhost:3000")
    
    yield
    
    # Shutdown
    logger.info("Остановка RAG Crawl сервиса...")


# Создание FastAPI приложения
app = FastAPI(
    title="RAG Crawl API",
    description="RAG микросервис для индексации документов и диалогового интерфейса",
    version="0.1.0",
    lifespan=lifespan
)

# CORS middleware - настройка для работы с Next.js фронтендом
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js dev server
        "http://localhost:3001",  # Next.js dev server (alternative port)
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://localhost:8000",  # FastAPI
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Подключение роутеров API
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(documents.router, prefix="/api/documents", tags=["documents"])
app.include_router(health.router, prefix="/api", tags=["health"])

# Корневой endpoint с информацией о сервисе
@app.get("/")
async def root():
    """Информация о сервисе."""
    return {
        "service": "RAG Crawl API",
        "version": "0.1.0",
        "description": "RAG микросервис для индексации документов и диалогового интерфейса",
        "docs": "/docs",
        "frontend": "http://localhost:3000",
        "api_base": "/api"
    }


if __name__ == "__main__":
    # Запуск сервера
    uvicorn.run(
        "rag_crawl.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_reload,
        log_level=settings.log_level.lower()
    ) 