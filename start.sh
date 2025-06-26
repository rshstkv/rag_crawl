#!/bin/bash

echo "🚀 Запуск RAG Crawl..."

# Проверяем, запущен ли Docker
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker не запущен. Запустите Docker Desktop и попробуйте снова."
    exit 1
fi

# Запускаем базу данных и Qdrant
echo "📦 Запуск базы данных и Qdrant..."
docker-compose up -d postgres qdrant

# Ждем запуска сервисов
echo "⏳ Ожидание запуска сервисов..."
sleep 5

# Проверяем, что Poetry активен
echo "🐍 Активация Poetry окружения..."
poetry install

# Запускаем миграции
echo "🗄️ Выполнение миграций базы данных..."
poetry run alembic upgrade head

# Запускаем приложение
echo "🎯 Запуск приложения..."
echo ""
echo "📱 Доступные URL:"
echo "   • Gradio UI: http://localhost:8000/"
echo "   • API Docs: http://localhost:8000/docs"
echo "   • Health: http://localhost:8000/api/health"
echo ""
echo "Для остановки нажмите Ctrl+C"
echo ""

poetry run uvicorn rag_crawl.main:app --host 0.0.0.0 --port 8000 --reload 