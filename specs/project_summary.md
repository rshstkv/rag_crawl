# RAG Crawl - Резюме проекта

## 🎯 Цель проекта

Создание микросервиса для **RAG (Retrieval Augmented Generation)** системы с возможностью:
- Загрузки и индексации документов различных форматов
- Диалогового общения с документами через чат-интерфейс  
- Указания точных источников в ответах
- Ресинхронизации документов по группам (namespace)

## 🛠️ Технологический стек

### Основные компоненты
| Компонент | Технология | Назначение |
|-----------|------------|------------|
| **Backend** | FastAPI + Python 3.11 | REST API и бизнес-логика |
| **UI** | Gradio 4.7+ | Веб-интерфейс для демо |
| **RAG Framework** | LlamaIndex 0.9+ | Обработка документов и retrieval |
| **LLM** | Azure OpenAI GPT-4 | Генерация ответов |
| **Embeddings** | Azure OpenAI text-embedding-ada-002 | Векторизация текста |
| **Vector DB** | Qdrant 1.6+ | Хранение векторов |
| **Metadata DB** | PostgreSQL 15 | Метаданные и история |
| **Dependencies** | Poetry | Управление зависимостями |
| **Containers** | Docker Compose | Локальная разработка |

### Порты сервисов
- **FastAPI**: 8000 (основной API + встроенный Gradio)
- **PostgreSQL**: 5432
- **Qdrant**: 6333 (HTTP), 6334 (gRPC)

## 📁 Структура проекта

```
rag_crawl/
├── specs/                    # 📚 Документация
├── src/rag_crawl/           # 🐍 Исходный код
│   ├── config.py            # ⚙️ Конфигурация
│   ├── main.py              # 🚀 FastAPI приложение  
│   ├── database/            # 🗄️ Модели и подключения БД
│   ├── services/            # 🔧 Бизнес-логика
│   ├── api/                 # 🌐 REST API endpoints
│   ├── ui/                  # 🎨 Gradio интерфейс
│   └── utils/               # 🛠️ Вспомогательные утилиты
├── tests/                   # 🧪 Тесты
├── alembic/                 # 📊 Миграции БД
├── .cursorrules             # 📋 Правила разработки
├── docker-compose.yml       # 🐳 Локальное окружение
└── pyproject.toml           # 📦 Poetry конфигурация
```

## 🔄 Основные процессы

### 1. Загрузка документа
```
Пользователь → Gradio UI → FastAPI → DocumentService → 
→ Извлечение текста → Chunking → PostgreSQL (метаданные) → 
→ VectorService → Azure OpenAI (embeddings) → Qdrant (векторы)
```

### 2. Чат-запрос  
```
Вопрос → Gradio UI → FastAPI → RAGService → 
→ VectorService → Поиск похожих chunks → 
→ Azure OpenAI (генерация ответа) → Ответ с источниками
```

### 3. Ресинхронизация
```
Триггер → DocumentService → Проверка изменений → 
→ Удаление старых векторов → Повторная обработка → 
→ Обновление БД и векторного хранилища
```

## 📋 Ключевые принципы

### Архитектурные принципы
- **Модульная архитектура** с четким разделением слоев
- **Dependency Injection** для тестируемости
- **Single Responsibility** для каждого сервиса
- **Тонкие API контроллеры** - вся логика в сервисах

### Принципы разработки
- **OOP без избыточности** - композиция вместо наследования
- **Типизация везде** - type hints обязательны
- **Structured logging** - JSON формат для логов
- **Конфигурация через ENV** - Pydantic Settings

### Ограничения размеров
- **Сервисы**: максимум 300 строк на файл
- **Функции**: максимум 50 строк, 4 параметра
- **API endpoints**: максимум 150 строк на файл

## 🗃️ Схема данных

### PostgreSQL таблицы
```sql
documents          # Метаданные документов (title, namespace, source_type, etc.)
document_chunks    # Информация о chunks (content, vector_id, metadata)
chat_history       # История диалогов (user_message, assistant_message, sources_used)
```

### Qdrant коллекции
```
documents          # Векторы chunks (1536 измерений, metadata с document_id)
```

## 🚀 Быстрый старт

```bash
# 1. Клонировать и установить зависимости
poetry install

# 2. Настроить окружение
cp .env.example .env
# Отредактировать .env с Azure OpenAI ключами

# 3. Запустить инфраструктуру  
docker-compose up -d postgres qdrant

# 4. Применить миграции
poetry run alembic upgrade head

# 5. Запустить приложение
poetry run python -m rag_crawl.main
```

Доступ:
- **API Docs**: http://localhost:8000/docs
- **Gradio UI**: http://localhost:8000

## 🎨 Пользовательский интерфейс

### Gradio функции
- **Загрузка файлов**: drag&drop интерфейс
- **Управление namespace**: группировка документов
- **Чат-интерфейс**: диалог с указанием источников
- **Ресинхронизация**: обновление документов
- **История чатов**: просмотр предыдущих диалогов

### API Endpoints  
```
POST /api/documents/upload      # Загрузка документа
GET  /api/documents             # Список документов  
POST /api/documents/resync      # Ресинхронизация
POST /api/chat                  # Чат API
GET  /api/chat/history         # История чатов
GET  /api/health               # Health check
```

## 🔧 Настройка Azure OpenAI

### Необходимые deployments
```bash
AZURE_OPENAI_CHAT_DEPLOYMENT=gpt-4                    # Для генерации ответов
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002  # Для векторизации
```

### Настройки chunking
```bash
MAX_CHUNK_SIZE=1024            # Размер chunks в токенах
CHUNK_OVERLAP=200              # Перекрытие между chunks
MAX_RETRIEVAL_RESULTS=3        # Количество источников в ответе
```

## 🧪 Тестирование

### Структура тестов
```
tests/
├── unit/           # Быстрые изолированные тесты (мокируем внешние сервисы)
├── integration/    # Тесты с реальными БД и сервисами  
└── fixtures/       # Тестовые данные и фикстуры
```

### Команды тестирования
```bash
poetry run pytest                              # Все тесты
poetry run pytest --cov=src/rag_crawl         # С покрытием
poetry run pytest tests/unit/                 # Только unit тесты
poetry run pytest tests/integration/          # Только интеграционные
```

## 📊 Мониторинг и отладка

### Health Checks
```bash
curl http://localhost:8000/api/health
```

### Отладка Qdrant
```bash
curl http://localhost:6333/collections                    # Список коллекций
curl http://localhost:6333/collections/documents          # Информация о коллекции
```

### Отладка PostgreSQL
```bash
docker-compose exec postgres psql -U rag_user -d rag_crawl
```

## 🛡️ Безопасность

### Текущие меры
- **Валидация входных данных** через Pydantic
- **Ограничения размеров файлов** (100MB)
- **Санитизация имен файлов**
- **Секреты через ENV переменные**

### Планы (будущие версии)
- JWT аутентификация
- Rate limiting
- Входная фильтрация контента

## 📈 Планы развития

### MVP (версия 0.1)
- ✅ Базовая загрузка документов (PDF, текст)
- ✅ Простой чат с источниками
- ✅ REST API
- ✅ Docker Compose окружение

### Версия 0.2
- [ ] Поддержка Word, Markdown, HTML
- [ ] Интеграция с внешними crawling сервисами
- [ ] Batch загрузка документов
- [ ] Redis кэширование

### Версия 0.3+
- [ ] Аутентификация пользователей
- [ ] Расширенные API интеграции
- [ ] Метрики и мониторинг
- [ ] Горизонтальное масштабирование

## 🚫 Текущие ограничения

### Что НЕ включено в MVP
- Аутентификация и авторизация
- Мультитенантность  
- Масштабирование на несколько инстансов
- Продвинутые алгоритмы re-ranking
- Кастомные embedding модели
- Интеграция с внешними crawlers

### Технические ограничения
- Один инстанс приложения
- Локальная файловая система
- Без кэширования результатов
- Базовый error handling

## 📞 Поддержка

### Основные команды
```bash
# Установка
poetry install

# Запуск dev окружения  
docker-compose up -d
poetry run python -m rag_crawl.main

# Тестирование
poetry run pytest

# Форматирование кода
poetry run black src/ tests/
poetry run isort src/ tests/

# Миграции БД
poetry run alembic upgrade head
```

### Отладка проблем
1. **Azure OpenAI**: проверить ключи и deployment names
2. **Qdrant**: перезапустить контейнер, проверить логи  
3. **PostgreSQL**: проверить миграции, перезапустить БД
4. **Memory issues**: уменьшить размер chunks 