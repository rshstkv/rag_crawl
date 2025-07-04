"""
Сервис для работы с документами.
Предоставляет методы для создания, получения и удаления документов.
"""

import logging
import uuid
from typing import List, Dict, Any, Optional

from sqlalchemy.orm import Session

from ..database.connection import SessionLocal
from ..database.models import Document
from ..config import settings

logger = logging.getLogger(__name__)


class DocumentService:
    """
    Сервис для работы с документами.
    """

    def __init__(self):
        """Инициализация сервиса."""
        self._db = SessionLocal()

    def __del__(self):
        """Закрытие соединения с БД при уничтожении объекта."""
        self._db.close()

    def create_document(
        self,
        content: str,
        metadata: Dict[str, Any],
        namespace: str = "default"
    ) -> Document:
        """
        Создание нового документа.
        
        Args:
            content: Текстовое содержимое документа
            metadata: Метаданные документа
            namespace: Пространство имен для документа
            
        Returns:
            Созданный документ
        """
        try:
            # Создание документа в БД
            document = Document(
                title=metadata.get("source", "Без названия"),
                source_type="txt",
                namespace=namespace,
                source_url=metadata.get("source", ""),
                content=content,
                content_hash=str(hash(content)),
                vector_id=str(uuid.uuid4()),
                chunks_count=max(1, len(content) // settings.max_chunk_size),
                metadata_json=metadata
            )
            
            self._db.add(document)
            self._db.commit()
            self._db.refresh(document)
            
            logger.info(f"Документ создан: {document.id}, namespace: {namespace}")
            return document
            
        except Exception as e:
            logger.error(f"Ошибка создания документа: {e}")
            self._db.rollback()
            raise

    def get_documents(
        self, 
        namespace: Optional[str] = None,
        source_type: Optional[str] = None
    ) -> List[Document]:
        """
        Получение списка документов.
        
        Args:
            namespace: Опциональный фильтр по пространству имен
            source_type: Опциональный фильтр по типу источника (web, pdf, txt, etc.)
            
        Returns:
            Список документов
        """
        try:
            query = self._db.query(Document).filter(Document.is_active == True)
            
            if namespace:
                query = query.filter(Document.namespace == namespace)
            
            if source_type:
                query = query.filter(Document.source_type == source_type)
                
            documents = query.order_by(Document.created_at.desc()).all()
            return documents
            
        except Exception as e:
            logger.error(f"Ошибка получения списка документов: {e}")
            raise

    def get_web_documents(self, namespace: Optional[str] = None) -> List[Document]:
        """
        Получение веб-документов.
        
        Args:
            namespace: Опциональный фильтр по пространству имен
            
        Returns:
            Список веб-документов
        """
        return self.get_documents(namespace=namespace, source_type="web")

    def get_documents_by_crawl_task(self, task_id: str) -> List[Document]:
        """
        Получение документов по ID задачи кроулинга.
        
        Args:
            task_id: ID задачи кроулинга
            
        Returns:
            Список документов созданных этой задачей
        """
        try:
            documents = self._db.query(Document).filter(
                Document.crawl_task_id == task_id,
                Document.is_active == True
            ).order_by(Document.created_at.desc()).all()
            return documents
            
        except Exception as e:
            logger.error(f"Ошибка получения документов для задачи {task_id}: {e}")
            raise

    def get_document(self, document_id: int) -> Optional[Document]:
        """
        Получение документа по ID.
        
        Args:
            document_id: ID документа
            
        Returns:
            Документ или None, если не найден
        """
        try:
            document = self._db.query(Document).filter(Document.id == document_id).first()
            return document
            
        except Exception as e:
            logger.error(f"Ошибка получения документа {document_id}: {e}")
            raise

    def delete_document(self, document_id: int) -> bool:
        """
        Удаление документа по ID.
        
        Args:
            document_id: ID документа
            
        Returns:
            True, если документ успешно удален
        """
        try:
            document = self._db.query(Document).filter(Document.id == document_id).first()
            
            if not document:
                return False
                
            self._db.delete(document)
            self._db.commit()
            
            logger.info(f"Документ удален: {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка удаления документа {document_id}: {e}")
            self._db.rollback()
            raise

    def delete_documents_by_crawl_task(self, task_id: str) -> int:
        """
        Удаление всех документов созданных определенной задачей кроулинга.
        
        Args:
            task_id: ID задачи кроулинга
            
        Returns:
            Количество удаленных документов
        """
        try:
            documents = self._db.query(Document).filter(
                Document.crawl_task_id == task_id
            ).all()
            
            count = len(documents)
            
            for document in documents:
                self._db.delete(document)
            
            self._db.commit()
            
            logger.info(f"Удалено {count} документов для задачи {task_id}")
            return count
            
        except Exception as e:
            logger.error(f"Ошибка удаления документов для задачи {task_id}: {e}")
            self._db.rollback()
            raise

    def update_document_metadata(self, document_id: int, metadata: Dict[str, Any]) -> bool:
        """
        Обновление метаданных документа.
        
        Args:
            document_id: ID документа
            metadata: Новые метаданные
            
        Returns:
            True, если документ успешно обновлен
        """
        try:
            document = self._db.query(Document).filter(Document.id == document_id).first()
            
            if not document:
                return False
            
            # Объединяем существующие метаданные с новыми
            current_metadata = document.metadata_json or {}
            current_metadata.update(metadata)
            document.metadata_json = current_metadata
            
            self._db.commit()
            
            logger.info(f"Метаданные документа {document_id} обновлены")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка обновления метаданных документа {document_id}: {e}")
            self._db.rollback()
            raise 