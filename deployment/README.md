# 🚀 Развертывание RAG Crawl на Azure

## 📋 Быстрый старт

### 1. Предварительные требования

- Docker Desktop
- Azure CLI
- Git
- Доступ к Azure Container Registry `crawl4aiacr6c07cdcc.azurecr.io`
- Доступ к Resource Group `davai_poigraem`

### 2. Переменные окружения

Создайте файл `.env.prod` в корне проекта со следующими переменными:

```bash
# PostgreSQL
POSTGRES_PASSWORD=your_secure_password

# Azure OpenAI
AZURE_OPENAI_API_KEY=your_api_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_CHAT_DEPLOYMENT=your_chat_deployment
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=your_embedding_deployment
AZURE_OPENAI_CHAT_MODEL=gpt-4
AZURE_OPENAI_EMBEDDING_MODEL=text-embedding-ada-002
AZURE_OPENAI_API_VERSION=2024-02-15-preview
```

### 3. Развертывание

```bash
# Авторизация в Azure
az login

# Развертывание (автоматически загружает .env.prod)
./azure/deploy.sh
```

## 🏗️ Архитектура

```
┌─────────────────────────────────────────────────────────────┐
│                    Azure Container App                     │
│                      rag-crawl-app                         │
├─────────────────────────────────────────────────────────────┤
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────┐ │
│ │   Nginx     │ │  Frontend   │ │   Backend   │ │  Data   │ │
│ │ (port 80)   │ │ (port 3000) │ │ (port 8000) │ │ Volume  │ │
│ └─────────────┘ └─────────────┘ └─────────────┘ └─────────┘ │
│ ┌─────────────┐ ┌─────────────┐                            │
│ │ PostgreSQL  │ │   Qdrant    │                            │
│ │ (port 5432) │ │ (port 6333) │                            │
│ └─────────────┘ └─────────────┘                            │
└─────────────────────────────────────────────────────────────┘
```

## 📁 Файлы развертывания

- `dockerfiles/` - Docker образы для каждого сервиса
- `docker-compose.production.yml` - Конфигурация для локального тестирования
- `nginx.conf` - Конфигурация reverse proxy
- `init-scripts/` - Скрипты инициализации БД
- `../azure/deploy.sh` - Скрипт развертывания на Azure
- `../azure/containerapp.json` - JSON конфигурация Container App

## 🔧 Локальное тестирование

```bash
# Сборка и запуск всех сервисов (с загрузкой .env.prod)
export $(cat .env.prod | grep -v ^# | xargs) && docker-compose -f deployment/docker-compose.production.yml up --build

# Только сборка
export $(cat .env.prod | grep -v ^# | xargs) && docker-compose -f deployment/docker-compose.production.yml build

# Остановка
export $(cat .env.prod | grep -v ^# | xargs) && docker-compose -f deployment/docker-compose.production.yml down -v
```

## 🔒 GitHub Secrets

Для автоматического развертывания настройте следующие секреты в репозитории:

```
AZURE_CREDENTIALS - JSON credentials для Azure
REGISTRY_USERNAME - Имя пользователя Container Registry
REGISTRY_PASSWORD - Пароль Container Registry
POSTGRES_PASSWORD - Пароль PostgreSQL
AZURE_OPENAI_API_KEY - API ключ Azure OpenAI
AZURE_OPENAI_ENDPOINT - Endpoint Azure OpenAI
AZURE_OPENAI_CHAT_DEPLOYMENT - Deployment chat модели
AZURE_OPENAI_EMBEDDING_DEPLOYMENT - Deployment embedding модели
AZURE_OPENAI_CHAT_MODEL - Имя chat модели
AZURE_OPENAI_EMBEDDING_MODEL - Имя embedding модели
AZURE_OPENAI_API_VERSION - Версия API
```

## 🛠️ Полезные команды

```bash
# Проверка статуса Container App
az containerapp show --name rag-crawl-app --resource-group davai_poigraem

# Получение URL приложения
az containerapp show --name rag-crawl-app --resource-group davai_poigraem --query properties.configuration.ingress.fqdn

# Просмотр логов
az containerapp logs show --name rag-crawl-app --resource-group davai_poigraem --follow

# Перезапуск приложения
az containerapp restart --name rag-crawl-app --resource-group davai_poigraem

# Обновление образа
az containerapp update --name rag-crawl-app --resource-group davai_poigraem --image crawl4aiacr6c07cdcc.azurecr.io/rag-crawl-nginx:latest
```

## 🐛 Отладка

### Проверка образов в реестре
```bash
az acr repository list --name crawl4aiacr6c07cdcc --output table
az acr repository show-tags --name crawl4aiacr6c07cdcc --repository rag-crawl-nginx --output table
```

### Локальная отладка
```bash
# Проверка сборки frontend
docker build -f deployment/dockerfiles/frontend.Dockerfile -t test-frontend .

# Проверка сборки backend
docker build -f deployment/dockerfiles/backend.Dockerfile -t test-backend .

# Проверка nginx
docker build -f deployment/dockerfiles/nginx.Dockerfile -t test-nginx .
```

## 🎯 Monitoring и производительность

- **Auto-scaling**: 0-3 реплики на основе HTTP трафика
- **Health checks**: Встроенные проверки работоспособности
- **Logs**: Централизованное логирование через Azure Monitor
- **Metrics**: Мониторинг CPU, памяти, сетевого трафика

## 📞 Поддержка

При возникновении проблем:

1. Проверьте логи Container App
2. Убедитесь, что все переменные окружения установлены
3. Проверьте доступность Container Registry
4. Убедитесь, что Container App Environment работает 