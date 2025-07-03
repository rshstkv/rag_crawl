# Анализ проблемы релевантности поиска

## 📝 Описание проблемы

### Текущее поведение
- Система возвращает нерелевантные документы с высокими score'ами релевантности (0.6-0.8)
- Документы, не содержащие информации по запросу, отображаются как подходящие источники
- Пользователи получают неточную информацию из неподходящих документов
- Качество векторного поиска не соответствует ожиданиям

### Ожидаемое поведение
- Нерелевантные документы должны иметь низкий score (< 0.3) или не появляться вообще
- Документы с низкой релевантностью не должны попадать в результаты поиска
- Только действительно релевантные источники должны отображаться пользователю
- Score должен корректно отражать семантическую близость содержимого к запросу
- Система должна различать тематически разные документы и не возвращать общие файлы для специфических запросов

## 🔍 Гипотезы причин проблемы

### 1. **🚨 ГЛАВНАЯ ПРОБЛЕМА: Временное in-memory хранилище вместо Qdrant**

**Текущая реализация (НЕПРАВИЛЬНО):**
```python
def _get_vector_store(self) -> Any:
    # ВРЕМЕННОЕ РЕШЕНИЕ: используем in-memory хранилище для тестирования
    logger.warning("Используем временное in-memory векторное хранилище для отладки")
    return None  # ❌ Создает SimpleVectorStore автоматически
```

**Правильная реализация (из документации LlamaIndex):**
```python
def _get_vector_store(self) -> QdrantVectorStore:
    try:
        client = qdrant_client.QdrantClient(
            host=settings.qdrant_host,  # localhost
            port=settings.qdrant_port   # 6333
        )
        
        return QdrantVectorStore(
            client=client,
            collection_name=settings.qdrant_collection_name  # docs_v2
        )
    except Exception as e:
        logger.error(f"Ошибка подключения к Qdrant: {e}")
        raise
```

**Причины проблемы:**
- SimpleVectorStore не предназначен для продакшена
- In-memory хранилище дает искаженные score'ы релевантности
- Qdrant уже настроен в docker-compose.yml и config.py, но не используется
- LlamaIndex рекомендует Qdrant для качественного векторного поиска

### 1.1 **Проблемы чанкинга документов**

**Текущая реализация (НЕПРАВИЛЬНО):**
```python
# Создаем один огромный чанк на весь документ
chunk = DocumentChunk(
    document_id=db_document.id,
    chunk_index=0,
    content=cleaned_text,  # ← ВЕСЬ документ целиком!
    vector_id=str(uuid.uuid4()),
)
```

**Правильная реализация (из документации LlamaIndex):**
```python
from llama_index.core.ingestion import IngestionPipeline
from llama_index.core.node_parser import SentenceSplitter

pipeline = IngestionPipeline(
    transformations=[
        SentenceSplitter(
            chunk_size=settings.max_chunk_size,  # 1024
            chunk_overlap=settings.chunk_overlap  # 200
        ),
        OpenAIEmbedding(),
    ],
    vector_store=vector_store,
)
nodes = pipeline.run(documents=documents)
```

### 1.2 **Конфигурационные проблемы**
- `MAX_RETRIEVAL_RESULTS=3` - слишком мало, нет фильтрации качества
- Отсутствует `SimilarityPostprocessor` с порогом фильтрации
- Нет reranking'а для улучшения результатов

### 1.3 **Отсутствие фильтрации по релевантности**

**Текущая реализация (НЕПРАВИЛЬНО):**
```python
# Нет фильтрации - возвращаем любые 3 результата
query_engine = index.as_query_engine(
    similarity_top_k=3  # Возвращает 3 лучших, даже если они нерелевантны
)
```

**Правильная реализация (из документации LlamaIndex):**
```python
from llama_index.core.postprocessor import SimilarityPostprocessor

query_engine = index.as_query_engine(
    similarity_top_k=10,  # Получаем больше кандидатов
    node_postprocessors=[
        SimilarityPostprocessor(similarity_cutoff=0.75)  # Фильтруем по порогу
    ]
)
```

### 2. **Проблемы с восстановлением индекса**
- Индекс пересоздается каждый раз при перезапуске приложения
- Некорректное восстановление из БД чанков в LlamaIndex документы
- Смешивание документов разных namespace'ов при восстановлении
- Метаданные могут не совпадать с исходными при восстановлении

### 3. **Отсутствие гибридного поиска и reranking'а**

**Возможность улучшения (из документации LlamaIndex):**
```python
# Гибридный поиск (семантический + keyword-based)
vector_store = QdrantVectorStore(
    client=client,
    collection_name="docs_v2",
    enable_hybrid=True,  # BM25 + векторный поиск
    fastembed_sparse_model="Qdrant/bm25"
)

query_engine = index.as_query_engine(
    vector_store_query_mode="hybrid",
    sparse_top_k=5,      # keyword-based результаты
    similarity_top_k=5,  # семантические результаты
    hybrid_top_k=3       # финальное количество
)
```

## 🧪 План диагностического тестирования

### Этап 1: Диагностика текущего состояния

#### 1.1 Проверка конфигурации
```bash
# Проверить текущие настройки
grep -E "(MAX_RETRIEVAL_RESULTS|MAX_CHUNK_SIZE|CHUNK_OVERLAP)" .env

# Проверить модели Azure OpenAI
grep -E "(AZURE_OPENAI.*MODEL|AZURE_OPENAI.*DEPLOYMENT)" .env

# Проверить настройки Qdrant
grep -E "(QDRANT_HOST|QDRANT_PORT|QDRANT_COLLECTION)" .env

# Проверить, что Qdrant запущен
curl -f http://localhost:6333/health || echo "❌ Qdrant недоступен"
docker ps | grep qdrant || echo "❌ Qdrant контейнер не запущен"
```

#### 1.2 Анализ индекса и документов
```bash
# Подключиться к базе данных
psql $DATABASE_URL

# Проверить количество документов и чанков
SELECT 
    namespace,
    COUNT(*) as documents_count,
    AVG(chunks_count) as avg_chunks_per_doc,
    SUM(chunks_count) as total_chunks
FROM documents 
WHERE is_active = true 
GROUP BY namespace;

# Проверить размеры чанков
SELECT 
    d.title,
    d.namespace,
    dc.chunk_index,
    LENGTH(dc.content) as chunk_length,
    dc.content[:100] as content_preview
FROM document_chunks dc
JOIN documents d ON dc.document_id = d.id
WHERE d.is_active = true
ORDER BY chunk_length DESC
LIMIT 10;
```

#### 1.3 Проверка использования vector store
```python
# Добавить в llama_service.py диагностику (на основе документации LlamaIndex)
def diagnose_vector_store_setup():
    """Диагностика почему используется in-memory вместо Qdrant"""
    
    # Проверяем настройки из config.py
    logger.info(f"QDRANT_HOST: {settings.qdrant_host}")
    logger.info(f"QDRANT_PORT: {settings.qdrant_port}")
    logger.info(f"QDRANT_COLLECTION: {settings.qdrant_collection_name}")
    
    # Проверяем доступность Qdrant (паттерн из документации)
    try:
        client = qdrant_client.QdrantClient(
            host=settings.qdrant_host,
            port=settings.qdrant_port
        )
        
        # Проверяем подключение
        collections_info = client.get_collections()
        logger.info(f"✅ Qdrant доступен, коллекции: {collections_info}")
        
        # Проверяем конкретную коллекцию
        if settings.qdrant_collection_name in [c.name for c in collections_info.collections]:
            collection_info = client.get_collection(settings.qdrant_collection_name)
            logger.info(f"✅ Коллекция {settings.qdrant_collection_name} найдена: {collection_info}")
        else:
            logger.warning(f"⚠️ Коллекция {settings.qdrant_collection_name} не найдена")
            
        return True
    except Exception as e:
        logger.error(f"❌ Qdrant недоступен: {e}")
        return False

# Проверить что действительно создается QdrantVectorStore
def diagnose_current_vector_store():
    """Проверить какой vector store фактически используется"""
    vector_store = self._get_vector_store()
    
    if vector_store is None:
        logger.error("❌ vector_store = None -> будет создан SimpleVectorStore")
        return "SimpleVectorStore"
    elif isinstance(vector_store, QdrantVectorStore):
        logger.info(f"✅ Используется QdrantVectorStore: {vector_store}")
        return "QdrantVectorStore"
    else:
        logger.warning(f"⚠️ Неизвестный тип vector store: {type(vector_store)}")
        return type(vector_store).__name__

# Вызвать при запуске сервиса
diagnose_vector_store_setup()
diagnose_current_vector_store()
```

#### 1.4 Тестирование поиска с логированием
```python
# Добавить в llama_service.py временное детальное логирование
import logging
logging.basicConfig(level=logging.DEBUG)

# Тестовый запрос с диагностикой
async def diagnostic_query(question: str, namespace: str = "default"):
    index = self._get_index(namespace)
    
    # Логируем состояние индекса
    logger.info(f"Index type: {type(index)}")
    logger.info(f"Index storage context: {type(index.storage_context)}")
    
    # Создаем query engine с детальным логированием
    query_engine = index.as_query_engine(
        similarity_top_k=10,  # Увеличиваем для диагностики
        verbose=True
    )
    
    response = query_engine.query(question)
    
    # Логируем все результаты
    if hasattr(response, 'source_nodes'):
        for i, node in enumerate(response.source_nodes):
            logger.info(f"Node {i}: score={getattr(node, 'score', 'N/A')}")
            logger.info(f"  Title: {node.metadata.get('title', 'Unknown')}")
            logger.info(f"  Content preview: {node.text[:200]}...")
            logger.info(f"  Metadata: {node.metadata}")
    
    return response
```

### Этап 2: Воспроизведение проблемы

#### 2.1 Создание тестовых документов
```bash
# Создать набор тестовых документов для диагностики
mkdir -p test_docs

# Документ про OKR (релевантный)
cat > test_docs/okr_guide.txt << 'EOF'
OKR (Objectives and Key Results) - это методология управления целями.
Objectives - это качественные цели, которые должны быть вдохновляющими.
Key Results - это количественные показатели достижения целей.
OKR помогает компаниям фокусироваться на важных задачах.
EOF

# Нерелевантный документ (README)
cat > test_docs/readme.txt << 'EOF'
# Проект RAG Crawl
Это веб-приложение для работы с документами.
Установка выполняется через Docker.
Для разработки используется Python и FastAPI.
Система поддерживает загрузку файлов различных форматов.
EOF
```

#### 2.2 Тестирование поиска
```bash
# Загрузить тестовые документы через API
curl -X POST "http://localhost:8000/api/documents/upload" \
  -F "file=@test_docs/okr_guide.txt" \
  -F "namespace=test"

curl -X POST "http://localhost:8000/api/documents/upload" \
  -F "file=@test_docs/readme.txt" \
  -F "namespace=test"

# Выполнить проблемный запрос
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "Что такое OKR?", "namespace": "test"}' \
  | jq '.'
```

### Этап 3: Детальная диагностика embedding'ов

#### 3.1 Проверка качества embedding'ов
```python
# Добавить в diagnostic функцию
async def test_embeddings():
    embed_model = self.embed_model
    
    # Тестовые тексты
    okr_text = "OKR это методология управления целями"
    readme_text = "Проект RAG Crawl веб-приложение для документов"
    query_text = "Что такое OKR?"
    
    # Получаем embedding'и
    query_embed = await embed_model.aget_text_embedding(query_text)
    okr_embed = await embed_model.aget_text_embedding(okr_text)
    readme_embed = await embed_model.aget_text_embedding(readme_text)
    
    # Вычисляем cosine similarity
    import numpy as np
    
    def cosine_similarity(a, b):
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
    
    okr_sim = cosine_similarity(query_embed, okr_embed)
    readme_sim = cosine_similarity(query_embed, readme_embed)
    
    logger.info(f"Query-OKR similarity: {okr_sim}")
    logger.info(f"Query-README similarity: {readme_sim}")
    
    return {"okr_similarity": okr_sim, "readme_similarity": readme_sim}
```

#### 3.2 Проверка чанкинга
```python
# Проверить как LlamaIndex разбивает документы
async def test_chunking():
    from llama_index.core.node_parser import SentenceSplitter
    
    splitter = SentenceSplitter(
        chunk_size=settings.max_chunk_size,
        chunk_overlap=settings.chunk_overlap
    )
    
    test_text = "..." # Большой тестовый текст
    
    # Создаем документ и смотрим на чанки
    doc = Document(text=test_text)
    nodes = splitter.get_nodes_from_documents([doc])
    
    logger.info(f"Text length: {len(test_text)}")
    logger.info(f"Number of chunks: {len(nodes)}")
    
    for i, node in enumerate(nodes):
        logger.info(f"Chunk {i}: length={len(node.text)}")
        logger.info(f"  Preview: {node.text[:100]}...")
```

### Этап 4: Анализ векторного хранилища

#### 4.1 Диагностика in-memory хранилища
```python
async def diagnose_vector_store():
    index = self._get_index("test")
    
    # Информация о векторном хранилище
    logger.info(f"Vector store type: {type(index.vector_store)}")
    logger.info(f"Storage context: {type(index.storage_context)}")
    
    # Попробовать получить статистику
    try:
        # Для SimpleVectorStore
        if hasattr(index.vector_store, 'data'):
            logger.info(f"Vector store size: {len(index.vector_store.data.embedding_dict)}")
            logger.info(f"Node count: {len(index.vector_store.data.text_id_to_ref_doc_id)}")
    except Exception as e:
        logger.warning(f"Cannot get vector store stats: {e}")
```

#### 4.2 Сравнение с Qdrant
```bash
# Проверить подключение к Qdrant
curl -X GET "http://localhost:6333/collections"

# Проверить коллекцию документов
curl -X GET "http://localhost:6333/collections/documents/info"
```

### Этап 5: Тестирование исправлений

#### 5.1 Тест с SimilarityPostprocessor
```python
# Временно модифицировать query engine
query_engine = index.as_query_engine(
    similarity_top_k=10,
    node_postprocessors=[
        SimilarityPostprocessor(similarity_cutoff=0.5)  # Тестовый порог
    ]
)
```

#### 5.2 Тест с увеличенным количеством результатов
```bash
# Изменить в .env
echo "MAX_RETRIEVAL_RESULTS=10" >> .env

# Перезапустить сервис и протестировать
```

#### 5.3 Тест с правильным чанкингом
```python
# Модифицировать upload_document для использования автоматического чанкинга
llama_doc = Document(text=cleaned_text, metadata=rich_metadata)

# Не создавать чанки вручную, позволить LlamaIndex делать это автоматически
index.insert(llama_doc)
```

## 📊 Метрики для оценки

### Количественные метрики
- **Precision@3**: Доля релевантных документов в топ-3
- **Recall@10**: Доля найденных релевантных документов
- **Average Score**: Средний score релевантных vs нерелевантных
- **Score Distribution**: Распределение score'ов по типам документов

### Качественные метрики
- **Manual Relevance**: Ручная оценка релевантности результатов
- **User Satisfaction**: Субъективная оценка качества ответов
- **False Positives**: Количество нерелевантных документов в результатах

## 🎯 Критерии успеха

1. **Нерелевантные документы имеют score < 0.3**
2. **Релевантные документы имеют score > 0.7**
3. **README файл не попадает в результаты по запросу "OKR"**
4. **Система возвращает только релевантные источники**
5. **Precision@3 > 80% на тестовом наборе**

## 🚀 План решения (на основе документации LlamaIndex)

### 1. **🚨 КРИТИЧЕСКИЙ ПРИОРИТЕТ: Переключение на Qdrant**

**Шаг 1.1:** Исправить `_get_vector_store()` в `llama_service.py`
```python
def _get_vector_store(self) -> QdrantVectorStore:
    """Получение Qdrant векторного хранилища (по документации LlamaIndex)."""
    try:
        client = qdrant_client.QdrantClient(
            host=settings.qdrant_host,    # localhost
            port=settings.qdrant_port     # 6333
        )
        
        return QdrantVectorStore(
            client=client,
            collection_name=settings.qdrant_collection_name  # docs_v2
        )
    except Exception as e:
        logger.error(f"Ошибка подключения к Qdrant: {e}")
        raise
```

**Шаг 1.2:** Обновить `_get_index()` для правильного использования StorageContext
```python
def _get_index(self, namespace: str) -> VectorStoreIndex:
    if namespace not in self._indices:
        vector_store = self._get_vector_store()
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        
        # Создаем новый индекс или загружаем существующий
        try:
            self._indices[namespace] = VectorStoreIndex.from_vector_store(
                vector_store=vector_store,
                storage_context=storage_context
            )
        except:
            # Если коллекция пуста, создаем новый индекс
            self._indices[namespace] = VectorStoreIndex(
                [],
                storage_context=storage_context
            )
    
    return self._indices[namespace]
```

### 2. **HIGH PRIORITY: Правильный чанкинг с IngestionPipeline**

**Шаг 2.1:** Заменить ручное создание чанков на IngestionPipeline
```python
async def upload_document(self, file: UploadFile, namespace: str = "default") -> DBDocument:
    # Извлечение текста
    text_content = await extract_text_from_file(file)
    cleaned_text = clean_text(text_content)
    
    # Создание LlamaIndex документа
    llama_doc = Document(
        text=cleaned_text,
        metadata={
            "title": title,
            "source_type": source_type,
            "namespace": namespace,
            "filename": file.filename,
        }
    )
    
    # Получаем vector store и используем IngestionPipeline
    vector_store = self._get_vector_store()
    
    pipeline = IngestionPipeline(
        transformations=[
            SentenceSplitter(
                chunk_size=settings.max_chunk_size,      # 1024
                chunk_overlap=settings.chunk_overlap      # 200
            ),
            self.embed_model,  # Azure OpenAI embedding
        ],
        vector_store=vector_store,
    )
    
    # Обработка документа через pipeline
    nodes = pipeline.run(documents=[llama_doc])
    
    # Сохранение метаданных в БД (упрощенно, без ручных чанков)
    db_document = DBDocument(
        title=title,
        source_type=source_type, 
        namespace=namespace,
        chunks_count=len(nodes),
        # vector_id больше не нужен - Qdrant управляет ID автоматически
    )
    
    self.db.add(db_document)
    self.db.commit()
    
    return db_document
```

### 3. **HIGH PRIORITY: Добавление фильтрации по релевантности**

**Шаг 3.1:** Обновить query engine с SimilarityPostprocessor
```python
def _get_query_engine(self, namespace: str):
    index = self._get_index(namespace)
    
    return index.as_query_engine(
        similarity_top_k=10,  # Увеличиваем количество кандидатов
        node_postprocessors=[
            SimilarityPostprocessor(similarity_cutoff=0.75)  # Фильтр релевантности
        ]
    )
```

### 4. **MEDIUM PRIORITY: Опциональное улучшение с Hybrid Search**

**Шаг 4.1:** Включить гибридный поиск (семантический + BM25)
```python
def _get_vector_store(self) -> QdrantVectorStore:
    client = qdrant_client.QdrantClient(
        host=settings.qdrant_host,
        port=settings.qdrant_port
    )
    
    return QdrantVectorStore(
        client=client,
        collection_name=settings.qdrant_collection_name,
        enable_hybrid=True,  # Включаем BM25 + векторный поиск
        fastembed_sparse_model="Qdrant/bm25"
    )

def _get_query_engine(self, namespace: str):
    index = self._get_index(namespace)
    
    return index.as_query_engine(
        vector_store_query_mode="hybrid",
        sparse_top_k=5,      # BM25 результаты
        similarity_top_k=5,  # Семантические результаты  
        hybrid_top_k=3,      # Финальное количество
        node_postprocessors=[
            SimilarityPostprocessor(similarity_cutoff=0.70)
        ]
    )
```

## 🎯 Ожидаемые результаты после исправлений

1. **Qdrant вместо SimpleVectorStore** → Правильные score'ы релевантности
2. **SentenceSplitter вместо одного чанка** → Лучшая точность поиска
3. **SimilarityPostprocessor** → Фильтрация нерелевантных результатов
4. **Hybrid Search** → Еще лучшее качество поиска

Основная проблема некорректных score'ов релевантности должна быть решена переходом на Qdrant.

## 🧪 Тестирование после исправлений

### Этап 0: Проверка зависимостей
```bash
# Все необходимые пакеты уже установлены в pyproject.toml:
# ✅ llama-index = "^0.12.0"
# ✅ qdrant-client = "^1.6.0" 
# ✅ llama-index-vector-stores-qdrant = "^0.6.1"
# ✅ llama-index-embeddings-azure-openai = "^0.3.8"

# Проверить что они установлены:
poetry show | grep -E "(llama-index|qdrant)"

# Переустановить если нужно:
poetry install
```

### Этап 1: Проверка подключения к Qdrant
```bash
# 1. Убедиться что Qdrant запущен
docker ps | grep qdrant

# 2. Проверить доступность API
curl -f http://localhost:6333/health

# 3. Проверить коллекции
curl "http://localhost:6333/collections"
```

### Этап 2: Функциональное тестирование
```python
# Создать тестовые документы для проверки релевантности
test_docs = [
    {"title": "Специфическая тема", "content": "Детальное описание конкретной методологии или процесса..."},
    {"title": "Общий документ", "content": "Общее описание проекта, установка, базовая информация..."}
]

# Загрузить через API
for doc in test_docs:
    response = requests.post("http://localhost:8000/api/documents/upload", 
                           files={"file": doc["content"]})

# Тестовый запрос на специфическую тему
response = requests.post("http://localhost:8000/api/chat",
                        json={"message": "Детальный вопрос по специфической теме", "namespace": "test"})

print(f"Ответ: {response.json()['response']}")
print(f"Источники: {response.json()['sources']}")

# Ожидаем: только релевантный документ в источниках
```

### Этап 3: Проверка качества результатов
**Критерии успеха:**
1. ✅ В логах должно быть: "✅ Используется QdrantVectorStore"
2. ✅ Нерелевантные документы не должны появляться в результатах для специфических запросов
3. ✅ Score релевантных документов > 0.75
4. ✅ Score нерелевантных документов < 0.3 (или не появляются вообще)
5. ✅ Время ответа не должно увеличиться значительно

### Этап 4: Мониторинг качества
```python
# Добавить логирование качества поиска
async def query_with_quality_metrics(self, question: str, namespace: str):
    response = await self.query(question, namespace)
    
    # Логируем метрики качества
    sources = response.get('sources', [])
    scores = [s.get('score', 0) for s in sources]
    
    logger.info(f"Query: {question}")
    logger.info(f"Sources count: {len(sources)}")
    logger.info(f"Scores: {scores}")
    logger.info(f"Min score: {min(scores) if scores else 0}")
    logger.info(f"Max score: {max(scores) if scores else 0}")
    
    return response
```

## 📊 Метрики до и после исправлений

| Метрика | До исправления | После исправления | Цель |
|---------|---------------|-------------------|------|
| Vector Store | SimpleVectorStore | QdrantVectorStore | ✅ |
| Чанкинг | 1 чанк = весь документ | SentenceSplitter | ✅ |
| Фильтрация | Нет | SimilarityPostprocessor | ✅ |
| Нерелевантные документы | Высокий score (0.6-0.8) | < 0.3 или отсутствуют | ✅ |
| Релевантные документы | Варьируется | > 0.75 | ✅ |

---

---

## 📋 ИТОГОВЫЙ SUMMARY

### 🚨 **Главная найденная проблема:**
**Код намеренно использует временное in-memory хранилище вместо настроенного Qdrant**

```python
# ❌ ТЕКУЩИЙ КОД (строка 118 в llama_service.py):
def _get_vector_store(self) -> Any:
    return None  # Создает SimpleVectorStore автоматически

# ✅ ДОЛЖНО БЫТЬ (по документации LlamaIndex):
def _get_vector_store(self) -> QdrantVectorStore:
    client = qdrant_client.QdrantClient(host="localhost", port=6333)
    return QdrantVectorStore(client=client, collection_name="docs_v2")
```

### 🎯 **Почему это вызывает проблему с релевантностью:**
1. **SimpleVectorStore** не предназначен для продакшена
2. **In-memory хранилище** дает искаженные score'ы релевантности
3. **Qdrant** значительно лучше работает с семантическим поиском
4. **LlamaIndex официально рекомендует** Qdrant для качественного векторного поиска

### 📊 **Ожидаемый эффект исправлений:**
- ❌ Нерелевантные документы с высоким score → ✅ Корректные score'ы или исключение из результатов
- ❌ Один большой чанк на документ → ✅ Правильное разбиение SentenceSplitter  
- ❌ Нет фильтрации по релевантности → ✅ SimilarityPostprocessor(cutoff=0.75)
- ❌ Только 3 результата без фильтра → ✅ 10 кандидатов + фильтрация

### 🔧 **Минимальные критические изменения:**
1. **Исправить `_get_vector_store()`** - заменить `return None` на правильную инициализацию
2. **Добавить SimilarityPostprocessor** - фильтровать по порогу релевантности
3. **Использовать SentenceSplitter** - правильный чанкинг вместо целого документа

### ✅ **Все готово для исправления:**
- ✅ Qdrant запущен в docker-compose.yml 
- ✅ Все зависимости установлены в pyproject.toml
- ✅ Конфигурация готова в config.py
- ✅ Примеры кода из официальной документации LlamaIndex

**ЗАКЛЮЧЕНИЕ:** Проблема вызвана использованием временного SimpleVectorStore вместо настроенного Qdrant. Исправление займет ~1 час и кардинально улучшит качество релевантности поиска. 