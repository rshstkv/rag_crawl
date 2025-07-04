"""
SQLAlchemy модели для хранения метаданных документов и истории чатов.
"""

import uuid
from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String, 
    Text,
    Boolean,
    DateTime,
    JSON,
    ForeignKey,
    Index,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


class Document(Base):
    """Модель документа для хранения метаданных."""
    
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(500), nullable=False)
    source_type = Column(String(50), nullable=False)  # pdf, txt, docx, web, etc.
    namespace = Column(String(255), nullable=False)
    source_url = Column(Text, nullable=True)
    content_hash = Column(String(64), nullable=False)  # SHA256 для обнаружения изменений
    vector_id = Column(String(255), nullable=True)  # UUID для связи с Qdrant
    chunks_count = Column(Integer, default=0)  # Количество chunks
    metadata_json = Column("metadata", JSON, nullable=True)  # Дополнительные метаданные
    
    # Поля для веб-кроулинга
    crawl_depth = Column(Integer, nullable=True)  # Глубина кроулинга
    crawl_task_id = Column(String(255), nullable=True)  # ID задачи кроулинга
    crawl_metadata = Column(JSON, nullable=True)  # Метаданные кроулинга
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    
    # Связь с chunks
    chunks = relationship("DocumentChunk", back_populates="document")
    
    # Индексы для производительности
    __table_args__ = (
        Index("idx_documents_namespace", "namespace"),
        Index("idx_documents_content_hash", "content_hash"),
        Index("idx_documents_is_active", "is_active"),
        Index("idx_documents_created_at", "created_at"),
        Index("idx_documents_source_type", "source_type"),
        Index("idx_documents_source_url", "source_url"),
        Index("idx_documents_crawl_task_id", "crawl_task_id"),
        Index("idx_documents_namespace_source", "namespace", "source_type"),
    )
    
    def __repr__(self) -> str:
        return f"<Document(id={self.id}, title='{self.title}', namespace='{self.namespace}')>"


class DocumentChunk(Base):
    """Модель для хранения информации о chunks документов."""
    
    __tablename__ = "document_chunks"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    chunk_index = Column(Integer, nullable=False)  # Порядковый номер chunk'а в документе
    content = Column(Text, nullable=False)  # Текстовое содержимое chunk'а
    vector_id = Column(String(255), unique=True, nullable=False)  # UUID для Qdrant
    metadata_json = Column("metadata", JSON, nullable=True)  # Метаданные chunk'а
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Связь с документом
    document = relationship("Document", back_populates="chunks")
    
    # Индексы
    __table_args__ = (
        Index("idx_chunks_document_id", "document_id"),
        Index("idx_chunks_vector_id", "vector_id"),
        Index("idx_chunks_chunk_index", "chunk_index"),
    )
    
    def __repr__(self) -> str:
        return f"<DocumentChunk(id={self.id}, document_id={self.document_id}, chunk_index={self.chunk_index})>"


class ChatHistory(Base):
    """Модель для хранения истории чатов."""
    
    __tablename__ = "chat_history"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(255), nullable=True)  # Идентификатор сессии
    user_message = Column(Text, nullable=False)
    assistant_message = Column(Text, nullable=False)
    sources_used = Column(JSON, nullable=True)  # Список источников, использованных в ответе
    namespace = Column(String(255), nullable=True)  # Namespace для фильтрации
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Индексы
    __table_args__ = (
        Index("idx_chat_session_id", "session_id"),
        Index("idx_chat_namespace", "namespace"),
        Index("idx_chat_created_at", "created_at"),
    )
    
    def __repr__(self) -> str:
        return f"<ChatHistory(id={self.id}, session_id='{self.session_id}')>"


def generate_vector_id() -> str:
    """Генерирует уникальный UUID для векторного ID."""
    return str(uuid.uuid4()) 