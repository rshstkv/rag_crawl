# Инструкции для разработки RAG Crawl

## Настройка окружения

### 1. Активация Poetry окружения
```bash
poetry install
poetry shell
```

### 2. Настройка переменных окружения
Файл `.env` уже настроен с базовыми параметрами. Проверьте что все ключи Azure OpenAI корректны.

### 3. Запуск базы данных и Qdrant
```bash
docker-compose up -d postgres qdrant
```

### 4. Миграции базы данных
```bash
poetry run alembic upgrade head
```

## Запуск приложения

### Разработка
```bash
poetry run python -m rag_crawl.main
```

### Через uvicorn (рекомендуется для разработки)
```bash
poetry run uvicorn rag_crawl.main:app --reload --host 0.0.0.0 --port 8000
```

## Проверка состояния

### API Health Check
```bash
curl http://localhost:8000/health
```

### API Documentation
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Gradio Interface
- Доступен через FastAPI на том же порту: http://localhost:8000/

## Полезные команды

### Установка новых зависимостей
```bash
poetry add package_name
```

### Форматирование кода
```bash
poetry run black src/
poetry run isort src/
```

### Проверка типов
```bash
poetry run mypy src/
```

## VS Code / Cursor настройки

Окружение настроено автоматически через файлы:
- `.vscode/settings.json` - настройки редактора и Python интерпретатора
- `.vscode/launch.json` - конфигурации отладки

Python интерпретатор: `/Users/romanshestakov/rag_crawl/.venv/bin/python`

## Структура проекта

```
src/rag_crawl/
├── main.py              # FastAPI приложение
├── config.py           # Настройки
├── api/                # API endpoints
├── services/           # Бизнес-логика  
├── database/           # Модели базы данных
├── ui/                 # Gradio интерфейс
└── utils/              # Утилиты
``` 