"""
Сервис для интеграции с Crawl4AI API.
Предоставляет методы для кроулинга веб-сайтов и управления задачами.
"""

import json
import logging
import asyncio
import hashlib
import re
from datetime import datetime
from typing import Dict, List, Optional, AsyncGenerator, Any
from urllib.parse import urlparse

import httpx
from pydantic import BaseModel, HttpUrl, Field, validator
from sqlalchemy.orm import Session
from sse_starlette import ServerSentEvent
from fastapi import HTTPException

from ..database.models import Document, DocumentChunk, generate_vector_id
from ..config import settings

logger = logging.getLogger(__name__)

# Специализированный логгер для кроулинга
crawl_logger = logging.getLogger("rag_crawl.crawl")


class CrawlConfig(BaseModel):
    """Конфигурация для кроулинга."""
    
    url: HttpUrl
    max_depth: int = Field(default=3, ge=1, le=10)
    max_pages: int = Field(default=50, ge=1, le=5000)
    browser_type: str = Field(default="chromium", pattern="^(chromium|firefox|webkit)$")
    wait_until: str = Field(default="networkidle", pattern="^(networkidle|domcontentloaded|load)$")
    exclude_external_links: bool = Field(default=False)
    exclude_external_images: bool = Field(default=False)
    word_count_threshold: int = Field(default=5, ge=1)
    page_timeout: int = Field(default=60000, ge=10000, le=300000)
    namespace: str = Field(default="default", min_length=1, max_length=50)
    stream: bool = Field(default=True)
    
    @validator('url')
    def validate_url(cls, v):
        """Валидация URL для безопасности."""
        if not URLValidator.validate_url(str(v)):
            raise ValueError('Недопустимый URL для кроулинга')
        return v


class URLValidator:
    """Валидатор URL для безопасности."""
    
    ALLOWED_SCHEMES = ['http', 'https']
    BLOCKED_DOMAINS = ['localhost', '127.0.0.1', '0.0.0.0', '::1']
    BLOCKED_PORTS = [22, 23, 25, 53, 135, 139, 445, 993, 995]
    
    @classmethod
    def validate_url(cls, url: str) -> bool:
        """Валидирует URL для безопасности."""
        try:
            parsed = urlparse(url)
            
            # Проверка схемы
            if parsed.scheme not in cls.ALLOWED_SCHEMES:
                return False
            
            # Проверка заблокированных доменов
            if parsed.hostname in cls.BLOCKED_DOMAINS:
                return False
            
            # Проверка приватных IP адресов
            if cls._is_private_ip(parsed.hostname):
                return False
            
            # Проверка портов
            if parsed.port and parsed.port in cls.BLOCKED_PORTS:
                return False
            
            return True
            
        except Exception:
            return False
    
    @staticmethod
    def _is_private_ip(hostname: str) -> bool:
        """Проверяет, является ли IP приватным."""
        try:
            import ipaddress
            ip = ipaddress.ip_address(hostname)
            return ip.is_private
        except Exception:
            return False


class DocumentProcessingError(Exception):
    """Исключение для ошибок обработки документов."""
    
    def __init__(self, document_id: int, reason: str):
        self.document_id = document_id
        self.reason = reason
        super().__init__(f"Document {document_id} processing failed: {reason}")


class CrawlService:
    """Сервис для кроулинга веб-сайтов."""
    
    def __init__(self, db: Session):
        self._db = db
        self._crawl_api_url = settings.crawl4ai_api_url
        self._active_tasks: Dict[str, asyncio.Task] = {}
        self._http_client = httpx.AsyncClient(timeout=settings.crawl4ai_timeout)
        
    async def __aenter__(self):
        """Async context manager entry."""
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self._http_client.aclose()

    async def start_crawl(self, config: CrawlConfig) -> AsyncGenerator[ServerSentEvent, None]:
        """Запускает кроулинг с стримингом результатов."""
        crawl_request = {
            "url": str(config.url),
            "max_depth": config.max_depth,
            "max_pages": config.max_pages,
            "browser_type": config.browser_type,
            "wait_until": config.wait_until,
            "exclude_external_links": config.exclude_external_links,
            "exclude_external_images": config.exclude_external_images,
            "word_count_threshold": config.word_count_threshold,
            "page_timeout": config.page_timeout,
            "stream": True
        }
        
        try:
            async with self._http_client.stream(
                "POST",
                f"{self._crawl_api_url}/crawl/stream",
                json=crawl_request,
                headers={"Content-Type": "application/json"}
            ) as response:
                task_id = None
                
                if response.status_code != 200:
                    error_data = await response.aread()
                    raise HTTPException(
                        status_code=response.status_code, 
                        detail=f"Crawl4AI API error: {error_data.decode()}"
                    )
                
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        try:
                            data = json.loads(line[6:])
                            
                            if data.get("type") == "crawl_started":
                                task_id = data.get("task_id")
                                crawl_logger.info(f"Кроулинг запущен: {task_id}, URL: {config.url}")
                                
                            elif data.get("type") == "page_complete":
                                # Обработка и сохранение страницы
                                page_data = data.get("page", {})
                                await self._process_crawled_page(page_data, config.namespace, task_id)
                                crawl_logger.info(f"Страница обработана: {page_data.get('url', 'Unknown')}")
                                
                            elif data.get("type") == "progress":
                                processed = data.get("processed", 0)
                                total = data.get("total", 0)
                                crawl_logger.info(f"Прогресс: {processed}/{total} страниц")
                                
                            elif data.get("type") == "error":
                                error_msg = data.get("message", "Unknown error")
                                crawl_logger.error(f"Ошибка кроулинга: {error_msg}")
                                
                            # Отправка события клиенту
                            yield ServerSentEvent(data=json.dumps(data))
                            
                            if data.get("type") == "crawl_complete":
                                crawl_logger.info(f"Кроулинг завершен: {task_id}")
                                break
                                
                        except json.JSONDecodeError as e:
                            crawl_logger.error(f"Ошибка парсинга JSON: {e}, line: {line}")
                            continue
                            
        except Exception as e:
            crawl_logger.error(f"Ошибка при выполнении кроулинга: {e}")
            error_event = {
                "type": "error",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }
            yield ServerSentEvent(data=json.dumps(error_event))

    async def _process_crawled_page(self, page_data: Dict, namespace: str, task_id: str) -> None:
        """Обрабатывает и сохраняет парсенную страницу."""
        try:
            # Создание объекта документа из веб-страницы
            document_data = {
                "title": page_data.get("title", "Без названия"),
                "source_type": "web",
                "namespace": namespace,
                "source_url": page_data["url"],
                "content": page_data.get("markdown", ""),
                "crawl_depth": page_data.get("depth", 0),
                "crawl_task_id": task_id,
                "crawl_metadata": {
                    "url": page_data["url"],
                    "title": page_data.get("title", ""),
                    "depth": page_data.get("depth", 0),
                    "crawled_at": page_data.get("crawled_at"),
                    "status_code": page_data.get("status_code"),
                    "processing_time": page_data.get("processing_time"),
                    "internal_links": page_data.get("internal_links", []),
                    "external_links": page_data.get("external_links", []),
                    "images": page_data.get("images", [])
                }
            }
            
            # Создание документа
            document = await self._create_document_from_web_content(document_data)
            crawl_logger.info(f"Документ создан: {document.id} для URL: {page_data['url']}")
            
        except Exception as e:
            crawl_logger.error(f"Ошибка при обработке страницы {page_data.get('url')}: {e}")
            raise DocumentProcessingError(document_id=0, reason=str(e))

    async def _create_document_from_web_content(self, document_data: Dict) -> Document:
        """Создает документ из веб-контента."""
        try:
            # Генерация хэша контента
            content_hash = hashlib.sha256(document_data["content"].encode()).hexdigest()
            
            # Проверка на дубликаты
            existing_doc = self._db.query(Document).filter(
                Document.content_hash == content_hash,
                Document.namespace == document_data["namespace"],
                Document.is_active == True
            ).first()
            
            if existing_doc:
                crawl_logger.info(f"Документ уже существует: {existing_doc.id}")
                return existing_doc
            
            # Создание записи в БД
            db_document = Document(
                title=document_data["title"],
                source_type=document_data["source_type"],
                namespace=document_data["namespace"],
                source_url=document_data["source_url"],
                content_hash=content_hash,
                vector_id=generate_vector_id(),
                crawl_depth=document_data.get("crawl_depth"),
                crawl_task_id=document_data.get("crawl_task_id"),
                crawl_metadata=document_data.get("crawl_metadata"),
                metadata_json=document_data.get("crawl_metadata", {}),
                is_active=True
            )
            
            self._db.add(db_document)
            self._db.flush()
            
            # Обработка и создание чанков
            chunks = await self._process_content_for_indexing(
                content=document_data["content"],
                document_id=db_document.id,
                metadata=document_data.get("crawl_metadata", {})
            )
            
            # Сохранение чанков в БД
            for chunk in chunks:
                self._db.add(chunk)
            
            db_document.chunks_count = len(chunks)
            self._db.commit()
            
            return db_document
            
        except Exception as e:
            self._db.rollback()
            crawl_logger.error(f"Ошибка при создании документа из веб-контента: {e}")
            raise DocumentProcessingError(document_id=0, reason=str(e))

    async def _process_content_for_indexing(
        self, 
        content: str, 
        document_id: int, 
        metadata: Dict
    ) -> List[DocumentChunk]:
        """Разбивает веб-контент на чанки для индексации."""
        # Очистка веб-контента
        clean_content = self._clean_web_content(content)
        
        # Разбивка на чанки
        chunks = self._split_into_chunks(
            content=clean_content,
            chunk_size=settings.web_content_chunk_size,
            chunk_overlap=settings.web_content_chunk_overlap
        )
        
        document_chunks = []
        for i, chunk in enumerate(chunks):
            chunk_metadata = {
                **metadata,
                "chunk_index": i,
                "chunk_type": "web_content",
                "document_id": document_id
            }
            
            document_chunks.append(DocumentChunk(
                document_id=document_id,
                chunk_index=i,
                content=chunk,
                vector_id=generate_vector_id(),
                metadata_json=chunk_metadata
            ))
        
        return document_chunks

    def _clean_web_content(self, content: str) -> str:
        """Очищает веб-контент от лишних элементов."""
        # Удаление лишних пробелов и переносов
        content = re.sub(r'\n\s*\n', '\n\n', content)
        content = re.sub(r'[ \t]+', ' ', content)
        
        # Удаление навигационных элементов
        content = re.sub(
            r'(Menu|Navigation|Footer|Header|Sidebar|Breadcrumb).*?(?=\n\n|\Z)', 
            '', 
            content, 
            flags=re.IGNORECASE
        )
        
        # Удаление повторяющихся ссылок
        content = re.sub(r'(https?://[^\s]+)', '', content)
        
        return content.strip()

    def _split_into_chunks(
        self, 
        content: str, 
        chunk_size: int = 1024, 
        chunk_overlap: int = 200
    ) -> List[str]:
        """Разбивает контент на чанки."""
        if len(content) <= chunk_size:
            return [content]
        
        chunks = []
        start = 0
        
        while start < len(content):
            end = start + chunk_size
            
            # Попытка найти удобное место для разрыва
            if end < len(content):
                # Ищем последнюю точку или перенос строки
                for i in range(end, max(start + chunk_size // 2, start), -1):
                    if content[i] in '.!?\n':
                        end = i + 1
                        break
            
            chunk = content[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - chunk_overlap
            
        return chunks

    async def stop_crawl(self, task_id: str) -> Dict:
        """Останавливает задачу кроулинга."""
        try:
            response = await self._http_client.post(
                f"{self._crawl_api_url}/crawl/stop/{task_id}"
            )
            response.raise_for_status()
            result = response.json()
            crawl_logger.info(f"Задача остановлена: {task_id}")
            return result
        except Exception as e:
            crawl_logger.error(f"Ошибка при остановке задачи {task_id}: {e}")
            raise

    async def pause_crawl(self, task_id: str) -> Dict:
        """Приостанавливает задачу кроулинга."""
        try:
            response = await self._http_client.post(
                f"{self._crawl_api_url}/crawl/pause/{task_id}"
            )
            response.raise_for_status()
            result = response.json()
            crawl_logger.info(f"Задача приостановлена: {task_id}")
            return result
        except Exception as e:
            crawl_logger.error(f"Ошибка при приостановке задачи {task_id}: {e}")
            raise

    async def resume_crawl(self, task_id: str) -> Dict:
        """Возобновляет задачу кроулинга."""
        try:
            response = await self._http_client.post(
                f"{self._crawl_api_url}/crawl/resume/{task_id}"
            )
            response.raise_for_status()
            result = response.json()
            crawl_logger.info(f"Задача возобновлена: {task_id}")
            return result
        except Exception as e:
            crawl_logger.error(f"Ошибка при возобновлении задачи {task_id}: {e}")
            raise

    async def get_active_tasks(self) -> Dict:
        """Получает список активных задач."""
        try:
            response = await self._http_client.get(
                f"{self._crawl_api_url}/crawl/active"
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            crawl_logger.error(f"Ошибка при получении активных задач: {e}")
            raise

    async def get_task_status(self, task_id: str) -> Dict:
        """Получает статус конкретной задачи."""
        try:
            response = await self._http_client.get(
                f"{self._crawl_api_url}/crawl/status/{task_id}"
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            crawl_logger.error(f"Ошибка при получении статуса задачи {task_id}: {e}")
            raise

    async def stop_all_crawls(self) -> Dict:
        """Останавливает все активные задачи."""
        try:
            response = await self._http_client.delete(
                f"{self._crawl_api_url}/crawl/stop-all"
            )
            response.raise_for_status()
            result = response.json()
            crawl_logger.info("Все задачи остановлены")
            return result
        except Exception as e:
            crawl_logger.error(f"Ошибка при остановке всех задач: {e}")
            raise


# Dependency injection функция
def get_crawl_service(db: Session) -> CrawlService:
    """Создает экземпляр CrawlService."""
    return CrawlService(db) 