# RAG Crawl Frontend

Современный веб-интерфейс для RAG Crawl на базе Next.js и shadcn/ui.

## Особенности

- 🚀 **Next.js 15** с App Router
- 🎨 **shadcn/ui** компоненты с Tailwind CSS
- 💬 **Чат интерфейс** для общения с документами
- 📁 **Загрузка документов** с визуальной обратной связью
- 📋 **Управление документами** со списком и удалением
- 🔄 **Адаптивная архитектура** для легкого изменения API
- 📱 **Адаптивный дизайн** для всех устройств

## Технологический стек

- **Next.js 15** - React фреймворк
- **TypeScript** - типизация
- **Tailwind CSS** - стилизация
- **shadcn/ui** - UI компоненты
- **Lucide Icons** - иконки
- **date-fns** - работа с датами

## Быстрый запуск

1. Установите зависимости:
   ```bash
   npm install
   ```

2. Настройте переменные окружения:
   ```bash
   cp .env.example .env.local
   ```

3. Запустите dev сервер:
   ```bash
   npm run dev
   ```

4. Откройте [http://localhost:3000](http://localhost:3000)

## Структура проекта

```
src/
├── app/                 # Next.js App Router
│   ├── globals.css     # Глобальные стили
│   ├── layout.tsx      # Основной layout
│   └── page.tsx        # Главная страница
├── components/         # React компоненты
│   ├── chat/          # Чат компоненты
│   ├── documents/     # Управление документами
│   └── ui/            # shadcn/ui компоненты
├── hooks/             # React хуки
│   ├── use-chat.ts    # Хук для чата
│   └── use-documents.ts # Хук для документов
└── lib/              # Утилиты
    ├── api.ts        # API клиент
    └── utils.ts      # Вспомогательные функции
```

## API Интеграция

Приложение использует адаптивную архитектуру API клиента:

### API Клиент (`src/lib/api.ts`)
- Типизированные запросы и ответы
- Централизованная обработка ошибок
- Легкая настройка базового URL

### Хуки для данных
- `useChat` - управление чатом и сообщениями
- `useDocuments` - загрузка и управление документами

### Адаптация к изменениям API

Для адаптации к изменениям API:

1. **Обновите типы** в `src/lib/api.ts`
2. **Измените endpoints** в `ApiClient` классе
3. **Обновите логику** в соответствующих хуках

## Переменные окружения

Создайте файл `.env.local` в папке `frontend/`:

```env
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000/api

# App Configuration
NEXT_PUBLIC_APP_NAME=RAG Crawl
NEXT_PUBLIC_APP_DESCRIPTION=Чат с документами на основе векторного поиска
```

### ⚠️ Важно: Настройка API URL

Убедитесь, что `NEXT_PUBLIC_API_URL` содержит корректный путь к API:

- ✅ Правильно: `http://localhost:8000/api` (с `/api`)
- ❌ Неправильно: `http://localhost:8000` (без `/api`)

Без правильного API URL фронтенд будет получать 404 ошибки при обращении к серверу.

## Разработка

### Добавление новых компонентов

```bash
npx shadcn@latest add [component-name]
```

### Стили и темы

Приложение использует Tailwind CSS с настроенной темой в `tailwind.config.ts`.

### Типизация

Все API интерфейсы описаны в TypeScript для безопасности типов.

## Производство

1. Соберите приложение:
   ```bash
   npm run build
   ```

2. Запустите production сервер:
   ```bash
   npm start
   ```

## Интеграция с Backend

Убедитесь, что backend API запущен на `http://localhost:8000` со следующими endpoints:

- `POST /api/chat` - отправка сообщений
- `POST /api/documents/upload` - загрузка документов
- `GET /api/documents` - получение списка документов
- `DELETE /api/documents/{id}` - удаление документа

## Лицензия

MIT
