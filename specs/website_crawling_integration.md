# Техническое задание: Интеграция парсинга сайтов в RAG систему

## Обзор

Добавление функции парсинга/кроулинга сайтов в существующую RAG систему для автоматического извлечения контента с веб-сайтов и его индексации в векторную базу данных Qdrant. Интеграция с микросервисом Crawl4AI для обеспечения надежного и масштабируемого кроулинга.

## Цели

1. **Расширение источников данных**: Добавить возможность парсинга веб-сайтов наряду с загрузкой документов
2. **Интерактивность**: Реализовать стриминг с показом прогресса в реальном времени через SSE
3. **Контроль процесса**: Предоставить возможность остановки, паузы и настройки параметров парсинга
4. **Автоматическая индексация**: Обеспечить автоматическое добавление парсенных данных в Qdrant с метаданными
5. **Управление задачами**: Мониторинг активных задач и возможность их остановки
6. **Настройка параметров**: Выбор глубины парсинга, количества страниц и других параметров

## Интеграция с Crawl4AI API

### Production URL
```
https://crawl4ai-dev--2wk9hbc.jollystone-8735f85a.westeurope.azurecontainerapps.io/api/v1
```

### Основные endpoints
- `POST /crawl/stream` - Стриминг кроулинг с SSE
- `POST /crawl/stop/{task_id}` - Остановка задачи
- `POST /crawl/pause/{task_id}` - Пауза задачи
- `POST /crawl/resume/{task_id}` - Возобновление задачи
- `GET /crawl/status/{task_id}` - Статус задачи
- `GET /crawl/active` - Активные задачи

## Архитектура системы

### Компоненты

1. **Frontend (Next.js)**
   - Новый компонент `WebsiteCrawler` 
   - Обновленный `DocumentUpload` с вкладками
   - Компонент управления задачами `CrawlTaskManager`

2. **Backend (FastAPI)**
   - Новый сервис `CrawlService` для интеграции с Crawl4AI
   - Обновленный `DocumentService` для обработки веб-контента
   - WebSocket/SSE endpointы для стриминга

3. **Интеграция**
   - HTTP клиент для Crawl4AI API
   - Обработка SSE для реального времени
   - Очередь задач для управления процессами

## Детальная спецификация

### 1. Frontend изменения

#### 1.1. Компонент WebsiteCrawler

**Файл:** `frontend/src/components/crawl/website-crawler.tsx`

```typescript
interface CrawlConfig {
  url: string;
  maxDepth: number;
  maxPages: number;
  browserType: 'chromium' | 'firefox' | 'webkit';
  waitUntil: 'networkidle' | 'domcontentloaded' | 'load';
  excludeExternalLinks: boolean;
  excludeExternalImages: boolean;
  wordCountThreshold: number;
  pageTimeout: number;
  namespace: string;
}

interface CrawlProgress {
  taskId: string;
  processed: number;
  total: number;
  currentUrl: string;
  status: 'running' | 'paused' | 'completed' | 'error';
  pages: CrawledPage[];
}
```

**Функциональность:**
- Форма настройки параметров кроулинга
- Валидация URL и параметров
- Показ прогресса в реальном времени
- Кнопки управления: старт/стоп/пауза/резюме
- Предпросмотр парсенного контента

#### 1.2. Обновленный DocumentUpload

**Файл:** `frontend/src/components/documents/document-upload.tsx`

```typescript
// Добавить вкладки для выбора типа загрузки
const UploadTabs = () => (
  <Tabs defaultValue="file" className="w-full">
    <TabsList className="grid w-full grid-cols-2">
      <TabsTrigger value="file">Загрузка документов</TabsTrigger>
      <TabsTrigger value="crawl">Парсинг сайта</TabsTrigger>
    </TabsList>
    <TabsContent value="file">
      <FileUploadComponent />
    </TabsContent>
    <TabsContent value="crawl">
      <WebsiteCrawler />
    </TabsContent>
  </Tabs>
);
```

#### 1.3. CrawlTaskManager

**Файл:** `frontend/src/components/crawl/task-manager.tsx`

```typescript
interface TaskInfo {
  taskId: string;
  url: string;
  status: string;
  startedAt: string;
  progress: number;
  totalPages: number;
  processedPages: number;
}
```

**Функциональность:**
- Список активных задач
- Управление задачами (остановка, пауза)
- История выполненных задач
- Детальная информация о задаче

### 2. Backend изменения

#### 2.1. Новый сервис CrawlService

**Файл:** `src/rag_crawl/services/crawl_service.py`

```python
from typing import Dict, List, Optional, AsyncGenerator
from pydantic import BaseModel, HttpUrl
from sqlalchemy.orm import Session
import httpx
import asyncio
from sse_starlette import ServerSentEvent

class CrawlConfig(BaseModel):
    url: HttpUrl
    max_depth: int = Field(default=3, ge=1, le=10)
    max_pages: int = Field(default=50, ge=1, le=5000)
    browser_type: str = Field(default="chromium", regex="^(chromium|firefox|webkit)$")
    wait_until: str = Field(default="networkidle", regex="^(networkidle|domcontentloaded|load)$")
    exclude_external_links: bool = Field(default=False)
    exclude_external_images: bool = Field(default=False)
    word_count_threshold: int = Field(default=5, ge=1)
    page_timeout: int = Field(default=60000, ge=10000, le=300000)
    namespace: str = Field(default="default", min_length=1, max_length=50)
    stream: bool = True

class CrawlService:
    def __init__(
        self, 
        db: Session, 
        document_service: DocumentService,
        crawl_api_base_url: str = "https://crawl4ai-dev--2wk9hbc.jollystone-8735f85a.westeurope.azurecontainerapps.io/api/v1"
    ):
        self._db = db
        self._document_service = document_service
        self._crawl_api_url = crawl_api_base_url
        self._active_tasks: Dict[str, asyncio.Task] = {}
        self._http_client = httpx.AsyncClient(timeout=300.0)

    async def start_crawl(self, config: CrawlConfig) -> AsyncGenerator[ServerSentEvent, None]:
        """Запускает кроулинг с стримингом результатов"""
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
                    raise HTTPException(status_code=response.status_code, detail=f"Crawl4AI API error: {error_data}")
                
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
                                await self._process_crawled_page(page_data, config.namespace)
                                crawl_logger.info(f"Страница обработана: {page_data.get('url', 'Unknown')}")
                                
                            elif data.get("type") == "progress":
                                crawl_logger.info(f"Прогресс: {data.get('processed', 0)}/{data.get('total', 0)} страниц")
                                
                            elif data.get("type") == "error":
                                crawl_logger.error(f"Ошибка кроулинга: {data.get('message', 'Unknown error')}")
                                
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

    async def _process_crawled_page(self, page_data: Dict, namespace: str) -> None:
        """Обрабатывает и сохраняет парсенную страницу"""
        try:
            # Создание объекта документа из веб-страницы
            document_data = {
                "filename": f"{page_data['url']}.html",
                "content": page_data.get("markdown", ""),
                "metadata": {
                    "source": "web_crawl",
                    "url": page_data["url"],
                    "title": page_data.get("title", ""),
                    "depth": page_data.get("depth", 0),
                    "crawled_at": page_data.get("crawled_at"),
                    "status_code": page_data.get("status_code"),
                    "processing_time": page_data.get("processing_time"),
                    "internal_links": page_data.get("internal_links", []),
                    "external_links": page_data.get("external_links", []),
                    "images": page_data.get("images", [])
                },
                "namespace": namespace
            }
            
            # Сохранение через DocumentService
            await self._document_service.create_document_from_content(document_data)
            
        except Exception as e:
            logger.error(f"Ошибка при обработке страницы {page_data.get('url')}: {e}")

    async def stop_crawl(self, task_id: str) -> Dict:
        """Останавливает задачу кроулинга"""
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
        """Приостанавливает задачу кроулинга"""
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
        """Возобновляет задачу кроулинга"""
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
        """Получает список активных задач"""
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
        """Получает статус конкретной задачи"""
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
        """Останавливает все активные задачи"""
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
```

#### 2.2. Обновленный DocumentService

**Файл:** `src/rag_crawl/services/document_service.py`

Добавить метод для создания документов из веб-контента:

```python
async def create_document_from_content(self, document_data: Dict) -> Document:
    """Создает документ из веб-контента"""
    try:
        # Создание записи в БД
        db_document = Document(
            filename=document_data["filename"],
            content_hash=self._generate_content_hash(document_data["content"]),
            metadata=document_data["metadata"],
            namespace=document_data["namespace"],
            is_active=True
        )
        
        self._db.add(db_document)
        self._db.flush()
        
        # Обработка и индексация контента
        chunks = await self._process_content_for_indexing(
            content=document_data["content"],
            document_id=db_document.id,
            metadata=document_data["metadata"]
        )
        
        # Сохранение в Qdrant
        await self._llama_service.store_document_chunks(
            chunks=chunks,
            namespace=document_data["namespace"]
        )
        
        self._db.commit()
        return db_document
        
    except Exception as e:
        self._db.rollback()
        logger.error(f"Ошибка при создании документа из веб-контента: {e}")
        raise DocumentProcessingError(document_id=0, reason=str(e))

async def _process_content_for_indexing(
    self, 
    content: str, 
    document_id: int, 
    metadata: Dict
) -> List[DocumentChunk]:
    """Разбивает веб-контент на чанки для индексации"""
    # Очистка HTML/Markdown контента
    clean_content = self._clean_web_content(content)
    
    # Разбивка на чанки
    chunks = self._split_into_chunks(
        content=clean_content,
        chunk_size=1024,
        chunk_overlap=200
    )
    
    document_chunks = []
    for i, chunk in enumerate(chunks):
        chunk_metadata = {
            **metadata,
            "chunk_index": i,
            "chunk_type": "web_content"
        }
        
        document_chunks.append(DocumentChunk(
            document_id=document_id,
            chunk_index=i,
            content=chunk,
            metadata=chunk_metadata
        ))
    
    return document_chunks

def _clean_web_content(self, content: str) -> str:
    """Очищает веб-контент от лишних элементов"""
    # Удаление лишних пробелов и переносов
    content = re.sub(r'\n\s*\n', '\n\n', content)
    content = re.sub(r'[ \t]+', ' ', content)
    
    # Удаление навигационных элементов
    content = re.sub(r'(Menu|Navigation|Footer|Header).*?(?=\n\n|\Z)', '', content, flags=re.IGNORECASE)
    
    return content.strip()
```

#### 2.3. Новые API endpoints

**Файл:** `src/rag_crawl/api/crawl.py`

```python
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sse_starlette import EventSourceResponse
from ..services.crawl_service import CrawlService, CrawlConfig
from ..database.connection import get_db

router = APIRouter(prefix="/api/crawl", tags=["crawl"])

@router.post("/start")
async def start_crawl(
    config: CrawlConfig,
    crawl_service: CrawlService = Depends(get_crawl_service)
):
    """Запускает кроулинг с Server-Sent Events"""
    try:
        return EventSourceResponse(
            crawl_service.start_crawl(config),
            media_type="text/event-stream"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stop/{task_id}")
async def stop_crawl(
    task_id: str,
    crawl_service: CrawlService = Depends(get_crawl_service)
):
    """Останавливает задачу кроулинга"""
    try:
        result = await crawl_service.stop_crawl(task_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/pause/{task_id}")
async def pause_crawl(
    task_id: str,
    crawl_service: CrawlService = Depends(get_crawl_service)
):
    """Приостанавливает задачу кроулинга"""
    try:
        result = await crawl_service.pause_crawl(task_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/resume/{task_id}")
async def resume_crawl(
    task_id: str,
    crawl_service: CrawlService = Depends(get_crawl_service)
):
    """Возобновляет задачу кроулинга"""
    try:
        result = await crawl_service.resume_crawl(task_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/stop-all")
async def stop_all_crawls(
    crawl_service: CrawlService = Depends(get_crawl_service)
):
    """Останавливает все активные задачи"""
    try:
        result = await crawl_service.stop_all_crawls()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/active")
async def get_active_tasks(
    crawl_service: CrawlService = Depends(get_crawl_service)
):
    """Получает список активных задач"""
    try:
        return await crawl_service.get_active_tasks()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{task_id}")
async def get_task_status(
    task_id: str,
    crawl_service: CrawlService = Depends(get_crawl_service)
):
    """Получает статус задачи"""
    try:
        return await crawl_service.get_task_status(task_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def get_crawl_service(db: Session = Depends(get_db)) -> CrawlService:
    """Dependency injection для CrawlService"""
    from ..services.document_service import DocumentService
    from ..services.llama_service import LlamaService
    
    document_service = DocumentService(db, LlamaService())
    return CrawlService(db, document_service)
```

### 3. Модели данных

#### 3.1. Обновление моделей БД

**Файл:** `src/rag_crawl/database/models.py`

Добавить новые поля в модель Document:

```python
class Document(Base):
    __tablename__ = "documents"
    
    # ... существующие поля ...
    
    # Новые поля для веб-контента
    source_type = Column(String, default="file")  # "file" или "web"
    source_url = Column(String, nullable=True)  # URL источника
    crawl_depth = Column(Integer, nullable=True)  # Глубина кроулинга
    crawl_metadata = Column(JSON, nullable=True)  # Метаданные кроулинга
    
    # Индексы для оптимизации поиска
    __table_args__ = (
        Index('idx_source_type', source_type),
        Index('idx_source_url', source_url),
        Index('idx_namespace_source', namespace, source_type),
    )
```

#### 3.2. Pydantic модели

**Файл:** `src/rag_crawl/api/models.py`

```python
class CrawlConfigRequest(BaseModel):
    url: HttpUrl
    max_depth: int = Field(default=3, ge=1, le=10)
    max_pages: int = Field(default=50, ge=1, le=5000)
    browser_type: str = Field(default="chromium", regex="^(chromium|firefox|webkit)$")
    wait_until: str = Field(default="networkidle", regex="^(networkidle|domcontentloaded|load)$")
    exclude_external_links: bool = Field(default=False)
    namespace: str = Field(default="default", min_length=1, max_length=50)
    page_timeout: int = Field(default=60000, ge=10000, le=300000)
    word_count_threshold: int = Field(default=5, ge=1)

class CrawlProgressEvent(BaseModel):
    type: str  # "crawl_started", "page_complete", "progress", "crawl_complete", "error"
    task_id: str
    message: Optional[str] = None
    progress: Optional[Dict] = None
    page: Optional[Dict] = None
    timestamp: str

class TaskInfo(BaseModel):
    task_id: str
    url: str
    status: str
    started_at: str
    progress: Optional[Dict] = None
    
class ActiveTasksResponse(BaseModel):
    active_tasks: List[str]
    task_details: List[TaskInfo]
    count: int
```

### 4. Настройка конфигурации

#### 4.1. Добавление настроек

**Файл:** `src/rag_crawl/config.py`

```python
class Settings(BaseSettings):
    # ... существующие настройки ...
    
    # Crawl4AI API настройки
    crawl4ai_api_url: str = Field(
        default="https://crawl4ai-dev--2wk9hbc.jollystone-8735f85a.westeurope.azurecontainerapps.io/api/v1",
        env="CRAWL4AI_API_URL"
    )
    crawl4ai_timeout: int = Field(default=300, env="CRAWL4AI_TIMEOUT")
    
    # Настройки кроулинга
    max_concurrent_crawls: int = Field(default=3, env="MAX_CONCURRENT_CRAWLS")
    default_crawl_depth: int = Field(default=3, env="DEFAULT_CRAWL_DEPTH")
    default_max_pages: int = Field(default=50, env="DEFAULT_MAX_PAGES")
    
    # Настройки обработки веб-контента
    web_content_chunk_size: int = Field(default=1024, env="WEB_CONTENT_CHUNK_SIZE")
    web_content_chunk_overlap: int = Field(default=200, env="WEB_CONTENT_CHUNK_OVERLAP")
```

### 5. Frontend интеграция

#### 5.1. Hooks для управления кроулингом

**Файл:** `frontend/src/hooks/use-crawl.ts`

```typescript
import { useState, useEffect } from 'react';

interface CrawlConfig {
  url: string;
  maxDepth: number;
  maxPages: number;
  browserType: string;
  waitUntil: string;
  excludeExternalLinks: boolean;
  namespace: string;
}

interface CrawlProgress {
  taskId: string;
  processed: number;
  total: number;
  currentUrl: string;
  status: string;
  pages: any[];
}

export const useCrawl = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [progress, setProgress] = useState<CrawlProgress | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeTasks, setActiveTasks] = useState<string[]>([]);

  const startCrawl = async (config: CrawlConfig) => {
    setIsLoading(true);
    setError(null);
    setProgress(null);

    try {
      const eventSource = new EventSource('/api/crawl/start', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(config),
      });

      eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        switch (data.type) {
          case 'crawl_started':
            setProgress(prev => ({ ...prev, taskId: data.task_id, status: 'running' }));
            break;
          case 'progress':
            setProgress(prev => ({ 
              ...prev, 
              processed: data.processed, 
              total: data.total,
              currentUrl: data.current_url 
            }));
            break;
          case 'page_complete':
            setProgress(prev => ({ 
              ...prev, 
              pages: [...(prev?.pages || []), data.page] 
            }));
            break;
          case 'crawl_complete':
            setIsLoading(false);
            setProgress(prev => ({ ...prev, status: 'completed' }));
            eventSource.close();
            break;
          case 'error':
            setError(data.message);
            setIsLoading(false);
            eventSource.close();
            break;
        }
      };

      eventSource.onerror = () => {
        setError('Ошибка соединения с сервером');
        setIsLoading(false);
        eventSource.close();
      };

    } catch (err) {
      setError('Ошибка при запуске кроулинга');
      setIsLoading(false);
    }
  };

  const stopCrawl = async (taskId: string) => {
    try {
      const response = await fetch(`/api/crawl/stop/${taskId}`, {
        method: 'POST',
      });
      
      if (!response.ok) {
        throw new Error('Не удалось остановить задачу');
      }
      
      setProgress(prev => ({ ...prev, status: 'stopped' }));
      setIsLoading(false);
    } catch (err) {
      setError('Ошибка при остановке кроулинга');
    }
  };

  const pauseCrawl = async (taskId: string) => {
    try {
      const response = await fetch(`/api/crawl/pause/${taskId}`, {
        method: 'POST',
      });
      
      if (!response.ok) {
        throw new Error('Не удалось приостановить задачу');
      }
      
      setProgress(prev => ({ ...prev, status: 'paused' }));
    } catch (err) {
      setError('Ошибка при приостановке кроулинга');
    }
  };

  const resumeCrawl = async (taskId: string) => {
    try {
      const response = await fetch(`/api/crawl/resume/${taskId}`, {
        method: 'POST',
      });
      
      if (!response.ok) {
        throw new Error('Не удалось возобновить задачу');
      }
      
      setProgress(prev => ({ ...prev, status: 'running' }));
    } catch (err) {
      setError('Ошибка при возобновлении кроулинга');
    }
  };

  const stopAllCrawls = async () => {
    try {
      const response = await fetch('/api/crawl/stop-all', {
        method: 'DELETE',
      });
      
      if (!response.ok) {
        throw new Error('Не удалось остановить все задачи');
      }
      
      setActiveTasks([]);
      setIsLoading(false);
    } catch (err) {
      setError('Ошибка при остановке всех задач');
    }
  };

  const getActiveTasks = async () => {
    try {
      const response = await fetch('/api/crawl/active');
      const data = await response.json();
      setActiveTasks(data.active_tasks);
    } catch (err) {
      console.error('Ошибка при получении активных задач:', err);
    }
  };

  useEffect(() => {
    getActiveTasks();
    const interval = setInterval(getActiveTasks, 5000);
    return () => clearInterval(interval);
  }, []);

  return {
    isLoading,
    progress,
    error,
    activeTasks,
    startCrawl,
    stopCrawl,
    pauseCrawl,
    resumeCrawl,
    stopAllCrawls,
    getActiveTasks,
  };
};
```

### 6. Обработка ошибок и мониторинг

#### 6.1. Логирование

```python
import logging
from datetime import datetime

# Настройка специализированного логгера для кроулинга
crawl_logger = logging.getLogger("rag_crawl.crawl")
crawl_logger.setLevel(logging.INFO)

# Форматтер для структурированного логирования
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Обработчик для файла логов кроулинга
file_handler = logging.FileHandler('logs/crawl.log')
file_handler.setFormatter(formatter)
crawl_logger.addHandler(file_handler)

# Логирование в CrawlService
class CrawlService:
    async def start_crawl(self, config: CrawlConfig) -> AsyncGenerator[ServerSentEvent, None]:
        crawl_logger.info(f"Начат кроулинг: {config.url}, глубина: {config.max_depth}")
        
        try:
            # ... логика кроулинга ...
            crawl_logger.info(f"Кроулинг завершен успешно: {config.url}")
        except Exception as e:
            crawl_logger.error(f"Ошибка кроулинга {config.url}: {str(e)}")
            raise
```

#### 6.2. Метрики и мониторинг

```python
from prometheus_client import Counter, Histogram, Gauge

# Метрики для мониторинга
crawl_requests_total = Counter('crawl_requests_total', 'Total crawl requests')
crawl_pages_processed = Counter('crawl_pages_processed_total', 'Total pages processed')
crawl_duration_seconds = Histogram('crawl_duration_seconds', 'Crawl duration')
active_crawl_tasks = Gauge('active_crawl_tasks', 'Number of active crawl tasks')

class CrawlService:
    async def start_crawl(self, config: CrawlConfig) -> AsyncGenerator[ServerSentEvent, None]:
        crawl_requests_total.inc()
        active_crawl_tasks.inc()
        
        start_time = time.time()
        
        try:
            # ... логика кроулинга ...
            
            # Обновление метрик при обработке страницы
            crawl_pages_processed.inc()
            
        finally:
            active_crawl_tasks.dec()
            crawl_duration_seconds.observe(time.time() - start_time)
```

### 7. Тестирование

#### 7.1. Unit тесты

**Файл:** `tests/unit/test_crawl_service.py`

```python
import pytest
from unittest.mock import AsyncMock, patch
from src.rag_crawl.services.crawl_service import CrawlService, CrawlConfig

@pytest.fixture
def mock_crawl_service():
    with patch('src.rag_crawl.services.crawl_service.httpx.AsyncClient') as mock_client:
        yield mock_client

@pytest.mark.asyncio
async def test_start_crawl_success(mock_crawl_service):
    # Настройка мока
    mock_response = AsyncMock()
    mock_response.aiter_lines.return_value = [
        'data: {"type": "crawl_started", "task_id": "test-123"}',
        'data: {"type": "page_complete", "page": {"url": "https://example.com", "title": "Test"}}',
        'data: {"type": "crawl_complete", "result": {"total_pages": 1}}'
    ]
    
    mock_crawl_service.return_value.stream.return_value.__aenter__.return_value = mock_response
    
    # Создание сервиса
    service = CrawlService(db=AsyncMock(), document_service=AsyncMock())
    
    # Настройка конфигурации
    config = CrawlConfig(
        url="https://example.com",
        max_depth=1,
        max_pages=5
    )
    
    # Выполнение теста
    events = []
    async for event in service.start_crawl(config):
        events.append(event)
    
    # Проверка результатов
    assert len(events) == 3
    assert 'crawl_started' in events[0].data
    assert 'page_complete' in events[1].data
    assert 'crawl_complete' in events[2].data
```

#### 7.2. Integration тесты

**Файл:** `tests/integration/test_crawl_integration.py`

```python
import pytest
from fastapi.testclient import TestClient
from src.rag_crawl.main import app

@pytest.fixture
def client():
    return TestClient(app)

def test_crawl_endpoint_integration(client):
    # Тест полной интеграции с мокованным Crawl4AI API
    crawl_config = {
        "url": "https://example.com",
        "max_depth": 1,
        "max_pages": 5,
        "namespace": "test"
    }
    
    with patch('src.rag_crawl.services.crawl_service.httpx.AsyncClient') as mock_client:
        # Настройка мока для успешного ответа
        mock_response = AsyncMock()
        mock_response.aiter_lines.return_value = [
            'data: {"type": "crawl_started", "task_id": "test-123"}',
            'data: {"type": "crawl_complete", "result": {"total_pages": 1}}'
        ]
        mock_client.return_value.stream.return_value.__aenter__.return_value = mock_response
        
        # Выполнение запроса
        response = client.post("/api/crawl/start", json=crawl_config)
        
        # Проверка ответа
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
```

### 8. Развертывание и конфигурация

#### 8.1. Docker конфигурация

**Файл:** `docker-compose.yml`

```yaml
version: '3.8'

services:
  rag-crawl:
    build: .
    ports:
      - "8000:8000"
    environment:
      - CRAWL4AI_API_URL=https://crawl4ai-dev--2wk9hbc.jollystone-8735f85a.westeurope.azurecontainerapps.io/api/v1
      - CRAWL4AI_TIMEOUT=300
      - MAX_CONCURRENT_CRAWLS=3
      - DEFAULT_CRAWL_DEPTH=3
      - DEFAULT_MAX_PAGES=50
    depends_on:
      - postgres
      - qdrant
    volumes:
      - ./logs:/app/logs

  # ... остальные сервисы ...
```

#### 8.2. Переменные окружения

**Файл:** `.env`

```env
# Crawl4AI API настройки
CRAWL4AI_API_URL=https://crawl4ai-dev--2wk9hbc.jollystone-8735f85a.westeurope.azurecontainerapps.io/api/v1
CRAWL4AI_TIMEOUT=300

# Настройки кроулинга
MAX_CONCURRENT_CRAWLS=3
DEFAULT_CRAWL_DEPTH=3
DEFAULT_MAX_PAGES=50

# Настройки обработки контента
WEB_CONTENT_CHUNK_SIZE=1024
WEB_CONTENT_CHUNK_OVERLAP=200
```

### 9. Безопасность

#### 9.1. Валидация URL

```python
from urllib.parse import urlparse
import re

class URLValidator:
    ALLOWED_SCHEMES = ['http', 'https']
    BLOCKED_DOMAINS = ['localhost', '127.0.0.1', '0.0.0.0']
    BLOCKED_PORTS = [22, 23, 25, 53, 80, 135, 139, 445, 993, 995]
    
    @classmethod
    def validate_url(cls, url: str) -> bool:
        """Валидирует URL для безопасности"""
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
            if parsed.port in cls.BLOCKED_PORTS:
                return False
            
            return True
            
        except Exception:
            return False
    
    @staticmethod
    def _is_private_ip(hostname: str) -> bool:
        """Проверяет, является ли IP приватным"""
        try:
            import ipaddress
            ip = ipaddress.ip_address(hostname)
            return ip.is_private
        except Exception:
            return False
```

#### 9.2. Ограничения и защита

```python
from fastapi import HTTPException
from functools import wraps
import time

class CrawlLimiter:
    def __init__(self, max_requests_per_minute: int = 10):
        self.max_requests = max_requests_per_minute
        self.requests = {}
    
    def check_rate_limit(self, client_ip: str) -> bool:
        """Проверяет лимит запросов для IP"""
        current_time = time.time()
        
        if client_ip not in self.requests:
            self.requests[client_ip] = []
        
        # Удаление старых запросов
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if current_time - req_time < 60  # За последнюю минуту
        ]
        
        if len(self.requests[client_ip]) >= self.max_requests:
            return False
        
        self.requests[client_ip].append(current_time)
        return True

# Применение в API
@router.post("/start")
async def start_crawl(
    config: CrawlConfig,
    request: Request,
    crawl_service: CrawlService = Depends(get_crawl_service)
):
    client_ip = request.client.host
    
    if not rate_limiter.check_rate_limit(client_ip):
        raise HTTPException(
            status_code=429, 
            detail="Превышен лимит запросов. Попробуйте позже."
        )
    
    if not URLValidator.validate_url(str(config.url)):
        raise HTTPException(
            status_code=400, 
            detail="Недопустимый URL для кроулинга"
        )
    
    # ... остальная логика ...
```

### 10. План развертывания

#### 10.1. Этапы развертывания

1. **Этап 1: Backend API**
   - Создание CrawlService
   - Добавление API endpoints
   - Тестирование интеграции с Crawl4AI

2. **Этап 2: Frontend компоненты**
   - Создание WebsiteCrawler компонента
   - Интеграция с существующим интерфейсом
   - Реализация управления задачами

3. **Этап 3: Стриминг и Real-time**
   - Настройка SSE для стриминга
   - Реализация прогресс-бара
   - Управление задачами

4. **Этап 4: Оптимизация и мониторинг**
   - Добавление логирования
   - Настройка метрик
   - Оптимизация производительности

#### 10.2. Критерии готовности

- [ ] Все unit тесты проходят
- [ ] Integration тесты с Crawl4AI API работают
- [ ] Frontend корректно отображает прогресс
- [ ] Возможность остановки задач работает
- [ ] Парсенные данные корректно сохраняются в Qdrant
- [ ] Логирование и мониторинг настроены
- [ ] Документация обновлена

### 11. Возможные проблемы и решения

#### 11.1. Проблемы с производительностью

**Проблема:** Медленная обработка больших сайтов
**Решение:** 
- Параллельная обработка страниц
- Оптимизация размера чанков
- Кэширование результатов

#### 11.2. Проблемы с памятью

**Проблема:** Переполнение памяти при обработке больших документов
**Решение:**
- Потоковая обработка контента
- Ограничение размера обрабатываемых страниц
- Периодическая очистка кэша

#### 11.3. Проблемы с сетью

**Проблема:** Таймауты и нестабильные соединения
**Решение:**
- Retry механизмы
- Настройка таймаутов
- Graceful handling сетевых ошибок

### 12. Будущие улучшения

1. **Планировщик задач** - Возможность планирования регулярного кроулинга
2. **Интеллектуальная фильтрация** - Автоматическое определение релевантного контента
3. **Дедупликация** - Обнаружение и удаление дублированного контента
4. **Аналитика** - Детальная статистика по кроулингу
5. **Webhook уведомления** - Уведомления о завершении задач

## Примеры использования API

### Простой сайт
```bash
curl -X POST "http://localhost:8000/api/crawl/start" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "maxDepth": 2,
    "maxPages": 10,
    "namespace": "example"
  }'
```

### JavaScript SPA с расширенными настройками
```bash
curl -X POST "http://localhost:8000/api/crawl/start" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://spa.example.com",
    "maxDepth": 3,
    "maxPages": 50,
    "browserType": "chromium",
    "waitUntil": "networkidle",
    "pageTimeout": 60000,
    "excludeExternalLinks": true,
    "excludeExternalImages": true,
    "wordCountThreshold": 10,
    "namespace": "spa_docs"
  }'
```

### Управление задачами
```bash
# Получение активных задач
curl -X GET "http://localhost:8000/api/crawl/active"

# Приостановка задачи
curl -X POST "http://localhost:8000/api/crawl/pause/{task_id}"

# Возобновление задачи
curl -X POST "http://localhost:8000/api/crawl/resume/{task_id}"

# Остановка всех задач
curl -X DELETE "http://localhost:8000/api/crawl/stop-all"
```

## Рекомендации по оптимизации

### Настройки производительности
- Для статических сайтов: `waitUntil: "domcontentloaded"`
- Для SPA: `waitUntil: "networkidle"`
- Для быстрого парсинга: `excludeExternalLinks: true`
- Для экономии ресурсов: `excludeExternalImages: true`

### Настройки качества контента
- Минимальный размер страницы: `wordCountThreshold: 10`
- Таймаут для медленных сайтов: `pageTimeout: 90000`
- Глубина для блогов/документации: `maxDepth: 3-5`
- Глубина для новостных сайтов: `maxDepth: 1-2`

### Мониторинг и отладка
- Используйте endpoint `/crawl/active` для мониторинга
- Логи доступны в `logs/crawl.log`
- Метрики Prometheus для production мониторинга

## Интеграция с существующими компонентами

### Обновление главной страницы
```typescript
// src/app/page.tsx
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { DocumentUpload } from '@/components/documents/document-upload';
import { WebsiteCrawler } from '@/components/crawl/website-crawler';

export default function Home() {
  return (
    <div className="container mx-auto p-4">
      <Tabs defaultValue="chat" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="chat">Чат</TabsTrigger>
          <TabsTrigger value="documents">Документы</TabsTrigger>
          <TabsTrigger value="crawl">Парсинг сайтов</TabsTrigger>
        </TabsList>
        
        <TabsContent value="chat">
          <ChatInterface />
        </TabsContent>
        
        <TabsContent value="documents">
          <DocumentUpload />
        </TabsContent>
        
        <TabsContent value="crawl">
          <WebsiteCrawler />
        </TabsContent>
      </Tabs>
    </div>
  );
}
```

### Обновление main.py
```python
# src/rag_crawl/main.py
from .api import crawl

app = FastAPI(title="RAG Crawl API", version="1.0.0")

# Добавление роутеров
app.include_router(crawl.router)
# ... остальные роутеры
```

## Заключение

Данная спецификация описывает полную интеграцию функции парсинга сайтов в существующую RAG систему. Решение обеспечивает:

- **Удобный пользовательский интерфейс** с вкладками и контролем прогресса
- **Реальное время обработки** с Server-Sent Events
- **Надежную интеграцию** с Crawl4AI микросервисом
- **Автоматическую индексацию** в Qdrant с богатыми метаданными
- **Масштабируемость** и производительность
- **Безопасность** с валидацией URL и ограничениями
- **Мониторинг** с логированием и метриками

Реализация позволит значительно расширить возможности RAG системы, добавив автоматическое извлечение знаний из веб-источников с полным контролем процесса и высокой производительностью. 