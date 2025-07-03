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

# Проверяем, запущен ли Docker
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker не запущен. Запустите Docker Desktop и попробуйте снова.${NC}"
    exit 1
fi

# Создаем директорию для логов, если её нет
mkdir -p logs

# Функция для остановки всех процессов при выходе
cleanup() {
    echo -e "\n${YELLOW}⏹️ Остановка всех процессов...${NC}"
    # Убиваем все дочерние процессы
    pkill -P $$
    echo -e "${GREEN}✅ Процессы остановлены${NC}"
    echo -e "${YELLOW}ℹ️ Для остановки Docker контейнеров выполните:${NC}"
    echo -e "   docker-compose down"
    exit 0
}

# Регистрируем функцию очистки при выходе
trap cleanup SIGINT SIGTERM

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

echo -e "${GREEN}🚀 Запуск бэкенда и фронтенда...${NC}"

# Запускаем бэкенд в фоновом режиме
echo -e "${BLUE}🔥 Запуск бэкенда...${NC}"
poetry run uvicorn rag_crawl.main:app --host 0.0.0.0 --port 8000 --reload > logs/backend.log 2>&1 &
BACKEND_PID=$!

# Проверяем, что бэкенд запустился
sleep 3
if ps -p $BACKEND_PID > /dev/null; then
    echo -e "${GREEN}✅ Бэкенд запущен (PID: $BACKEND_PID)${NC}"
else
    echo -e "${RED}❌ Не удалось запустить бэкенд. Проверьте логи в logs/backend.log${NC}"
    exit 1
fi

# Запускаем фронтенд в фоновом режиме
echo -e "${BLUE}🔥 Запуск фронтенда...${NC}"
cd frontend && npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!

# Проверяем, что фронтенд запустился
sleep 5
if ps -p $FRONTEND_PID > /dev/null; then
    echo -e "${GREEN}✅ Фронтенд запущен (PID: $FRONTEND_PID)${NC}"
else
    echo -e "${RED}❌ Не удалось запустить фронтенд. Проверьте логи в logs/frontend.log${NC}"
    exit 1
fi

cd ..

echo -e "${GREEN}🎉 Среда разработки успешно запущена!${NC}"
echo -e "${BLUE}📱 Доступные URL:${NC}"
echo -e "   • Backend API: http://localhost:8000"
echo -e "   • API Docs: http://localhost:8000/docs"
echo -e "   • Frontend: http://localhost:3000"
echo ""
echo -e "${YELLOW}📊 Логи:${NC}"
echo -e "   • Бэкенд: logs/backend.log"
echo -e "   • Фронтенд: logs/frontend.log"
echo -e "   • Docker: docker-compose logs -f"
echo ""
echo -e "${YELLOW}⚠️ Для остановки всех процессов нажмите Ctrl+C${NC}"

# Показываем логи в реальном времени (можно выбрать один из вариантов)
echo -e "${BLUE}📋 Вывод логов бэкенда:${NC}"
tail -f logs/backend.log 