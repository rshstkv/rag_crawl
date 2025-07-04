# 🚀 План развертывания RAG Crawl на Azure

## 📋 Обзор

Этот план описывает развертывание RAG Crawl приложения на Azure с использованием **существующих ресурсов** без нарушения работы текущих приложений (`crawl4ai-dev` и `totchka-instance`).

## 🏗️ Архитектура развертывания

### 🔧 Используемые существующие ресурсы:

1. **Resource Group**: `davai_poigraem` (West Europe)
2. **Container Registry**: `crawl4aiacr6c07cdcc.azurecr.io` (Basic)
3. **Container App Environment**: `crawl4ai-env` (где уже работает `crawl4ai-dev`)
4. **Azure OpenAI**: `openai-totchka` (East US)

### 💡 Подход "Все в Docker" (экономный вариант):

- **Frontend**: Next.js в контейнере
- **Backend**: Python FastAPI в контейнере  
- **PostgreSQL**: В контейнере с persistent volume
- **Qdrant**: В контейнере с persistent volume
- **Reverse Proxy**: Nginx в контейнере для маршрутизации

## 🐳 Контейнерная архитектура

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

## 📁 Структура проекта для развертывания

```
├── deployment/
│   ├── dockerfiles/
│   │   ├── frontend.Dockerfile
│   │   ├── backend.Dockerfile
│   │   └── nginx.Dockerfile
│   ├── docker-compose.production.yml
│   ├── nginx.conf
│   └── init-scripts/
│       └── init-db.sql
├── .github/workflows/
│   └── deploy-azure.yml
└── azure/
    ├── containerapp.json
    └── deploy.sh
```

## 🚀 Этапы развертывания

### 1️⃣ Этап 1: Подготовка Docker образов

#### Frontend Dockerfile:
```dockerfile
FROM node:18-alpine AS builder
WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

FROM node:18-alpine AS runner
WORKDIR /app
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
USER nextjs
EXPOSE 3000
CMD ["node", "server.js"]
```

#### Backend Dockerfile:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN pip install poetry
RUN poetry config virtualenvs.create false
RUN poetry install --no-dev
COPY src/ ./src/
COPY alembic/ ./alembic/
COPY alembic.ini ./
EXPOSE 8000
CMD ["python", "-m", "rag_crawl.main"]
```

#### Nginx Dockerfile:
```dockerfile
FROM nginx:alpine
COPY deployment/nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
```

### 2️⃣ Этап 2: Конфигурация сервисов

#### docker-compose.production.yml:
```yaml
version: '3.8'
services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: rag_crawl
      POSTGRES_USER: rag_user
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped
    
  qdrant:
    image: qdrant/qdrant:latest
    volumes:
      - qdrant_data:/qdrant/storage
    environment:
      QDRANT__SERVICE__HTTP_PORT: 6333
    restart: unless-stopped
    
  backend:
    build:
      context: .
      dockerfile: deployment/dockerfiles/backend.Dockerfile
    environment:
      - DATABASE_URL=postgresql://rag_user:${POSTGRES_PASSWORD}@postgres:5432/rag_crawl
      - QDRANT_HOST=qdrant
      - QDRANT_PORT=6333
      - AZURE_OPENAI_API_KEY=${AZURE_OPENAI_API_KEY}
      - AZURE_OPENAI_ENDPOINT=${AZURE_OPENAI_ENDPOINT}
      - AZURE_OPENAI_CHAT_DEPLOYMENT=${AZURE_OPENAI_CHAT_DEPLOYMENT}
      - AZURE_OPENAI_EMBEDDING_DEPLOYMENT=${AZURE_OPENAI_EMBEDDING_DEPLOYMENT}
      - AZURE_OPENAI_CHAT_MODEL=${AZURE_OPENAI_CHAT_MODEL}
      - AZURE_OPENAI_EMBEDDING_MODEL=${AZURE_OPENAI_EMBEDDING_MODEL}
    depends_on:
      - postgres
      - qdrant
    restart: unless-stopped
    
  frontend:
    build:
      context: .
      dockerfile: deployment/dockerfiles/frontend.Dockerfile
    environment:
      - NEXT_PUBLIC_API_URL=http://backend:8000
    depends_on:
      - backend
    restart: unless-stopped
    
  nginx:
    build:
      context: .
      dockerfile: deployment/dockerfiles/nginx.Dockerfile
    ports:
      - "80:80"
    depends_on:
      - frontend
      - backend
    restart: unless-stopped

volumes:
  postgres_data:
  qdrant_data:
```

#### nginx.conf:
```nginx
events {
    worker_connections 1024;
}

http {
    upstream frontend {
        server frontend:3000;
    }
    
    upstream backend {
        server backend:8000;
    }
    
    server {
        listen 80;
        
        location /api/ {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
        
        location / {
            proxy_pass http://frontend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
    }
}
```

## 💰 Стоимость и экономия

### 📊 Оценка стоимости (месяц):
- **Container App**: ~$15-30 (с auto-scaling to 0)
- **Storage Account**: ~$5-10 
- **Container Registry**: ~$5 (Basic tier)
- **Суммарно**: ~$25-45/месяц

### 🎯 Экономия:
- **Auto-scaling to 0**: Приложение "засыпает" при отсутствии трафика
- **Shared infrastructure**: Использование существующего Container App Environment
- **No managed databases**: PostgreSQL и Qdrant в контейнерах
- **Single Container App**: Все сервисы в одном контейнере

## 🔒 Безопасность

### 🛡️ Меры безопасности:
1. **Secrets**: Все секреты хранятся в Container App secrets
2. **Environment Variables**: Конфиденциальные данные через secretRef
3. **Network**: Внутренние сервисы недоступны извне
4. **HTTPS**: Автоматический SSL через Azure
5. **Registry**: Приватный Container Registry

## 📋 Чек-лист развертывания

### ✅ Подготовка:
- [ ] Подготовить GitHub Secrets для CI/CD
- [ ] Создать Dockerfiles для всех сервисов
- [ ] Настроить nginx конфигурацию
- [ ] Подготовить production docker-compose

### ✅ Развертывание:
- [ ] Создать Storage Account и File Share
- [ ] Добавить storage к Container App Environment
- [ ] Собрать и загрузить Docker образы
- [ ] Создать Container App
- [ ] Настроить GitHub Actions

### ✅ Тестирование:
- [ ] Проверить доступность приложения
- [ ] Протестировать все API endpoints
- [ ] Проверить работу с базой данных
- [ ] Протестировать векторный поиск
- [ ] Проверить автоматический деплой

## 🚨 Важные замечания

### ⚠️ Безопасность существующих приложений:
1. **crawl4ai-dev**: Останется работать в том же environment без изменений
2. **totchka-instance**: Не будет затронут, продолжит работать
3. **Изоляция**: Новый Container App будет изолирован от существующих

### 🔄 Rollback план:
1. Сохранить предыдущую версию образа
2. Быстрый откат через `az containerapp update`
3. Восстановление из бэкапа данных

## 🎯 Следующие шаги

1. **Получить credentials для Container Registry**
2. **Создать GitHub Secrets**
3. **Создать Dockerfiles**
4. **Запустить deployment скрипт**
5. **Настроить CI/CD pipeline**

---

**Готово к реализации!** 🚀 