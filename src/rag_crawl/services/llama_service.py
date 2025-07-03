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
from llama_index.core.postprocessor import SimilarityPostprocessor
from llama_index.core.ingestion import IngestionPipeline
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

    def _get_vector_store(self) -> QdrantVectorStore:
        """Получение Qdrant векторного хранилища (исправлено согласно документации LlamaIndex)."""
        try:
            client = qdrant_client.QdrantClient(
                host=settings.qdrant_host,    # localhost
                port=settings.qdrant_port,    # 6333
                timeout=30,                   # Таймаут соединения
                prefer_grpc=False            # Используем HTTP вместо gRPC
            )
            
            # Проверяем существование коллекции и создаем если нужно
            collection_name = settings.qdrant_collection_name
            try:
                client.get_collection(collection_name)
                logger.info(f"✅ Коллекция '{collection_name}' уже существует")
            except Exception:
                # Коллекция не существует, создаем её
                from qdrant_client.models import Distance, VectorParams
                client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=1536,  # Размер векторов Azure OpenAI embeddings
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"✅ Создана новая коллекция '{collection_name}'")
            
            vector_store = QdrantVectorStore(
                client=client,
                collection_name=collection_name
            )
            
            logger.info(f"✅ Используется QdrantVectorStore: {settings.qdrant_host}:{settings.qdrant_port}/{collection_name}")
            return vector_store
            
        except Exception as e:
            logger.error(f"❌ Ошибка подключения к Qdrant: {e}")
            raise

    def _get_vector_store_lazy(self) -> Any:
        """Ленивая инициализация vector store."""
        if self._vector_store is None:
            self._vector_store = self._get_vector_store()
        return self._vector_store

    def _get_index(self, namespace: str) -> VectorStoreIndex:
        """Получение или создание индекса для namespace (обновлено для Qdrant)."""
        if namespace not in self._indices:
            vector_store = self._get_vector_store_lazy()
            storage_context = StorageContext.from_defaults(vector_store=vector_store)
            
            # Пытаемся загрузить существующий индекс из Qdrant
            try:
                self._indices[namespace] = VectorStoreIndex.from_vector_store(
                    vector_store=vector_store,
                    storage_context=storage_context
                )
                logger.info(f"✅ Загружен существующий Qdrant индекс для namespace: {namespace}")
            except Exception as e:
                # Если коллекция пуста или не существует, создаем новый индекс
                logger.info(f"Создаем новый Qdrant индекс для namespace: {namespace} (причина: {e})")
                self._indices[namespace] = VectorStoreIndex(
                    [],
                    storage_context=storage_context
                )
                logger.info(f"✅ Создан новый Qdrant индекс для namespace: {namespace}")
            
        return self._indices[namespace]

    def _get_chat_engine(self, namespace: str, session_id: Optional[str] = None):
        """Получение chat engine для namespace с фильтрацией релевантности."""
        cache_key = f"{namespace}:{session_id or 'default'}"
        
        if cache_key not in self._chat_engines:
            index = self._get_index(namespace)
            
            # Настройка постпроцессоров для фильтрации релевантности
            node_postprocessors = [
                SimilarityPostprocessor(similarity_cutoff=0.75)  # Тот же фильтр что и в query
            ]
            
            # Создаем chat engine с фильтрацией релевантности
            chat_engine = index.as_chat_engine(
                chat_mode="context",
                similarity_top_k=10,  # Увеличиваем до фильтрации
                node_postprocessors=node_postprocessors,
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
        Загрузка и обработка документа через IngestionPipeline (исправлено согласно спецификации).
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
                "upload_source": "file_upload",
                "language": "ru",
            }
            
            llama_doc = Document(
                text=cleaned_text,
                metadata=rich_metadata
            )
            
            # Получаем vector store для pipeline
            vector_store = self._get_vector_store_lazy()
            
            # ✅ ИСПРАВЛЕНО: Создание pipeline для правильного чанкинга
            pipeline = IngestionPipeline(
                transformations=[
                    SentenceSplitter(
                        chunk_size=settings.max_chunk_size,    # 1024
                        chunk_overlap=settings.chunk_overlap   # 200
                    ),
                    self.embed_model,
                ],
                vector_store=vector_store,
            )
            
            # Обработка документа через pipeline (это создаст правильные чанки)
            nodes = pipeline.run(documents=[llama_doc])
            chunk_count = len(nodes)
            
            logger.info(f"✅ IngestionPipeline создал {chunk_count} чанков из документа '{title}'")
            
            # Сохранение метаданных в БД
            db_document = DBDocument(
                title=title,
                source_type=source_type,
                namespace=namespace,
                source_url=file.filename,
                content_hash=str(hash(cleaned_text)),
                vector_id=str(uuid.uuid4()),
                chunks_count=chunk_count,  # Реальное количество чанков
                metadata_json=rich_metadata
            )
            
            self.db.add(db_document)
            self.db.commit()
            self.db.refresh(db_document)
            
            # Создаем чанки в базе данных для каждого node
            for i, node in enumerate(nodes):
                chunk = DocumentChunk(
                    document_id=db_document.id,
                    chunk_index=i,
                    content=node.text,
                    vector_id=node.node_id,
                    metadata_json={**rich_metadata, "chunk_index": i}
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
            
            logger.info(f"✅ Документ '{title}' загружен в namespace '{namespace}', создано {chunk_count} чанков через IngestionPipeline")
            
            return db_document
            
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки документа: {e}")
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
        Простой запрос с фильтрацией релевантности (обновлено согласно спецификации).
        """
        try:
            index = self._get_index(namespace)
            
            # Настройка постпроцессоров для фильтрации релевантности
            node_postprocessors = [
                SimilarityPostprocessor(similarity_cutoff=0.75)  # Фильтр релевантности
            ]
            
            # Создание query engine с фильтрацией
            query_engine = index.as_query_engine(
                similarity_top_k=10,  # Увеличиваем до фильтрации
                node_postprocessors=node_postprocessors,
                verbose=True
            )
            
            # Выполнение запроса
            response = query_engine.query(question)
            
            # Извлечение источников с улучшенной информацией
            sources = []
            if hasattr(response, 'source_nodes') and response.source_nodes:
                for node in response.source_nodes:
                    if hasattr(node, 'metadata'):
                        sources.append({
                            "document_title": node.metadata.get("title", "Unknown"),
                            "source_type": node.metadata.get("source_type", "unknown"),
                            "score": round(getattr(node, 'score', 0.0), 3),  # Округляем для читаемости
                            "document_id": node.metadata.get("document_id"),
                            "chunk_index": node.metadata.get("chunk_index", 0)
                        })
            
            logger.info(f"✅ Query выполнен, найдено {len(sources)} релевантных источников (>0.75)")
            
            return {
                "response": str(response),
                "sources": sources,
                "total_sources": len(sources)  # Добавляем счетчик для отладки
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка запроса: {e}")
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