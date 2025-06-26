# RAG Crawl

RAG микросервис для индексации документов и диалогового интерфейса с современным Next.js фронтендом.

## 🚀 Особенности

- **Современный веб-интерфейс** на Next.js с shadcn/ui
- **RAG (Retrieval-Augmented Generation)** для умного поиска по документам
- **Векторное хранилище** на базе Qdrant для семантического поиска
- **Azure OpenAI** для эмбеддингов и генерации ответов
- **LlamaIndex** для обработки документов и RAG пайплайна
- **PostgreSQL** для хранения метаданных
- **FastAPI** для высокопроизводительного REST API
- **Docker Compose** для локальной разработки

## 🏗️ Архитектура

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Next.js       │    │   FastAPI       │    │   Qdrant        │
│   Frontend      │───▶│   Backend       │───▶│   Vector DB     │
│   (Port 3000)   │    │   (Port 8000)   │    │   (Port 6333)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   PostgreSQL    │
                       │   Metadata DB   │
                       │   (Port 5432)   │
                       └─────────────────┘
```

## 🛠️ Технологический стек

### Frontend
- **Next.js 15** - React фреймворк с App Router
- **TypeScript** - типизация
- **shadcn/ui** - современные UI компоненты
- **Tailwind CSS** - стилизация
- **Lucide Icons** - иконки

### Backend
- **Python 3.11+** с Poetry
- **FastAPI** - REST API фреймворк
- **LlamaIndex** - RAG пайплайн
- **SQLAlchemy** - ORM для PostgreSQL
- **Qdrant** - векторная база данных
- **Azure OpenAI** - эмбеддинги и LLM

## 🚀 Быстрый запуск

### 1. Клонирование репозитория

```bash
git clone <repository-url>
cd rag_crawl
```

### 2. Настройка переменных окружения

```bash
cp env.example .env
```

Заполните файл `.env` вашими настройками:

```env
# Azure OpenAI
AZURE_OPENAI_API_KEY=your_api_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2023-05-15
AZURE_OPENAI_EMBEDDING_MODEL=text-embedding-ada-002
AZURE_OPENAI_CHAT_MODEL=gpt-4

# Database
DATABASE_URL=postgresql://username:password@localhost:5432/rag_crawl

# Qdrant
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=optional_api_key

# Application
APP_HOST=0.0.0.0
APP_PORT=8000
LOG_LEVEL=INFO
```

### 3. Запуск с Docker Compose

```bash
# Запуск всех сервисов (PostgreSQL + Qdrant)
docker-compose up -d

# Ожидание запуска сервисов
sleep 10
```

### 4. Установка Python зависимостей

```bash
# Установка Poetry (если не установлен)
curl -sSL https://install.python-poetry.org | python3 -

# Установка зависимостей
poetry install
```

### 5. Миграции базы данных

```bash
poetry run alembic upgrade head
```

### 6. Запуск Backend API

```bash
poetry run python -m rag_crawl.main
```

API будет доступен на http://localhost:8000
Документация API: http://localhost:8000/docs

### 7. Установка Frontend зависимостей

```bash
cd frontend
npm install
```

### 8. Запуск Frontend

```bash
npm run dev
```

Frontend будет доступен на http://localhost:3000

## 📖 Использование

### Веб-интерфейс

1. Откройте http://localhost:3000
2. В правой панели загрузите документы (.txt, .pdf, .docx, .md)
3. Документы автоматически индексируются в векторную базу
4. Задавайте вопросы в чате - система найдет релевантную информацию
5. Управляйте документами через интерфейс

### API

Полная документация API доступна на http://localhost:8000/docs

Основные endpoints:
- `POST /api/chat` - отправка сообщений в чат
- `POST /api/documents/upload` - загрузка документов
- `GET /api/documents` - получение списка документов
- `DELETE /api/documents/{id}` - удаление документа

## 🔧 Разработка

### Архитектурные принципы

1. **Разделение ответственности**: Frontend и Backend полностью разделены
2. **Адаптивность API**: Легкая адаптация к изменениям API через типизированный клиент
3. **Компонентная архитектура**: Переиспользуемые React компоненты
4. **Типобезопасность**: TypeScript на фронтенде, Pydantic на бэкенде

### Структура проекта

```
rag_crawl/
├── frontend/              # Next.js приложение
│   ├── src/
│   │   ├── app/          # Next.js App Router
│   │   ├── components/   # React компоненты
│   │   ├── hooks/        # React хуки
│   │   └── lib/          # Утилиты и API клиент
│   └── package.json
├── src/rag_crawl/        # Python бэкенд
│   ├── api/              # FastAPI роуты
│   ├── services/         # Бизнес-логика
│   ├── database/         # SQLAlchemy модели
│   └── utils/            # Вспомогательные функции
├── alembic/              # Миграции БД
├── docker-compose.yml    # Docker сервисы
└── pyproject.toml        # Python зависимости
```

### Добавление новых функций

#### Backend

1. Создайте новые модели в `src/rag_crawl/database/models.py`
2. Добавьте бизнес-логику в `src/rag_crawl/services/`
3. Создайте API endpoints в `src/rag_crawl/api/`
4. Обновите схемы Pydantic

#### Frontend

1. Обновите типы в `frontend/src/lib/api.ts`
2. Добавьте новые методы в `ApiClient`
3. Создайте хуки для управления состоянием
4. Реализуйте UI компоненты

## 🧪 Тестирование

### Backend тесты

```bash
poetry run pytest
```

### Frontend тесты

```bash
cd frontend
npm run test
```

## 📦 Деплой

### Production сборка

```bash
# Backend
poetry build

# Frontend
cd frontend
npm run build
```

### Docker production

```bash
docker-compose -f docker-compose.prod.yml up -d
```

## 🤝 Вклад в проект

1. Форкните репозиторий
2. Создайте feature ветку
3. Внесите изменения
4. Добавьте тесты
5. Отправьте Pull Request

## 📄 Лицензия

MIT License

## 📞 Поддержка

- 📚 [Документация](./docs/)
- 🐛 [Issues](https://github.com/your-repo/issues)
- 💬 [Discussions](https://github.com/your-repo/discussions) 