"""
API endpoints для управления кроулингом веб-сайтов.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sse_starlette import EventSourceResponse
from sqlalchemy.orm import Session
from typing import Dict, Any

from ..database.connection import get_db
from ..services.crawl_service import CrawlService, CrawlConfig, get_crawl_service
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


@router.post("/start")
async def start_crawl(
    config: CrawlConfigRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Запускает кроулинг с Server-Sent Events."""
    try:
        # Создание конфигурации кроулинга
        crawl_config = CrawlConfig(
            url=config.url,
            max_depth=config.max_depth,
            max_pages=config.max_pages,
            browser_type=config.browser_type,
            wait_until=config.wait_until,
            exclude_external_links=config.exclude_external_links,
            exclude_external_images=config.exclude_external_images,
            word_count_threshold=config.word_count_threshold,
            page_timeout=config.page_timeout,
            namespace=config.namespace
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