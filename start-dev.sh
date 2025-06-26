#!/bin/bash

echo "🚀 Запуск RAG Crawl Development Environment"
echo "=========================================="

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция для проверки статуса команды
check_status() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ $1${NC}"
    else
        echo -e "${RED}❌ $1${NC}"
        exit 1
    fi
}

echo -e "${BLUE}📦 Запуск Docker сервисов...${NC}"
docker-compose up -d postgres qdrant
check_status "Docker сервисы запущены"

echo -e "${BLUE}⏳ Ожидание готовности сервисов...${NC}"
sleep 10

echo -e "${BLUE}🗄️ Применение миграций БД...${NC}"
poetry run alembic upgrade head
check_status "Миграции применены"

echo -e "${BLUE}🔧 Установка frontend зависимостей...${NC}"
cd frontend && npm install
check_status "Frontend зависимости установлены"

cd ..

echo -e "${GREEN}🎉 Готово! Запускайте сервисы:${NC}"
echo ""
echo -e "${YELLOW}Backend API:${NC}"
echo "  poetry run python -m rag_crawl.main"
echo "  Доступен на: http://localhost:8000"
echo "  API docs: http://localhost:8000/docs"
echo ""
echo -e "${YELLOW}Frontend:${NC}"
echo "  cd frontend && npm run dev"
echo "  Доступен на: http://localhost:3000"
echo ""
echo -e "${YELLOW}Для остановки Docker сервисов:${NC}"
echo "  docker-compose down"
echo "" 