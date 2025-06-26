"""
Основной сервис для работы с LlamaIndex.
Использует встроенные компоненты LlamaIndex для RAG функциональности.
"""

import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import uuid

from llama_index.core import VectorStoreIndex, Document, StorageContext, Settings
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.azure_openai import AzureOpenAIEmbedding
from llama_index.llms.azure_openai import AzureOpenAI
from llama_index.vector_stores.qdrant import QdrantVectorStore
import qdrant_client
from fastapi import UploadFile
from sqlalchemy.orm import Session

from ..config import settings
from ..database.models import Document as DBDocument, ChatHistory, DocumentChunk
from ..utils.text_processing import extract_text_from_file, clean_text, sanitize_filename

logger = logging.getLogger(__name__)


class LlamaIndexService:
    """
    Сервис для работы с LlamaIndex.
    Использует встроенные возможности для максимальной эффективности.
    """

    def __init__(self, db: Session):
        """Инициализация сервиса."""
        self.db = db
        self._vector_store = None
        self._indices = {}  # Кэш индексов по namespace
        self._chat_engines = {}  # Кэш chat engines по namespace
        self._setup_llama_index()
        
    def _setup_llama_index(self):
        """Настройка глобальных параметров LlamaIndex."""
        # Настройка LLM - используем AzureOpenAI
        self.llm = AzureOpenAI(
            model=settings.azure_openai_chat_model,  # Используем переменную из environment
            deployment_name=settings.azure_openai_chat_deployment,
            api_key=settings.azure_openai_api_key,
            azure_endpoint=settings.azure_openai_endpoint,
            api_version=settings.azure_openai_api_version,
            temperature=0.1,
        )
        
        # Настройка Embedding модели
        self.embed_model = AzureOpenAIEmbedding(
            model=settings.azure_openai_embedding_model,  # Используем переменную из environment
            deployment_name=settings.azure_openai_embedding_deployment,
            api_key=settings.azure_openai_api_key,
            azure_endpoint=settings.azure_openai_endpoint,
            api_version=settings.azure_openai_api_version,
        )
        
        # Настройка глобальных параметров через Settings
        Settings.llm = self.llm
        Settings.embed_model = self.embed_model
        Settings.node_parser = SentenceSplitter(
            chunk_size=settings.max_chunk_size,
            chunk_overlap=settings.chunk_overlap
        )
        
        logger.info("LlamaIndex настроен с Azure OpenAI")
    
    def _detect_document_category(self, title: str, source_type: str, content: str) -> str:
        """Автоматически определяет категорию документа по содержимому."""
        title_lower = title.lower()
        content_lower = content.lower()
        
        # Определяем по расширению файла
        if source_type in ['md', 'markdown']:
            return "documentation"
        elif source_type in ['pdf']:
            return "document"
        elif source_type in ['txt']:
            return "text"
        elif source_type in ['html', 'htm']:
            return "web_page"
        elif source_type in ['docx', 'doc']:
            return "office_document"
        
        # Определяем по ключевым словам в заголовке
        if any(word in title_lower for word in ['readme', 'документация', 'инструкция', 'guide']):
            return "documentation"
        elif any(word in title_lower for word in ['api', 'reference', 'spec']):
            return "reference"
        elif any(word in title_lower for word in ['tutorial', 'урок', 'обучение']):
            return "tutorial"
        elif any(word in title_lower for word in ['новости', 'news', 'статья', 'article']):
            return "article"
        elif any(word in title_lower for word in ['отчет', 'report', 'анализ']):
            return "report"
        
        # Определяем по содержимому
        if len(content) < 500:
            return "snippet"
        elif '```' in content or 'def ' in content or 'function ' in content:
            return "code_documentation"
        elif content.count('\n#') > 3:  # много заголовков
            return "structured_document"
        
        return "general"

    def _get_vector_store(self) -> Any:
        """Получение векторного хранилища - ВРЕМЕННО используем in-memory хранилище."""
        try:
            # ВРЕМЕННОЕ РЕШЕНИЕ: используем in-memory хранилище для тестирования
            logger.warning("Используем временное in-memory векторное хранилище для отладки")
            # Возвращаем None - VectorStoreIndex создаст автоматически SimpleVectorStore
            return None
            
        except Exception as e:
            logger.error(f"Критическая ошибка создания временного vector store: {e}")
            raise

    def _get_vector_store_lazy(self) -> Any:
        """Ленивая инициализация vector store."""
        if self._vector_store is None:
            self._vector_store = self._get_vector_store()
        return self._vector_store

    def _get_index(self, namespace: str) -> VectorStoreIndex:
        """Получение или создание индекса для namespace."""
        if namespace not in self._indices:
            vector_store = self._get_vector_store_lazy()
            
            if vector_store is None:
                # Создаем in-memory индекс и загружаем существующие документы
                logger.warning("Используем временное in-memory векторное хранилище для отладки")
                
                # Получаем все chunks из базы для данного namespace через join с documents
                chunks = self.db.query(DocumentChunk).join(DBDocument).filter(
                    DBDocument.namespace == namespace,
                    DBDocument.is_active == True
                ).all()
                
                llama_docs = []
                for chunk in chunks:
                    # Восстанавливаем LlamaIndex документы из чанков
                    llama_doc = Document(
                        text=chunk.content,
                        metadata={
                            "title": chunk.document.title,
                            "source_type": chunk.document.source_type,
                            "namespace": chunk.document.namespace,
                            "document_id": chunk.document.id,
                            "chunk_index": chunk.chunk_index,
                            "vector_id": chunk.vector_id,
                            **(chunk.document.metadata_json or {})
                        }
                    )
                    llama_docs.append(llama_doc)
                
                self._indices[namespace] = VectorStoreIndex.from_documents(llama_docs)
                logger.info(f"Создан in-memory индекс для namespace: {namespace} с {len(llama_docs)} чанками")
            else:
                # Создаем storage context с фильтром по namespace
                storage_context = StorageContext.from_defaults(
                    vector_store=vector_store
                )
                
                # Создаем индекс из существующего vector store
                self._indices[namespace] = VectorStoreIndex.from_vector_store(
                    vector_store=vector_store,
                    storage_context=storage_context
                )
                logger.info(f"Создан индекс для namespace: {namespace}")
            
        return self._indices[namespace]

    def _get_chat_engine(self, namespace: str, session_id: Optional[str] = None):
        """Получение chat engine для namespace."""
        cache_key = f"{namespace}:{session_id or 'default'}"
        
        if cache_key not in self._chat_engines:
            index = self._get_index(namespace)
            
            # Создаем chat engine с встроенной функциональностью
            chat_engine = index.as_chat_engine(
                chat_mode="context",
                verbose=True
            )
            
            self._chat_engines[cache_key] = chat_engine
            
        return self._chat_engines[cache_key]

    async def upload_document(
        self, 
        file: UploadFile, 
        namespace: str = "default"
    ) -> DBDocument:
        """
        Загрузка и обработка документа через встроенный IngestionPipeline.
        """
        try:
            # Извлечение текста из файла
            text_content = await extract_text_from_file(file)
            cleaned_text = clean_text(text_content)
            
            if not cleaned_text.strip():
                raise ValueError("Файл не содержит текста для обработки")
            
            # Создание документа LlamaIndex с богатыми метаданными
            title = sanitize_filename(file.filename or "unknown")
            source_type = Path(file.filename or "").suffix.lower()[1:] or "unknown"
            
            # Автоматически определяем категорию документа
            document_category = self._detect_document_category(title, source_type, cleaned_text)
            
            # Богатые метаданные для умной фильтрации
            rich_metadata = {
                "title": title,
                "source_type": source_type,
                "category": document_category,
                "namespace": namespace,
                "filename": file.filename,
                "content_length": len(cleaned_text),
                "content_preview": cleaned_text[:200] + "..." if len(cleaned_text) > 200 else cleaned_text,
                "upload_source": "file_upload",  # можно будет добавить web_scraping и др.
                "language": "ru",  # можно добавить определение языка
            }
            
            llama_doc = Document(
                text=cleaned_text,
                metadata=rich_metadata
            )
            
            # Создание индекса и добавление документа
            index = self._get_index(namespace)
            index.insert(llama_doc)
            
            # Подсчет чанков (приблизительно)
            chunk_count = max(1, len(cleaned_text) // settings.max_chunk_size)
            
            # Сохранение метаданных в БД
            db_document = DBDocument(
                title=title,
                source_type=source_type,
                namespace=namespace,
                source_url=file.filename,
                content_hash=str(hash(cleaned_text)),
                vector_id=str(uuid.uuid4()),
                chunks_count=chunk_count,
                metadata_json=rich_metadata  # Сохраняем все богатые метаданные
            )
            
            self.db.add(db_document)
            self.db.commit()
            self.db.refresh(db_document)
            
            # Создаем чанки в базе данных для последующего восстановления индекса
            # Используем тот же текст, что и в LlamaIndex документе
            chunk = DocumentChunk(
                document_id=db_document.id,
                chunk_index=0,
                content=cleaned_text,
                vector_id=str(uuid.uuid4()),
                metadata_json=rich_metadata
            )
            self.db.add(chunk)
            self.db.commit()
            
            # Очистка кэша для namespace
            if namespace in self._indices:
                del self._indices[namespace]
            
            # Очистка кэша chat engines для этого namespace
            keys_to_remove = [k for k in self._chat_engines.keys() if k.startswith(f"{namespace}:")]
            for key in keys_to_remove:
                del self._chat_engines[key]
            
            logger.info(f"Документ '{title}' загружен в namespace '{namespace}', создано {chunk_count} чанков")
            
            return db_document
            
        except Exception as e:
            logger.error(f"Ошибка загрузки документа: {e}")
            self.db.rollback()
            raise

    async def chat(
        self, 
        message: str, 
        namespace: str = "default",
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Чат с документами через встроенный ChatEngine.
        """
        try:
            chat_engine = self._get_chat_engine(namespace, session_id)
            
            # Получение ответа через встроенный chat engine
            response = chat_engine.chat(message)
            
            # Извлечение источников
            sources = []
            if hasattr(response, 'source_nodes') and response.source_nodes:
                for node in response.source_nodes:
                    if hasattr(node, 'metadata'):
                        sources.append({
                            "document_title": node.metadata.get("title", "Unknown"),
                            "source_type": node.metadata.get("source_type", "unknown"),
                            "score": getattr(node, 'score', 0.0)
                        })
            
            # Сохранение в историю чатов
            chat_record = ChatHistory(
                session_id=session_id or "default",
                namespace=namespace,
                user_message=message,
                assistant_message=str(response),
                sources_used=sources
            )
            
            self.db.add(chat_record)
            self.db.commit()
            
            return {
                "response": str(response),
                "sources": sources,
                "session_id": session_id
            }
            
        except Exception as e:
            logger.error(f"Ошибка чата: {e}")
            raise

    async def query(
        self, 
        question: str, 
        namespace: str = "default"
    ) -> Dict[str, Any]:
        """
        Простой запрос без сохранения контекста через QueryEngine.
        """
        try:
            index = self._get_index(namespace)
            
            # Создание query engine
            query_engine = index.as_query_engine(
                similarity_top_k=settings.max_retrieval_results
            )
            
            # Выполнение запроса
            response = query_engine.query(question)
            
            # Извлечение источников
            sources = []
            if hasattr(response, 'source_nodes') and response.source_nodes:
                for node in response.source_nodes:
                    if hasattr(node, 'metadata'):
                        sources.append({
                            "document_title": node.metadata.get("title", "Unknown"),
                            "source_type": node.metadata.get("source_type", "unknown"),
                            "score": getattr(node, 'score', 0.0)
                        })
            
            return {
                "response": str(response),
                "sources": sources
            }
            
        except Exception as e:
            logger.error(f"Ошибка запроса: {e}")
            raise

    async def get_documents(
        self, 
        namespace: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Получение списка документов."""
        try:
            query = self.db.query(DBDocument).filter(DBDocument.is_active == True)
            
            if namespace:
                query = query.filter(DBDocument.namespace == namespace)
            
            documents = query.all()
            
            return [
                {
                    "id": doc.id,
                    "title": doc.title,
                    "source_type": doc.source_type,
                    "namespace": doc.namespace,
                    "created_at": doc.created_at.isoformat(),
                    "chunks_count": doc.chunks_count,
                    "metadata": doc.metadata_json or {},
                    "size": len(str(doc.metadata_json or {})),
                }
                for doc in documents
            ]
            
        except Exception as e:
            logger.warning(f"Ошибка получения документов: {e}")
            # Возвращаем пустой список при ошибке, а не поднимаем исключение
            return []

    async def delete_document(self, document_id: int) -> bool:
        """Удаление документа."""
        try:
            document = self.db.query(DBDocument).filter(
                DBDocument.id == document_id,
                DBDocument.is_active == True
            ).first()
            
            if not document:
                return False
            
            # Мягкое удаление
            document.is_active = False
            self.db.commit()
            
            # Очистка кэшей
            namespace = document.namespace
            if namespace in self._indices:
                del self._indices[namespace]
            
            keys_to_remove = [k for k in self._chat_engines.keys() if k.startswith(f"{namespace}:")]
            for key in keys_to_remove:
                del self._chat_engines[key]
            
            logger.info(f"Документ {document_id} удален")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка удаления документа: {e}")
            self.db.rollback()
            raise

    async def get_chat_history(
        self,
        session_id: Optional[str] = None,
        namespace: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Получение истории чатов."""
        try:
            query = self.db.query(ChatHistory)
            
            if session_id:
                query = query.filter(ChatHistory.session_id == session_id)
            
            if namespace:
                query = query.filter(ChatHistory.namespace == namespace)
            
            history = query.order_by(
                ChatHistory.created_at.desc()
            ).limit(limit).all()
            
            return [
                {
                    "id": record.id,
                    "session_id": record.session_id,
                    "namespace": record.namespace,
                    "user_message": record.user_message,
                    "assistant_message": record.assistant_message,
                    "created_at": record.created_at.isoformat()
                }
                for record in history
            ]
            
        except Exception as e:
            logger.error(f"Ошибка получения истории: {e}")
            raise

    async def resync_namespace(self, namespace: str) -> Dict[str, Any]:
        """Ресинхронизация документов в namespace."""
        try:
            # Очистка кэшей
            if namespace in self._indices:
                del self._indices[namespace]
            
            keys_to_remove = [k for k in self._chat_engines.keys() if k.startswith(f"{namespace}:")]
            for key in keys_to_remove:
                del self._chat_engines[key]
            
            # Получение количества документов
            doc_count = self.db.query(DBDocument).filter(
                DBDocument.namespace == namespace,
                DBDocument.is_active == True
            ).count()
            
            logger.info(f"Namespace '{namespace}' ресинхронизирован")
            
            return {
                "namespace": namespace,
                "documents_count": doc_count,
                "message": "Ресинхронизация завершена"
            }
            
        except Exception as e:
            logger.error(f"Ошибка ресинхронизации: {e}")
            raise

    def index_document(self, document: 'DBDocument') -> bool:
        """
        Индексирует документ в векторном хранилище.
        
        Args:
            document: Документ для индексации
            
        Returns:
            True, если документ успешно проиндексирован
        """
        try:
            # Создаем документ LlamaIndex
            llama_doc = Document(
                text=document.content,
                metadata={
                    "title": document.title,
                    "source_type": document.source_type,
                    "namespace": document.namespace,
                    "document_id": document.id,
                    "vector_id": document.vector_id,
                }
            )
            
            # Получаем индекс для namespace
            index = self._get_index(document.namespace)
            
            # Добавляем документ в индекс
            index.insert(llama_doc)
            
            # Очищаем кэш для namespace
            if document.namespace in self._chat_engines:
                del self._chat_engines[document.namespace]
            
            logger.info(f"Документ {document.id} успешно проиндексирован в namespace {document.namespace}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка индексации документа {document.id}: {e}")
            raise 

    def chat_with_docs(self, message: str, namespace: str = "default") -> str:
        """
        Чат с документами через встроенный ChatEngine.
        
        Args:
            message: Сообщение пользователя
            namespace: Пространство имен для поиска документов
            
        Returns:
            Ответ на вопрос пользователя
        """
        try:
            # Получаем chat engine для namespace
            chat_engine = self._get_chat_engine(namespace)
            
            # Получаем ответ через встроенный chat engine
            response = chat_engine.chat(message)
            
            # Извлечение источников
            sources = []
            if hasattr(response, 'source_nodes') and response.source_nodes:
                for node in response.source_nodes:
                    if hasattr(node, 'metadata'):
                        sources.append({
                            "document_title": node.metadata.get("title", "Unknown"),
                            "source_type": node.metadata.get("source_type", "unknown"),
                            "score": getattr(node, 'score', 0.0)
                        })
            
            # Формируем ответ с источниками
            result = str(response)
            
            if sources:
                result += "\n\n📚 **Источники:**\n"
                for i, source in enumerate(sources, 1):
                    title = source.get('document_title', 'Неизвестный документ')
                    score = source.get('score', 0.0)
                    result += f"{i}. {title} (релевантность: {score:.3f})\n"
            
            logger.info(f"Получен ответ на запрос в namespace {namespace}")
            return result
            
        except Exception as e:
            logger.error(f"Ошибка при обработке запроса: {e}")
            return f"❌ Ошибка: {str(e)}" 