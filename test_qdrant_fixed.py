#!/usr/bin/env python3
"""
Тестирование исправлений согласно официальной документации LlamaIndex
"""

import asyncio
import sys
import os
sys.path.append("src")

from rag_crawl.services.llama_service import LlamaIndexService
from rag_crawl.database.connection import get_db
from fastapi import UploadFile
import io

async def test_official_qdrant_approach():
    """Тестирование согласно официальной документации LlamaIndex"""
    
    print("🧪 Тестирование согласно официальной документации LlamaIndex...")
    
    # Получаем сессию БД
    db = next(get_db())
    
    # Создаем сервис
    service = LlamaIndexService(db)
    
    print("✅ Сервис создан")
    
    # Тестируем подключение к Qdrant согласно документации
    try:
        vector_store = service._get_vector_store()
        print(f"✅ QdrantVectorStore создан: {type(vector_store).__name__}")
        print(f"   📚 Коллекция: {vector_store.collection_name}")
        print(f"   🔌 Client: {type(vector_store.client).__name__}")
    except Exception as e:
        print(f"❌ Ошибка создания QdrantVectorStore: {e}")
        return False
    
    # Тестируем создание индекса с StorageContext
    try:
        index = service._get_index("test_namespace")
        print(f"✅ Индекс создан: {type(index).__name__}")
        print(f"   📦 Есть storage_context: {hasattr(index, 'storage_context')}")
        if hasattr(index, 'storage_context'):
            print(f"   🏪 Vector store в context: {type(index.storage_context.vector_store).__name__}")
    except Exception as e:
        print(f"❌ Ошибка создания индекса: {e}")
        return False
    
    # Тестируем загрузку документа с IngestionPipeline
    try:
        # Создаем тестовый файл
        test_content = """
        Это тестовый документ для проверки работы системы RAG.
        
        OKR (Objectives and Key Results) - это система управления целями.
        OKR помогает компаниям фокусироваться на главных приоритетах.
        
        Ключевые принципы OKR:
        1. Цели должны быть амбициозными и вдохновляющими
        2. Результаты должны быть измеримыми
        3. OKR должны обновляться каждый квартал
        4. Прозрачность является основой успеха OKR
        
        Внедрение OKR помогает улучшить производительность команды.
        """
        
        # Создаем UploadFile из контента
        file_content = test_content.encode('utf-8')
        upload_file = UploadFile(
            filename="test_okr_document.txt",
            file=io.BytesIO(file_content),
            size=len(file_content),
            headers={"content-type": "text/plain"}
        )
        
        # Загружаем документ
        document = await service.upload_document(upload_file, "test_namespace")
        print(f"✅ Документ загружен: {document.title}")
        print(f"   📊 Количество чанков: {document.chunks_count}")
        print(f"   🆔 ID в БД: {document.id}")
        
    except Exception as e:
        print(f"❌ Ошибка загрузки документа: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Тестируем поиск с фильтрацией релевантности
    try:
        response = await service.query("Что такое OKR?", "test_namespace")
        print(f"✅ Поиск выполнен успешно")
        print(f"   🔍 Ключи ответа: {list(response.keys())}")
        if 'answer' in response:
            print(f"   📝 Ответ: {response['answer'][:100]}...")
        elif 'response' in response:
            print(f"   📝 Ответ: {response['response'][:100]}...")
        print(f"   📚 Количество источников: {len(response.get('sources', []))}")
        
        # Проверяем релевантность
        if response['sources']:
            avg_score = sum(s.get('score', 0) for s in response['sources']) / len(response['sources'])
            print(f"   📈 Средний score релевантности: {avg_score:.3f}")
            
        # Тестируем более сложный запрос
        response2 = await service.query("Как часто нужно обновлять OKR?", "test_namespace")
        print(f"✅ Второй поиск выполнен")
        print(f"   📚 Количество источников: {len(response2['sources'])}")
        
    except Exception as e:
        print(f"❌ Ошибка поиска: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Тестируем чат
    try:
        chat_response = await service.chat("Объясни основные принципы OKR", "test_namespace", "test_session")
        print(f"✅ Чат работает")
        answer_key = 'answer' if 'answer' in chat_response else 'response'
        print(f"   💬 Ответ: {chat_response[answer_key][:100]}...")
        
    except Exception as e:
        print(f"❌ Ошибка чата: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n🎉 Все тесты прошли успешно! Qdrant и LlamaIndex работают корректно.")
    return True

if __name__ == "__main__":
    result = asyncio.run(test_official_qdrant_approach())
    sys.exit(0 if result else 1) 