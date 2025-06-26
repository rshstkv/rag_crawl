# Руководство по разработке RAG Crawl

## Быстрый старт

### Предварительные требования

- **Python 3.11+**
- **Poetry** для управления зависимостями
- **Docker & Docker Compose** для локальных сервисов
- **Azure OpenAI** аккаунт с API ключами

### Установка и настройка

1. **Клонирование и установка зависимостей**
```bash
git clone <repository>
cd rag_crawl
poetry install
```

2. **Настройка окружения**
```bash
cp .env.example .env
# Отредактируйте .env файл с вашими Azure OpenAI ключами
```

3. **Запуск инфраструктуры**
```bash
docker-compose up -d postgres qdrant
```

4. **Инициализация базы данных**
```bash
poetry run alembic upgrade head
```

5. **Запуск приложения**
```bash
poetry run python -m rag_crawl.main
```

Приложение будет доступно на:
- **API**: http://localhost:8000
- **Gradio UI**: http://localhost:8000 (встроен в FastAPI)
- **API Docs**: http://localhost:8000/docs

## Структура проекта

```
rag_crawl/
├── specs/                          # 📚 Техническая документация
│   ├── technical_requirements.md   # Техническое задание
│   ├── architecture_design.md      # Архитектурный дизайн
│   └── development_guide.md        # Это руководство
├── src/rag_crawl/                  # 🐍 Основной код
│   ├── __init__.py
│   ├── config.py                   # ⚙️ Конфигурация приложения
│   ├── main.py                     # 🚀 Точка входа FastAPI
│   ├── database/                   # 🗄️ Работа с БД
│   │   ├── __init__.py
│   │   ├── models.py              # SQLAlchemy модели
│   │   ├── connection.py          # Подключения к БД
│   │   └── repositories.py        # Репозитории данных
│   ├── services/                   # 🔧 Бизнес-логика
│   │   ├── __init__.py
│   │   ├── document_service.py    # Обработка документов
│   │   ├── chat_service.py        # Чат-сервис
│   │   ├── rag_service.py         # RAG логика
│   │   └── vector_service.py      # Работа с Qdrant
│   ├── api/                       # 🌐 REST API endpoints
│   │   ├── __init__.py
│   │   ├── documents.py           # Документы API
│   │   ├── chat.py                # Чат API
│   │   └── health.py              # Health checks
│   ├── ui/                        # 🎨 Пользовательский интерфейс
│   │   ├── __init__.py
│   │   └── gradio_app.py          # Gradio приложение
│   └── utils/                     # 🛠️ Утилиты
│       ├── __init__.py
│       ├── text_processing.py     # Обработка текста
│       ├── file_handlers.py       # Работа с файлами
│       └── logging.py             # Логирование
├── tests/                         # 🧪 Тесты
│   ├── unit/                      # Unit тесты
│   ├── integration/               # Интеграционные тесты
│   └── fixtures/                  # Тестовые данные
├── alembic/                       # 📊 Миграции БД
│   ├── versions/                  # Файлы миграций
│   ├── env.py                     # Конфигурация Alembic
│   └── script.py.mako             # Шаблон миграций
├── .cursorrules                   # 📋 Правила разработки
├── docker-compose.yml             # 🐳 Docker окружение
├── pyproject.toml                 # 📦 Poetry конфигурация
├── .env.example                   # 🔐 Пример переменных окружения
└── README.md                      # 📖 Основная документация
```

## Конфигурация переменных окружения

### Обязательные переменные

```bash
# Azure OpenAI Configuration
AZURE_OPENAI_API_KEY=your_azure_openai_api_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2023-12-01-preview
AZURE_OPENAI_CHAT_DEPLOYMENT=gpt-4
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002

# Database Configuration  
DATABASE_URL=postgresql://rag_user:rag_password@localhost:5432/rag_crawl

# Qdrant Configuration
QDRANT_HOST=localhost
QDRANT_PORT=6333
```

### Опциональные переменные

```bash
# Application Configuration
LOG_LEVEL=INFO                     # DEBUG, INFO, WARNING, ERROR
MAX_CHUNK_SIZE=1024               # Размер chunks в токенах
CHUNK_OVERLAP=200                 # Перекрытие chunks
MAX_RETRIEVAL_RESULTS=3           # Количество источников в ответе

# Gradio Configuration
GRADIO_SHARE=false                # Публичная ссылка Gradio
GRADIO_DEBUG=true                 # Режим отладки
```

## Команды разработки

### Установка зависимостей
```bash
# Установка всех зависимостей
poetry install

# Добавление новой зависимости
poetry add package_name

# Добавление dev зависимости
poetry add --group dev package_name
```

### Запуск сервисов

```bash
# Запуск всех внешних сервисов
docker-compose up -d

# Запуск только PostgreSQL
docker-compose up -d postgres

# Запуск только Qdrant
docker-compose up -d qdrant

# Остановка всех сервисов
docker-compose down

# Очистка данных (ВНИМАНИЕ: удаляет все данные!)
docker-compose down -v
```

### Работа с базой данных

```bash
# Создание новой миграции
poetry run alembic revision --autogenerate -m "Description"

# Применение миграций
poetry run alembic upgrade head

# Откат на одну миграцию назад
poetry run alembic downgrade -1

# Просмотр истории миграций
poetry run alembic history
```

### Линтеры и форматирование

```bash
# Форматирование кода
poetry run black src/ tests/

# Сортировка импортов
poetry run isort src/ tests/

# Проверка типов
poetry run mypy src/

# Проверка стиля
poetry run flake8 src/ tests/

# Все проверки сразу
poetry run pre-commit run --all-files
```

### Тестирование

```bash
# Запуск всех тестов
poetry run pytest

# Запуск с покрытием
poetry run pytest --cov=src/rag_crawl

# Запуск только unit тестов
poetry run pytest tests/unit/

# Запуск только интеграционных тестов
poetry run pytest tests/integration/

# Запуск конкретного теста
poetry run pytest tests/unit/test_document_service.py::test_upload_document
```

## Разработка компонентов

### Создание нового сервиса

1. **Создайте файл сервиса**
```python
# src/rag_crawl/services/new_service.py
from typing import Protocol
from sqlalchemy.orm import Session

class NewService:
    def __init__(self, db: Session):
        self._db = db
    
    async def some_method(self, param: str) -> str:
        """Описание метода."""
        # Бизнес-логика здесь
        pass
```

2. **Добавьте в DI контейнер**
```python
# src/rag_crawl/dependencies.py
def get_new_service(db: Session = Depends(get_db)) -> NewService:
    return NewService(db)
```

3. **Создайте API endpoint**
```python
# src/rag_crawl/api/new_endpoint.py
from fastapi import APIRouter, Depends
from ..services.new_service import NewService
from ..dependencies import get_new_service

router = APIRouter()

@router.post("/api/new-endpoint")
async def new_endpoint(
    service: NewService = Depends(get_new_service)
):
    return await service.some_method("param")
```

### Добавление новой модели данных

1. **Определите SQLAlchemy модель**
```python
# src/rag_crawl/database/models.py
class NewModel(Base):
    __tablename__ = "new_table"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

2. **Создайте Pydantic схемы**
```python
# src/rag_crawl/schemas/new_schemas.py
from pydantic import BaseModel
from datetime import datetime

class NewModelCreate(BaseModel):
    name: str

class NewModelResponse(BaseModel):
    id: int
    name: str
    created_at: datetime
    
    class Config:
        from_attributes = True
```

3. **Создайте миграцию**
```bash
poetry run alembic revision --autogenerate -m "Add new_table"
poetry run alembic upgrade head
```

## Отладка и логирование

### Структурированные логи

```python
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)

# Хороший пример логирования
logger.info(
    json.dumps({
        "timestamp": datetime.utcnow().isoformat(),
        "level": "INFO",
        "component": "document_service",
        "action": "upload_document",
        "document_id": document.id,
        "namespace": document.namespace,
        "size_bytes": len(content)
    })
)
```

### Отладка Qdrant

```bash
# Проверка коллекций
curl http://localhost:6333/collections

# Информация о коллекции
curl http://localhost:6333/collections/documents

# Поиск точек (для отладки)
curl -X POST http://localhost:6333/collections/documents/points/search \
  -H 'Content-Type: application/json' \
  -d '{
    "vector": [0.1, 0.2, ...],
    "limit": 3
  }'
```

### Отладка PostgreSQL

```bash
# Подключение к БД
docker-compose exec postgres psql -U rag_user -d rag_crawl

# Полезные SQL запросы
SELECT * FROM documents ORDER BY created_at DESC LIMIT 5;
SELECT namespace, COUNT(*) FROM documents GROUP BY namespace;
SELECT * FROM chat_history ORDER BY created_at DESC LIMIT 5;
```

## Производительность и мониторинг

### Профилирование

```python
# Профилирование медленных операций
import time
import functools

def profile_time(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.time()
        result = await func(*args, **kwargs)
        duration = time.time() - start
        logger.info(f"{func.__name__} took {duration:.2f} seconds")
        return result
    return wrapper

@profile_time
async def slow_operation():
    # Медленная операция
    pass
```

### Health Checks

```bash
# Проверка состояния всех сервисов
curl http://localhost:8000/api/health

# Пример ответа
{
  "status": "healthy",
  "database": {"status": "up", "response_time_ms": 5},
  "qdrant": {"status": "up", "response_time_ms": 12},
  "azure_openai": {"status": "up", "response_time_ms": 245}
}
```

## Часто встречающиеся проблемы

### 1. Ошибки подключения к Azure OpenAI

**Проблема**: `Authentication failed` или `Rate limit exceeded`

**Решение**:
- Проверьте правильность API ключей в `.env`
- Убедитесь, что deployment names соответствуют реальным
- Проверьте лимиты в Azure Portal

### 2. Qdrant недоступен

**Проблема**: `ConnectionError: Cannot connect to Qdrant`

**Решение**:
```bash
# Проверьте статус контейнера
docker-compose ps qdrant

# Перезапустите сервис
docker-compose restart qdrant

# Проверьте логи
docker-compose logs qdrant
```

### 3. Ошибки миграций PostgreSQL

**Проблема**: `Target database is not up to date`

**Решение**:
```bash
# Проверьте текущую версию
poetry run alembic current

# Примените миграции
poetry run alembic upgrade head

# В случае конфликтов - откатитесь и примените заново
poetry run alembic downgrade base
poetry run alembic upgrade head
```

### 4. Проблемы с memory при больших документах

**Проблема**: Out of memory при обработке больших файлов

**Решение**:
- Уменьшите `MAX_CHUNK_SIZE` в конфигурации
- Добавьте пагинацию при обработке
- Используйте streaming для больших файлов

## Развертывание в продакшн

### Docker образ приложения

```dockerfile
# Dockerfile (будет создан позже)
FROM python:3.11-slim

WORKDIR /app

# Install Poetry
RUN pip install poetry

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev

# Copy application code
COPY src/ ./src/

# Expose port
EXPOSE 8000

# Run application
CMD ["python", "-m", "rag_crawl.main"]
```

### Docker Compose для продакшн

```yaml
# docker-compose.prod.yml (будет создан позже)
version: '3.8'
services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/rag_crawl
      - QDRANT_HOST=qdrant
    depends_on:
      - postgres
      - qdrant
    
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: rag_crawl
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      
  qdrant:
    image: qdrant/qdrant:v1.6.1
    volumes:
      - qdrant_data:/qdrant/storage

volumes:
  postgres_data:
  qdrant_data:
```

## Планы развития

### Версия 0.2
- [ ] Интеграция с внешними crawling сервисами
- [ ] Улучшенная обработка HTML контента
- [ ] Batch операции для массовой загрузки
- [ ] Redis кэширование для embeddings

### Версия 0.3  
- [ ] Простая аутентификация (JWT)
- [ ] Расширенные API для интеграций
- [ ] Метрики и мониторинг (Prometheus)
- [ ] Автоматические бэкапы данных

### Версия 1.0
- [ ] Мультитенантность
- [ ] Горизонтальное масштабирование
- [ ] Продвинутые алгоритмы re-ranking
- [ ] Admin панель для управления 