"""
API endpoints для управления кроулингом веб-сайтов.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Query
from fastapi.responses import StreamingResponse
from sse_starlette import EventSourceResponse
from sqlalchemy.orm import Session
from typing import Dict, Any

from ..database.connection import get_db
from ..services.crawl_service import CrawlService, CrawlConfig
from pydantic import BaseModel

router = APIRouter(prefix="/api/crawl", tags=["crawl"])

# Pydantic модели для API
class CrawlConfigRequest(BaseModel):
    """Запрос на кроулинг."""
    url: str
    max_depth: int = 3
    max_pages: int = 50
    browser_type: str = "chromium"
    wait_until: str = "networkidle"
    exclude_external_links: bool = False
    exclude_external_images: bool = False
    word_count_threshold: int = 5
    page_timeout: int = 60000
    namespace: str = "default"

class TaskResponse(BaseModel):
    """Ответ для операций с задачами."""
    success: bool
    message: str
    task_id: str
    timestamp: str

class TaskStatusResponse(BaseModel):
    """Ответ со статусом задачи."""
    task_id: str
    status: str
    url: str
    progress: Dict[str, Any] = None

class ActiveTasksResponse(BaseModel):
    """Ответ со списком активных задач."""
    active_tasks: list[str]
    task_details: list[TaskStatusResponse]
    count: int


@router.get("/start")
async def start_crawl(
    url: str = Query(..., description="URL для кроулинга"),
    max_depth: int = Query(3, ge=1, le=10, description="Глубина кроулинга"),
    max_pages: int = Query(50, ge=1, le=5000, description="Максимальное количество страниц"),
    browser_type: str = Query("chromium", description="Тип браузера"),
    wait_until: str = Query("networkidle", description="Условие ожидания"),
    exclude_external_links: bool = Query(False, description="Исключить внешние ссылки"),
    exclude_external_images: bool = Query(False, description="Исключить внешние изображения"),
    word_count_threshold: int = Query(5, ge=0, description="Минимальное количество слов"),
    page_timeout: int = Query(60000, ge=1000, le=300000, description="Таймаут страницы в мс"),
    namespace: str = Query("default", description="Namespace для индексации"),
    request: Request = None,
    db: Session = Depends(get_db)
):
    """Запускает кроулинг с Server-Sent Events."""
    try:
        # Создание конфигурации кроулинга
        crawl_config = CrawlConfig(
            url=url,
            max_depth=max_depth,
            max_pages=max_pages,
            browser_type=browser_type,
            wait_until=wait_until,
            exclude_external_links=exclude_external_links,
            exclude_external_images=exclude_external_images,
            word_count_threshold=word_count_threshold,
            page_timeout=page_timeout,
            namespace=namespace
        )
        
        # Создание сервиса кроулинга
        crawl_service = CrawlService(db)
        
        # Возвращение EventSourceResponse для SSE
        return EventSourceResponse(
            crawl_service.start_crawl(crawl_config),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Cache-Control"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop/{task_id}")
async def stop_crawl(
    task_id: str,
    db: Session = Depends(get_db)
):
    """Останавливает задачу кроулинга."""
    try:
        crawl_service = CrawlService(db)
        result = await crawl_service.stop_crawl(task_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pause/{task_id}")
async def pause_crawl(
    task_id: str,
    db: Session = Depends(get_db)
):
    """Приостанавливает задачу кроулинга."""
    try:
        crawl_service = CrawlService(db)
        result = await crawl_service.pause_crawl(task_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/resume/{task_id}")
async def resume_crawl(
    task_id: str,
    db: Session = Depends(get_db)
):
    """Возобновляет задачу кроулинга."""
    try:
        crawl_service = CrawlService(db)
        result = await crawl_service.resume_crawl(task_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/stop-all")
async def stop_all_crawls(
    db: Session = Depends(get_db)
):
    """Останавливает все активные задачи."""
    try:
        crawl_service = CrawlService(db)
        result = await crawl_service.stop_all_crawls()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/active")
async def get_active_tasks(
    db: Session = Depends(get_db)
):
    """Получает список активных задач."""
    try:
        crawl_service = CrawlService(db)
        result = await crawl_service.get_active_tasks()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{task_id}")
async def get_task_status(
    task_id: str,
    db: Session = Depends(get_db)
):
    """Получает статус задачи."""
    try:
        crawl_service = CrawlService(db)
        result = await crawl_service.get_task_status(task_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Проверка состояния сервиса кроулинга."""
    return {
        "status": "healthy",
        "service": "crawl",
        "timestamp": "2024-01-01T00:00:00Z"
    } 