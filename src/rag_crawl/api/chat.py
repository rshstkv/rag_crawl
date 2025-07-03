"""
API endpoints для чата с документами.
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database.connection import get_db
from ..services.llama_service import LlamaIndexService

router = APIRouter()


class ChatRequest(BaseModel):
    """Модель запроса для чата."""
    message: str
    namespace: Optional[str] = None
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Модель ответа чата."""
    response: str
    sources: List[Dict[str, Any]]
    session_id: Optional[str] = None


class QueryRequest(BaseModel):
    """Модель запроса для простого поиска."""
    question: str
    namespace: Optional[str] = None


class QueryResponse(BaseModel):
    """Модель ответа поиска с debug информацией."""
    response: str
    sources: List[Dict[str, Any]]
    debug_info: Optional[Dict[str, Any]] = None
    total_documents: Optional[int] = None
    search_time_ms: Optional[float] = None


def get_llama_service(db: Session = Depends(get_db)) -> LlamaIndexService:
    """Dependency для получения LlamaIndex сервиса."""
    return LlamaIndexService(db)


@router.post("/chat", response_model=ChatResponse)
async def chat_with_documents(
    request: ChatRequest,
    service: LlamaIndexService = Depends(get_llama_service)
):
    """
    Чат с документами с сохранением контекста.
    Использует встроенный LlamaIndex ChatEngine.
    """
    try:
        result = await service.chat(
            message=request.message,
            namespace=request.namespace or "default",
            session_id=request.session_id
        )
        return ChatResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query", response_model=QueryResponse)
async def query_documents(
    request: QueryRequest,
    service: LlamaIndexService = Depends(get_llama_service)
):
    """
    Простой запрос к документам без сохранения контекста с debug информацией.
    Использует встроенный LlamaIndex QueryEngine.
    """
    try:
        result = await service.query(
            question=request.question,
            namespace=request.namespace or "default"
        )
        return QueryResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_chat_history(
    session_id: Optional[str] = None,
    namespace: Optional[str] = None,
    limit: int = 50,
    service: LlamaIndexService = Depends(get_llama_service)
):
    """Получение истории чатов."""
    try:
        history = await service.get_chat_history(
            session_id=session_id,
            namespace=namespace,
            limit=limit
        )
        return {"history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 