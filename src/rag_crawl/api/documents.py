"""
API endpoints для управления документами.
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database.connection import get_db
from ..services.llama_service import LlamaIndexService

router = APIRouter()


class DocumentResponse(BaseModel):
    """Модель ответа с информацией о документе."""
    id: int
    title: str
    source_type: str
    namespace: str
    created_at: str
    chunks_count: int


class UploadResponse(BaseModel):
    """Модель ответа при загрузке документа."""
    id: int
    title: str
    namespace: str
    message: str


class ReindexRequest(BaseModel):
    """Модель запроса для переиндексации."""
    document_ids: Optional[List[int]] = None
    namespace: Optional[str] = None


class ReindexResponse(BaseModel):
    """Модель ответа при переиндексации."""
    message: str
    documents_processed: int
    total_documents: int
    errors: Optional[List[str]] = None


def get_llama_service(db: Session = Depends(get_db)) -> LlamaIndexService:
    """Dependency для получения LlamaIndex сервиса."""
    return LlamaIndexService(db)


@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    namespace: str = Form(default="default"),
    service: LlamaIndexService = Depends(get_llama_service)
):
    """
    Загрузка и обработка документа через LlamaIndex IngestionPipeline.
    """
    # Проверка размера файла
    if file.size and file.size > 100 * 1024 * 1024:  # 100MB
        raise HTTPException(status_code=413, detail="Файл слишком большой (максимум 100MB)")
    
    try:
        document = await service.upload_document(
            file=file,
            namespace=namespace
        )
        
        return UploadResponse(
            id=document.id,
            title=document.title,
            namespace=document.namespace,
            message="Документ успешно загружен и проиндексирован"
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка загрузки документа: {str(e)}")


@router.get("/", response_model=List[DocumentResponse])
async def get_documents(
    namespace: Optional[str] = None,
    service: LlamaIndexService = Depends(get_llama_service)
):
    """Получение списка документов."""
    try:
        documents = await service.get_documents(namespace=namespace)
        return [DocumentResponse(**doc) for doc in documents]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{document_id}/content")
async def get_document_content(
    document_id: int,
    service: LlamaIndexService = Depends(get_llama_service)
):
    """Получить содержимое документа с чанками."""
    try:
        content = await service.get_document_content(document_id)
        if "error" in content:
            raise HTTPException(status_code=404, detail=content["error"])
        return content
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{document_id}/chunks")
async def get_document_chunks(
    document_id: int,
    service: LlamaIndexService = Depends(get_llama_service)
):
    """Получить все чанки документа."""
    try:
        chunks = await service.get_document_chunks(document_id)
        return {"chunks": chunks}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reindex", response_model=ReindexResponse)
async def reindex_documents(
    request: Optional[ReindexRequest] = None,
    service: LlamaIndexService = Depends(get_llama_service)
):
    """Переиндексация документов в namespace."""
    try:
        namespace = request.namespace if request else None
        result = await service.reindex_all_documents(namespace)
        return ReindexResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reindex-all", response_model=ReindexResponse)
async def reindex_all_documents(
    service: LlamaIndexService = Depends(get_llama_service)
):
    """Переиндексация всех документов во всех namespace."""
    try:
        result = await service.reindex_all_documents()
        return ReindexResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{document_id}/reindex")
async def reindex_single_document(
    document_id: int,
    service: LlamaIndexService = Depends(get_llama_service)
):
    """Переиндексация одного документа."""
    try:
        result = await service.reindex_document(document_id)
        if not result["success"]:
            raise HTTPException(status_code=404, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reindex-batch")
async def reindex_batch_documents(
    request: ReindexRequest,
    service: LlamaIndexService = Depends(get_llama_service)
):
    """Переиндексация группы документов."""
    try:
        if not request.document_ids:
            raise HTTPException(status_code=400, detail="Список document_ids не может быть пустым")
        
        result = await service.reindex_documents_batch(request.document_ids)
        return ReindexResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/diagnostics")
async def get_system_diagnostics(
    service: LlamaIndexService = Depends(get_llama_service)
):
    """Получить диагностическую информацию о системе."""
    try:
        diagnostics = await service.get_system_diagnostics()
        return diagnostics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{document_id}")
async def delete_document(
    document_id: int,
    service: LlamaIndexService = Depends(get_llama_service)
):
    """Удаление документа и его векторов."""
    try:
        success = await service.delete_document(document_id)
        if not success:
            raise HTTPException(status_code=404, detail="Документ не найден")
        
        return {"message": "Документ успешно удален"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/resync/{namespace}")
async def resync_namespace(
    namespace: str,
    service: LlamaIndexService = Depends(get_llama_service)
):
    """Ресинхронизация документов в namespace."""
    try:
        result = await service.resync_namespace(namespace)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 