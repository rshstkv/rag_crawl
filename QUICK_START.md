# 🚀 RAG Crawl - Быстрый старт

## Что это?

RAG Crawl - это современное веб-приложение для работы с документами через AI чат. Загружайте документы, задавайте вопросы, получайте точные ответы с указанием источников.

## Требования

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- Azure OpenAI API ключ

## Пошаговая установка

### 1. Настройка переменных окружения

```bash
cp env.example .env
```

Заполните в `.env`:
```env
AZURE_OPENAI_API_KEY=your_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
DATABASE_URL=postgresql://rag_user:rag_password@localhost:5432/rag_crawl
```

### 2. Автоматическая установка

```bash
# Сделайте скрипт исполняемым (один раз)
chmod +x start-dev.sh

# Запустите автоустановку
./start-dev.sh
```

Скрипт автоматически:
- ✅ Запустит Docker сервисы (PostgreSQL, Qdrant)
- ✅ Применит миграции БД
- ✅ Установит frontend зависимости
- ✅ Покажет команды для запуска

### 3. Запуск сервисов

**Терминал 1 - Backend API:**
```bash
poetry run python -m rag_crawl.main
# Доступен на http://localhost:8000
```

**Терминал 2 - Frontend:**
```bash
cd frontend && npm run dev
# Доступен на http://localhost:3000
```

### 4. Использование

1. Откройте http://localhost:3000
2. Загрузите документы в правой панели
3. Задавайте вопросы в чате
4. Получайте ответы с источниками!

## Остановка

```bash
# Остановить Docker сервисы
docker-compose down

# Остановить dev серверы - Ctrl+C в терминалах
```

## Полезные ссылки

- 🌐 **Frontend**: http://localhost:3000
- 🔧 **API**: http://localhost:8000
- 📚 **API Docs**: http://localhost:8000/docs
- 🗄️ **Qdrant**: http://localhost:6333/dashboard

## Проблемы?

1. **API ошибки**: Проверьте Azure OpenAI ключи в `.env`
2. **Docker не запускается**: `docker-compose down && docker-compose up -d`
3. **Frontend не собирается**: `cd frontend && npm install`
4. **БД ошибки**: `poetry run alembic upgrade head`

## Что дальше?

- Изучите [полную документацию](README.md)
- Попробуйте [API endpoints](http://localhost:8000/docs)
- Настройте production деплой 