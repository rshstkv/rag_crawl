"""
API endpoints для health checks.
"""

import asyncio
import time
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session
import qdrant_client
from typing import Dict, Any

from ..config import settings
from ..database.connection import SessionLocal

router = APIRouter()


class HealthResponse(BaseModel):
    """Модель ответа health check."""
    status: str
    timestamp: str
    services: Dict[str, Any]


async def check_database() -> Dict[str, Any]:
    """Проверка подключения к PostgreSQL."""
    try:
        start_time = time.time()
        db = SessionLocal()
        
        # Простой запрос для проверки соединения
        db.execute(text("SELECT 1"))
        db.close()
        
        response_time = (time.time() - start_time) * 1000
        
        return {
            "status": "healthy",
            "response_time_ms": round(response_time, 2)
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


async def check_qdrant() -> Dict[str, Any]:
    """Проверка подключения к Qdrant."""
    try:
        start_time = time.time()
        
        client = qdrant_client.QdrantClient(
            host=settings.qdrant_host,
            port=settings.qdrant_port
        )
        
        # Проверка здоровья Qdrant
        collections = client.get_collections()
        
        response_time = (time.time() - start_time) * 1000
        
        return {
            "status": "healthy",
            "response_time_ms": round(response_time, 2),
            "collections_count": len(collections.collections)
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


async def check_azure_openai() -> Dict[str, Any]:
    """Проверка доступности Azure OpenAI."""
    try:
        from openai import AzureOpenAI
        
        start_time = time.time()
        
        client = AzureOpenAI(
            api_key=settings.azure_openai_api_key,
            azure_endpoint=settings.azure_openai_endpoint,
            api_version=settings.azure_openai_api_version
        )
        
        # Простой запрос для проверки
        response = client.chat.completions.create(
            model=settings.azure_openai_chat_deployment,
            messages=[{"role": "user", "content": "ping"}],
            max_tokens=1
        )
        
        response_time = (time.time() - start_time) * 1000
        
        return {
            "status": "healthy",
            "response_time_ms": round(response_time, 2),
            "model": settings.azure_openai_chat_deployment
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Базовая проверка здоровья сервиса."""
    return HealthResponse(
        status="healthy",
        timestamp=time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        services={}
    )


@router.get("/health/database")
async def health_database():
    """Проверка только базы данных."""
    result = await check_database()
    if result["status"] != "healthy":
        raise HTTPException(status_code=503, detail=result)
    return result


@router.get("/health/qdrant")
async def health_qdrant():
    """Проверка только Qdrant."""
    result = await check_qdrant()
    if result["status"] != "healthy":
        raise HTTPException(status_code=503, detail=result)
    return result


@router.get("/health/azure")
async def health_azure():
    """Проверка только Azure OpenAI."""
    result = await check_azure_openai()
    if result["status"] != "healthy":
        raise HTTPException(status_code=503, detail=result)
    return result 