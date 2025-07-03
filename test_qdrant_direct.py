#!/usr/bin/env python3
"""Простой тест подключения к Qdrant"""

import qdrant_client
from qdrant_client.models import Distance, VectorParams

def test_qdrant_direct():
    try:
        print("🔌 Тестируем подключение к Qdrant напрямую...")
        
        # Простое подключение
        client = qdrant_client.QdrantClient(
            host="localhost",
            port=6333,
            timeout=10,
            prefer_grpc=False
        )
        
        # Проверяем соединение
        print("✅ Подключение успешно")
        
        # Получаем список коллекций
        collections = client.get_collections()
        print(f"📚 Коллекции: {[c.name for c in collections.collections]}")
        
        # Пробуем создать тестовую коллекцию
        collection_name = "test_collection"
        try:
            client.get_collection(collection_name)
            print(f"📁 Коллекция '{collection_name}' уже существует")
        except:
            print(f"🆕 Создаем коллекцию '{collection_name}'...")
            client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=1536,
                    distance=Distance.COSINE
                )
            )
            print(f"✅ Коллекция '{collection_name}' создана")
        
        # Получаем информацию о коллекции
        info = client.get_collection(collection_name)
        print(f"📊 Векторов в коллекции: {info.vectors_count}")
        
        print("✅ Все тесты прошли успешно!")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_qdrant_direct() 