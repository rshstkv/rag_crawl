"""
Модуль конфигурации приложения с использованием Pydantic Settings.
Все настройки загружаются из переменных окружения.
"""

from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Настройки приложения с валидацией через Pydantic."""
    
    # Azure OpenAI Configuration
    azure_openai_api_key: str = Field(..., env="AZURE_OPENAI_API_KEY")
    azure_openai_endpoint: str = Field(..., env="AZURE_OPENAI_ENDPOINT")
    azure_openai_api_version: str = Field(
        default="2023-12-01-preview", env="AZURE_OPENAI_API_VERSION"
    )
    azure_openai_chat_deployment: str = Field(..., env="AZURE_OPENAI_CHAT_DEPLOYMENT")
    azure_openai_embedding_deployment: str = Field(
        ..., env="AZURE_OPENAI_EMBEDDING_DEPLOYMENT"
    )
    # Новые переменные для моделей (имена моделей OpenAI)
    azure_openai_chat_model: str = Field(..., env="AZURE_OPENAI_CHAT_MODEL")
    azure_openai_embedding_model: str = Field(..., env="AZURE_OPENAI_EMBEDDING_MODEL")
    
    # Database Configuration
    database_url: str = Field(..., env="DATABASE_URL")
    
    # Qdrant Configuration
    qdrant_host: str = Field(default="localhost", env="QDRANT_HOST")
    qdrant_port: int = Field(default=6333, env="QDRANT_PORT")
    qdrant_collection_name: str = Field(default="docs_v2", env="QDRANT_COLLECTION_NAME")
    
    # Application Configuration
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    max_chunk_size: int = Field(default=1024, env="MAX_CHUNK_SIZE")
    chunk_overlap: int = Field(default=200, env="CHUNK_OVERLAP")
    max_retrieval_results: int = Field(default=3, env="MAX_RETRIEVAL_RESULTS")
    max_file_size_mb: int = Field(default=100, env="MAX_FILE_SIZE_MB")
    
    # FastAPI Configuration
    app_host: str = Field(default="0.0.0.0", env="APP_HOST")
    app_port: int = Field(default=8000, env="APP_PORT")
    app_reload: bool = Field(default=False, env="APP_RELOAD")
    
    # Gradio Configuration
    gradio_share: bool = Field(default=False, env="GRADIO_SHARE")
    gradio_debug: bool = Field(default=False, env="GRADIO_DEBUG")
    gradio_server_name: str = Field(default="0.0.0.0", env="GRADIO_SERVER_NAME")
    gradio_server_port: int = Field(default=7860, env="GRADIO_SERVER_PORT")
    
    # Crawl4AI Configuration
    crawl4ai_api_url: str = Field(
        default="https://crawl4ai-dev.delightfulplant-c2330751.westeurope.azurecontainerapps.io/api/v1",
        env="CRAWL4AI_API_URL"
    )
    crawl4ai_timeout: int = Field(default=300, env="CRAWL4AI_TIMEOUT")
    max_concurrent_crawls: int = Field(default=3, env="MAX_CONCURRENT_CRAWLS")
    default_crawl_depth: int = Field(default=3, env="DEFAULT_CRAWL_DEPTH")
    default_max_pages: int = Field(default=50, env="DEFAULT_MAX_PAGES")
    web_content_chunk_size: int = Field(default=1024, env="WEB_CONTENT_CHUNK_SIZE")
    web_content_chunk_overlap: int = Field(default=200, env="WEB_CONTENT_CHUNK_OVERLAP")
    
    # Security (for future versions)
    secret_key: str = Field(
        default="your-secret-key-change-in-production", env="SECRET_KEY"
    )
    algorithm: str = Field(default="HS256", env="ALGORITHM")
    access_token_expire_minutes: int = Field(
        default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    
    class Config:
        """Конфигурация Pydantic Settings."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Глобальный экземпляр настроек
settings = Settings()


def get_settings() -> Settings:
    """Получить экземпляр настроек для dependency injection."""
    return settings 