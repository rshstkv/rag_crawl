# 🚀 Быстрый старт RAG Crawl

Это руководство поможет быстро запустить RAG сервис на вашей машине.

## 📋 Предварительные требования

- **Python 3.11+**
- **Poetry** (для управления зависимостями)
- **Docker & Docker Compose** (для БД и Qdrant)
- **Azure OpenAI** аккаунт с доступом к API

## 🛠️ Установка

### 1. Клонирование и установка зависимостей

```bash
# Переход в директорию проекта
cd rag_crawl

# Установка зависимостей через Poetry
poetry install

# Активация виртуального окружения
poetry shell
```

### 2. Настройка переменных окружения

```bash
# Копирование примера конфигурации
cp env.example .env

# Редактирование .env файла (укажите ваши Azure OpenAI ключи)
nano .env
```

**Обязательно настройте в .env:**
```
AZURE_OPENAI_API_KEY=ваш_ключ_azure_openai
AZURE_OPENAI_ENDPOINT=https://ваш-ресурс.openai.azure.com/
AZURE_OPENAI_CHAT_DEPLOYMENT=имя_деплоймента_gpt4
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=имя_деплоймента_embeddings
```

### 3. Запуск внешних сервисов

```bash
# Запуск PostgreSQL и Qdrant через Docker Compose
docker-compose up -d postgres qdrant

# Проверка статуса
docker-compose ps
```

### 4. Инициализация базы данных

```bash
# Инициализация Alembic (только при первом запуске)
poetry run alembic init alembic

# Создание первой миграции
poetry run alembic revision --autogenerate -m "Initial migration"

# Применение миграций
poetry run alembic upgrade head
```

## 🏃‍♂️ Запуск приложения

### Вариант 1: Через Poetry

```bash
# Запуск сервера разработки
poetry run python -m src.rag_crawl.main

# Или через uvicorn напрямую
poetry run uvicorn src.rag_crawl.main:app --host 0.0.0.0 --port 8000 --reload
```

### Вариант 2: Через Docker (опционально)

```bash
# Сборка образа
docker build -t rag-crawl .

# Запуск контейнера
docker run -p 8000:8000 --env-file .env rag-crawl
```

## 🌐 Доступ к интерфейсам

После запуска сервиса будут доступны:

- **📚 API Документация (Swagger)**: http://localhost:8000/docs
- **🤖 Gradio UI (Чат с документами)**: http://localhost:8000/gradio
- **🔍 ReDoc API**: http://localhost:8000/redoc
- **❤️ Health Check**: http://localhost:8000/api/health

## 📖 Использование

### Загрузка документов через API

```bash
# Загрузка PDF документа
curl -X POST "http://localhost:8000/api/documents/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@your_document.pdf" \
  -F "namespace=my_docs"
```

### Чат с документами

```bash
# Отправка вопроса
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Расскажи о содержании документа",
    "namespace": "my_docs"
  }'
```

### Использование Gradio UI

1. Откройте http://localhost:8000/gradio
2. Загрузите документы в разделе "Управление документами"
3. Задавайте вопросы в чате
4. Получайте ответы с указанием источников

## 🔧 Разработка

### Структура проекта

```
rag_crawl/
├── src/rag_crawl/           # Основной код
│   ├── api/                 # FastAPI роуты
│   ├── database/            # SQLAlchemy модели
│   ├── services/            # Бизнес-логика
│   ├── ui/                  # Gradio интерфейс
│   ├── utils/               # Утилиты
│   ├── config.py            # Конфигурация
│   └── main.py              # Точка входа
├── alembic/                 # Миграции БД
├── specs/                   # Документация
├── docker-compose.yml       # Docker сервисы
└── pyproject.toml          # Зависимости
```

### Полезные команды

```bash
# Форматирование кода
poetry run black src/
poetry run isort src/

# Линтинг
poetry run ruff src/

# Тесты (когда будут добавлены)
poetry run pytest

# Создание новой миграции
poetry run alembic revision --autogenerate -m "Description"

# Применение миграций
poetry run alembic upgrade head

# Откат миграций
poetry run alembic downgrade -1
```

## 🐛 Решение проблем

### Проблемы с подключением к БД

```bash
# Проверка статуса PostgreSQL
docker-compose logs postgres

# Перезапуск сервисов
docker-compose restart postgres qdrant
```

### Проблемы с Qdrant

```bash
# Проверка логов Qdrant
docker-compose logs qdrant

# Проверка доступности через API
curl http://localhost:6333/health
```

### Проблемы с Azure OpenAI

```bash
# Проверка переменных окружения
echo $AZURE_OPENAI_API_KEY

# Тест подключения
curl -H "api-key: YOUR_KEY" "https://your-resource.openai.azure.com/"
```

## 📊 Мониторинг

### Health Checks

```bash
# Общий статус
curl http://localhost:8000/api/health

# Статус БД
curl http://localhost:8000/api/health/database

# Статус Qdrant
curl http://localhost:8000/api/health/qdrant

# Статус Azure OpenAI
curl http://localhost:8000/api/health/azure
```

### Логи

```bash
# Логи приложения (если запущено через Docker)
docker-compose logs app

# Логи PostgreSQL
docker-compose logs postgres

# Логи Qdrant
docker-compose logs qdrant
```

## 🚢 Продакшн деплой

Для продакшн деплоя рекомендуется:

1. Использовать PostgreSQL и Qdrant в managed версиях
2. Настроить Azure Key Vault для секретов
3. Использовать Azure Container Apps или Kubernetes
4. Настроить мониторинг и логирование
5. Использовать CDN для статических файлов

## 🆘 Поддержка

При возникновении проблем:

1. Проверьте логи сервисов
2. Убедитесь, что все переменные окружения настроены
3. Проверьте доступность внешних сервисов (Azure OpenAI, БД)
4. Обратитесь к документации в папке `specs/`

## 📝 Лицензия

MIT License - см. файл LICENSE для деталей. 