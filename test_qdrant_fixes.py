#!/usr/bin/env python3
"""
Тестирование исправлений релевантности поиска с Qdrant
"""

import asyncio
import sys
import os
sys.path.append("src")

from rag_crawl.services.llama_service import LlamaIndexService
from rag_crawl.database.connection import get_db
from fastapi import UploadFile
import io


async def test_qdrant_fixes():
    """Тестирование исправлений с Qdrant"""
    
    print("🧪 Запуск тестирования исправлений Qdrant...")
    
    # Получаем сессию БД
    db = next(get_db())
    
    # Создаем сервис
    service = LlamaIndexService(db)
    
    print("✅ Сервис создан")
    
    # Тестируем подключение к Qdrant
    try:
        vector_store = service._get_vector_store()
        print(f"✅ Подключение к Qdrant: {type(vector_store).__name__}")
    except Exception as e:
        print(f"❌ Ошибка подключения к Qdrant: {e}")
        return
    
    # Загружаем тестовый документ
    print("\n📄 Загрузка тестового документа...")
    
    with open("test_document.txt", "rb") as f:
        file_content = f.read()
    
    # Создаем UploadFile объект
    upload_file = UploadFile(
        filename="test_document.txt",
        file=io.BytesIO(file_content)
    )
    
    try:
        document = await service.upload_document(upload_file, namespace="test")
        print(f"✅ Документ загружен: {document.title}, чанков: {document.chunks_count}")
    except Exception as e:
        print(f"❌ Ошибка загрузки документа: {e}")
        return
    
    # Тестируем поиск с фильтрацией релевантности
    print("\n🔍 Тестирование поиска с фильтрацией релевантности...")
    
    test_queries = [
        "Что такое OKR?",
        "Как работает система целей?", 
        "README файл инструкции",  # Должно не найти ничего релевантного
    ]
    
    for query in test_queries:
        print(f"\n🔍 Запрос: '{query}'")
        try:
            result = await service.query(query, namespace="test")
            sources = result.get("sources", [])
            
            print(f"  📊 Найдено источников: {len(sources)}")
            for source in sources:
                print(f"    📄 {source['document_title']} (score: {source['score']})")
            
            if len(sources) == 0:
                print("  ✅ Нет нерелевантных результатов - фильтр работает!")
            
        except Exception as e:
            print(f"  ❌ Ошибка поиска: {e}")
    
    # Проверяем Qdrant коллекцию
    print(f"\n🗃️ Проверка коллекции Qdrant...")
    try:
        client = vector_store.client
        collection_info = client.get_collection("docs_v2")
        vectors_count = collection_info.vectors_count
        print(f"  ✅ Векторов в коллекции: {vectors_count}")
    except Exception as e:
        print(f"  ❌ Ошибка проверки коллекции: {e}")
    
    print("\n✅ Тестирование завершено!")


if __name__ == "__main__":
    asyncio.run(test_qdrant_fixes()) 