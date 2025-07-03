# План решения проблемы поиска и просмотра документов

## 🔍 Анализ проблемы

### Выявленные проблемы:
1. **КРИТИЧЕСКАЯ ПРОБЛЕМА**: Документы загружены в PostgreSQL, но не проиндексированы в Qdrant
   - PostgreSQL: 6 активных документов, 7 чанков
   - Qdrant коллекция `docs_v2`: 0 векторов (`points_count: 0`)
   - Результат: Empty response при поиске по "Ableton" (хотя в `LessonsEN.txt` есть информация про Ableton Live)

2. **Отсутствие диагностики**: Нет инструментов для просмотра содержимого документов в UI
3. **Отсутствие визуализации**: Нет возможности видеть, что скрывается за документами

### Файл с информацией про Ableton:
```
Название: LessonsEN.txt
Содержимое: "The Birds of Prey Ableton Live Pack contains 7 Instrument Racks..."
Статус: Загружен в PostgreSQL ✅, НЕ проиндексирован в Qdrant ❌
```

## 🎯 Цели решения

### 1. Исправить проблему индексации
- Наладить синхронизацию между PostgreSQL и Qdrant
- Переиндексировать существующие документы
- Добавить диагностику процесса индексации

### 2. Добавить возможность просмотра документов
- Показать содержимое документов в UI
- Добавить предварительный просмотр чанков
- Показать метаданные документов

### 3. Улучшить диагностику поиска
- Добавить отладочную информацию в API
- Показать score релевантности
- Добавить информацию о количестве найденных документов

## 📋 Подробный план реализации

### Этап 1: Исправление проблемы индексации (КРИТИЧЕСКИЙ)

#### 1.1 Диагностика текущего состояния
```bash
# Проверить состояние векторного хранилища
curl -s "http://localhost:6333/collections/docs_v2" | jq '.result.points_count'

# Проверить документы в PostgreSQL
psql -U rag_user -d rag_crawl -c "SELECT COUNT(*) FROM documents WHERE is_active = true;"
```

#### 1.2 Исправление процесса индексации
**Файл**: `src/rag_crawl/services/llama_service.py`

**Проблемные места для исправления:**
1. **Метод `upload_document`**: Проверить, что IngestionPipeline корректно сохраняет векторы в Qdrant
2. **Метод `_get_vector_store`**: Убедиться, что подключение к Qdrant работает
3. **Добавить логирование**: Для отслеживания процесса индексации

**Изменения:**
```python
# Добавить детальное логирование в upload_document
logger.info(f"📊 Начинается индексация документа: {title}")
logger.info(f"🔍 Vector store: {type(vector_store).__name__}")
logger.info(f"📝 Создано чанков: {len(nodes)}")

# Проверить, что векторы действительно сохранены
points_count_before = self._get_collection_points_count()
nodes = pipeline.run(documents=[llama_doc])
points_count_after = self._get_collection_points_count()
logger.info(f"✅ Векторы добавлены: {points_count_after - points_count_before}")
```

#### 1.3 Добавление методов переиндексации
**Новые методы в LlamaIndexService**:
```python
async def reindex_all_documents(self, namespace: Optional[str] = None) -> Dict[str, Any]:
    """Переиндексация всех документов в namespace."""
    # Получить все документы из PostgreSQL
    # Для каждого документа создать векторы заново
    # Очистить старые векторы, если есть
    # Создать новые векторы через IngestionPipeline

async def reindex_document(self, document_id: int) -> Dict[str, Any]:
    """Переиндексация одного документа."""
    # Получить документ по ID
    # Очистить старые векторы для этого документа
    # Создать новые векторы через IngestionPipeline
    
async def reindex_documents_batch(self, document_ids: List[int]) -> Dict[str, Any]:
    """Переиндексация группы документов."""
    # Получить документы по списку ID
    # Для каждого документа выполнить переиндексацию
    # Вернуть сводку по результатам
    
async def reload_document_content(self, document_id: int) -> Dict[str, Any]:
    """Перезагрузка содержимого документа из исходного файла."""
    # Найти исходный файл (если доступен)
    # Перечитать содержимое
    # Обновить в PostgreSQL
    # Переиндексировать в Qdrant
```

#### 1.4 Новые API endpoints для переиндексации
**Файл**: `src/rag_crawl/api/documents.py`
```python
@router.post("/reindex")
async def reindex_documents(
    namespace: Optional[str] = None,
    service: LlamaIndexService = Depends(get_llama_service)
):
    """Переиндексация всех документов в namespace."""
    result = await service.reindex_all_documents(namespace)
    return result

@router.post("/reindex-all")
async def reindex_all_documents(
    service: LlamaIndexService = Depends(get_llama_service)
):
    """Переиндексация всех документов во всех namespace."""
    result = await service.reindex_all_documents()
    return result

@router.post("/{document_id}/reindex")
async def reindex_single_document(
    document_id: int,
    service: LlamaIndexService = Depends(get_llama_service)
):
    """Переиндексация одного документа."""
    result = await service.reindex_document(document_id)
    return result

@router.post("/reindex-batch")
async def reindex_batch_documents(
    document_ids: List[int],
    service: LlamaIndexService = Depends(get_llama_service)
):
    """Переиндексация группы документов."""
    result = await service.reindex_documents_batch(document_ids)
    return result

@router.post("/{document_id}/reload")
async def reload_document_content(
    document_id: int,
    service: LlamaIndexService = Depends(get_llama_service)
):
    """Перезагрузка содержимого документа (если исходный файл изменился)."""
    result = await service.reload_document_content(document_id)
    return result
```

### Этап 2: Добавление просмотра документов в UI

#### 2.1 Расширение API для получения содержимого
**Файл**: `src/rag_crawl/api/documents.py`

**Новые endpoints:**
```python
@router.get("/{document_id}/content")
async def get_document_content(
    document_id: int,
    service: LlamaIndexService = Depends(get_llama_service)
):
    """Получить содержимое документа с чанками."""
    
@router.get("/{document_id}/chunks")
async def get_document_chunks(
    document_id: int,
    service: LlamaIndexService = Depends(get_llama_service)
):
    """Получить все чанки документа."""
```

#### 2.2 Расширение сервиса для получения содержимого
**Файл**: `src/rag_crawl/services/llama_service.py`

**Новые методы:**
```python
async def get_document_content(self, document_id: int) -> Dict[str, Any]:
    """Получить полное содержимое документа с чанками."""
    
async def get_document_chunks(self, document_id: int) -> List[Dict[str, Any]]:
    """Получить все чанки документа с метаданными."""
```

#### 2.3 Создание отдельной страницы управления документами
**Новая страница**: `frontend/src/app/documents/page.tsx`

**Функциональность:**
1. Табличное представление документов с колонками (используя Shadcn UI Table):
   - Название документа
   - Тип файла
   - Namespace  
   - Количество чанков
   - Дата создания
   - Статус индексации (Progress Bar)
   - Действия (DropdownMenu)

2. Групповые операции:
   - Выбор нескольких документов (Shadcn UI Checkbox)
   - Кнопка "Переиндексировать выбранные"
   - Кнопка "Удалить выбранные" (с AlertDialog подтверждения)
   - Кнопка "Экспорт выбранных"

3. Индивидуальные операции для каждого документа:
   - Кнопка "Просмотр" (открывает Sheet с содержимым)
   - Кнопка "Переиндексировать"
   - Кнопка "Перезагрузить" (reload content)
   - Кнопка "Удалить" (с AlertDialog подтверждения)

**Новые компоненты (используя Shadcn UI):**
- `DocumentsTable.tsx` - таблица документов (Table, Checkbox, DropdownMenu)
- `DocumentViewer.tsx` - для просмотра содержимого (Sheet, Tabs, ScrollArea)
- `DocumentChunksView.tsx` - для просмотра чанков (Card, Badge)
- `DocumentMetadataView.tsx` - для просмотра метаданных (Card, Separator)
- `DocumentActions.tsx` - панель действий (Button, AlertDialog)
- `BatchActions.tsx` - панель групповых операций (Button, Progress, Toast)

#### 2.4 Обновление навигации
**Файл**: `frontend/src/app/layout.tsx`

**Изменения:**
1. Добавить в главное меню ссылку "Управление документами"
2. Обновить главную страницу с табами: "Чат" / "Загрузка" / "Диагностика"
3. Убрать список документов из главной страницы

#### 2.5 Улучшение UX (используя Shadcn UI)
**Дополнительные функции:**
1. Поиск и фильтрация документов (Input, Select, Badge)
2. Сортировка по колонкам (встроенная в Table)
3. Пагинация для больших списков (Pagination)
4. Индикаторы статуса индексации (Progress, Badge)
5. Прогресс-бары для операций переиндексации (Progress, Toast)
6. Уведомления об успешных операциях (Toast)
7. Модальные диалоги подтверждения (AlertDialog)
8. Боковая панель для детального просмотра (Sheet)

### Этап 3: Улучшение диагностики поиска

#### 3.1 Расширение API ответов
**Файл**: `src/rag_crawl/api/chat.py`

**Изменения в `QueryResponse`:**
```python
class QueryResponse(BaseModel):
    response: str
    sources: List[Dict[str, Any]]
    debug_info: Optional[Dict[str, Any]] = None  # Новое поле
    total_documents: Optional[int] = None
    search_time_ms: Optional[float] = None
```

#### 3.2 Добавление debug информации
**Файл**: `src/rag_crawl/services/llama_service.py`

**Изменения в методе `query`:**
```python
async def query(self, question: str, namespace: str = "default") -> Dict[str, Any]:
    start_time = time.time()
    
    # Получить информацию о коллекции
    collection_info = self._get_collection_info()
    
    # Выполнить поиск
    response = query_engine.query(question)
    
    search_time = (time.time() - start_time) * 1000
    
    return {
        "response": str(response),
        "sources": sources,
        "debug_info": {
            "collection_points_count": collection_info.get("points_count", 0),
            "similarity_cutoff": 0.75,
            "search_time_ms": search_time,
            "namespace": namespace
        }
    }
```

#### 3.3 Обновление UI для показа debug информации
**Файл**: `frontend/src/components/chat/message-item.tsx`

**Изменения:**
1. Показать количество найденных документов
2. Показать время поиска
3. Показать score релевантности для каждого источника
4. Добавить кнопку "Подробности поиска"

### Этап 4: Добавление административных функций

#### 4.1 Новый API endpoint для диагностики
**Файл**: `src/rag_crawl/api/admin.py` (новый файл)

```python
@router.get("/diagnostics")
async def get_diagnostics():
    """Получить диагностическую информацию о системе."""
    
@router.post("/reindex-all")
async def reindex_all_documents():
    """Переиндексировать все документы."""
    
@router.get("/collection-info")
async def get_collection_info():
    """Получить информацию о Qdrant коллекции."""
```

#### 4.2 Добавление в главное меню
**Файл**: `frontend/src/app/layout.tsx`

**Изменения:**
1. Добавить пункт меню "Администрирование"
2. Добавить страницу с диагностикой
3. Добавить кнопки для переиндексации

## 🛠️ Техническая реализация

### Файлы для изменения:

#### Backend:
1. `src/rag_crawl/services/llama_service.py` - исправление индексации
2. `src/rag_crawl/api/documents.py` - новые endpoints
3. `src/rag_crawl/api/chat.py` - debug информация
4. `src/rag_crawl/api/admin.py` - новый файл для админки

#### Frontend:
1. `frontend/src/app/documents/page.tsx` - страница управления документами
2. `frontend/src/components/documents/documents-table.tsx` - таблица документов
3. `frontend/src/components/documents/document-viewer.tsx` - просмотр содержимого
4. `frontend/src/components/documents/document-actions.tsx` - панель действий
5. `frontend/src/components/documents/batch-actions.tsx` - групповые операции
6. `frontend/src/components/documents/document-chunks-view.tsx` - просмотр чанков
7. `frontend/src/components/documents/document-metadata-view.tsx` - просмотр метаданных
8. `frontend/src/components/chat/message-item.tsx` - debug информация
9. `frontend/src/app/page.tsx` - обновленные табы
10. `frontend/src/app/layout.tsx` - навигация
11. `frontend/src/lib/api.ts` - новые API методы

### Новые зависимости:
```json
// package.json
{
  "dependencies": {
    "react-syntax-highlighter": "^15.5.0",  // Для подсветки кода (опционально)
    "lucide-react": "^0.263.1"              // Иконки (уже используется)
  }
}
```

### Новые Shadcn UI компоненты:
```bash
# Добавить необходимые компоненты Shadcn UI
npx shadcn-ui@latest add table
npx shadcn-ui@latest add checkbox  
npx shadcn-ui@latest add select
npx shadcn-ui@latest add pagination
npx shadcn-ui@latest add progress
npx shadcn-ui@latest add tabs
npx shadcn-ui@latest add toast
npx shadcn-ui@latest add alert-dialog
npx shadcn-ui@latest add dropdown-menu
npx shadcn-ui@latest add sheet
```

### Примеры использования Shadcn UI компонентов:
```tsx
// Таблица документов
<Table>
  <TableHeader>
    <TableRow>
      <TableHead className="w-[50px]">
        <Checkbox />
      </TableHead>
      <TableHead>Название</TableHead>
      <TableHead>Тип</TableHead>
      <TableHead>Namespace</TableHead>
      <TableHead>Статус</TableHead>
      <TableHead>Действия</TableHead>
    </TableRow>
  </TableHeader>
  <TableBody>
    <TableRow>
      <TableCell><Checkbox /></TableCell>
      <TableCell>LessonsEN.txt</TableCell>
      <TableCell><Badge variant="secondary">txt</Badge></TableCell>
      <TableCell><Badge variant="outline">default</Badge></TableCell>
      <TableCell>
        <Progress value={100} className="w-[80px]" />
      </TableCell>
      <TableCell>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost">•••</Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuItem>Просмотр</DropdownMenuItem>
            <DropdownMenuItem>Переиндексировать</DropdownMenuItem>
            <DropdownMenuItem>Удалить</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </TableCell>
    </TableRow>
  </TableBody>
</Table>

// Просмотр документа
<Sheet>
  <SheetContent className="sm:max-w-[800px]">
    <SheetHeader>
      <SheetTitle>Просмотр документа</SheetTitle>
    </SheetHeader>
    <Tabs defaultValue="content" className="w-full">
      <TabsList>
        <TabsTrigger value="content">Содержимое</TabsTrigger>
        <TabsTrigger value="chunks">Чанки</TabsTrigger>
        <TabsTrigger value="metadata">Метаданные</TabsTrigger>
      </TabsList>
      <TabsContent value="content">
        <ScrollArea className="h-[500px]">
          {documentContent}
        </ScrollArea>
      </TabsContent>
    </Tabs>
  </SheetContent>
</Sheet>
```

## 🔧 Порядок реализации

### Приоритет 1 (КРИТИЧЕСКИЙ): Исправление индексации
1. Исправить `upload_document` в `llama_service.py`
2. Добавить метод переиндексации
3. Создать API endpoint для переиндексации
4. Переиндексировать существующие документы

### Приоритет 2: Просмотр документов
1. Создать API для получения содержимого
2. Создать компонент `DocumentViewer`
3. Интегрировать в `DocumentList`

### Приоритет 3: Диагностика поиска
1. Добавить debug информацию в API
2. Обновить UI для отображения debug информации

### Приоритет 4: Административные функции
1. Создать страницу администрирования
2. Добавить мониторинг состояния системы

## 🧪 Тестирование

### Тест 1: Проверка индексации
```bash
# После исправления проверить, что векторы создаются
curl -s "http://localhost:6333/collections/docs_v2" | jq '.result.points_count'
# Должно быть > 0
```

### Тест 2: Переиндексация существующих документов
```bash
# Переиндексировать все документы
curl -X POST "http://localhost:8000/api/documents/reindex-all" \
  -H "Content-Type: application/json"

# Переиндексировать документы в конкретном namespace
curl -X POST "http://localhost:8000/api/documents/reindex" \
  -H "Content-Type: application/json" \
  -d '{"namespace": "default"}'

# Переиндексировать один документ
curl -X POST "http://localhost:8000/api/documents/5/reindex" \
  -H "Content-Type: application/json"
```

### Тест 3: Проверка поиска
```bash
# Запрос через API
curl -X POST "http://localhost:8000/api/chat/query" \
  -H "Content-Type: application/json" \
  -d '{"question": "Ableton", "namespace": "default"}'
# Должен вернуть информацию из LessonsEN.txt
```

### Тест 4: Проверка просмотра документов
1. Открыть страницу управления документами
2. Проверить отображение в табличном виде
3. Нажать "Просмотр" на документе
4. Проверить, что отображается содержимое

### Тест 5: Групповые операции
1. Выбрать несколько документов в таблице
2. Нажать "Переиндексировать выбранные"
3. Проверить, что все документы переиндексированы
4. Проверить поиск по переиндексированным документам

## 📊 Ожидаемые результаты

После реализации плана:
1. ✅ Поиск по "Ableton" вернет информацию из `LessonsEN.txt`
2. ✅ Можно будет просматривать содержимое документов в UI
3. ✅ Будет видно debug информацию о поиске
4. ✅ Будет возможность переиндексировать документы
5. ✅ Будет диагностика состояния системы

## 🚀 Дальнейшие улучшения

После основной реализации можно добавить:
1. Полнотекстовый поиск по содержимому документов
2. Фильтрацию по типам документов  
3. Экспорт содержимого документов
4. Аналитику по использованию документов
5. Автоматическую переиндексацию при изменении документов
6. Drag & Drop для загрузки документов
7. Bulk операции для массовых изменений
8. Резервное копирование и восстановление индексов

## 📋 Резюме обновленного плана

### Ключевые изменения:
1. **Использование Shadcn UI**: Полная интеграция с существующими компонентами
2. **Отдельная страница управления документами**: Вместо встроенного списка
3. **Групповые операции**: Возможность работать с несколькими документами одновременно
4. **Улучшенная переиндексация**: Индивидуальная, групповая и полная переиндексация
5. **Богатый интерфейс**: Таблицы, модальные окна, прогресс-бары, уведомления

### Приоритеты реализации:
1. **КРИТИЧЕСКИЙ**: Исправление индексации + переиндексация существующих документов
2. **ВЫСОКИЙ**: Создание страницы управления документами с Shadcn UI
3. **СРЕДНИЙ**: Добавление debug информации и диагностики
4. **НИЗКИЙ**: Дополнительные функции и улучшения UX 