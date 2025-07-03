#!/usr/bin/env python3
"""
Простой тест QdrantVectorStore напрямую согласно документации
"""

import qdrant_client
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.core import StorageContext

def test_direct_qdrant():
    """Тест прямого подключения к Qdrant согласно документации"""
    
    print("🔌 Тестируем прямое подключение к QdrantVectorStore...")
    
    try:
        # Создаем client согласно документации
        client = qdrant_client.QdrantClient(
            host="localhost",
            port=6333,
            timeout=10,
            prefer_grpc=False,
            check_compatibility=False  # Отключаем проверку версий
        )
        
        print("✅ Qdrant client создан")
        
        # Тестируем connection
        collections = client.get_collections()
        print(f"✅ Подключение работает, коллекций: {len(collections.collections)}")
        
        # Создаем QdrantVectorStore согласно документации
        vector_store = QdrantVectorStore(
            client=client,
            collection_name="docs_v2"
        )
        
        print("✅ QdrantVectorStore создан успешно!")
        print(f"   📚 Коллекция: {vector_store.collection_name}")
        
        # Создаем StorageContext согласно документации
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        print("✅ StorageContext создан")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = test_direct_qdrant()
    print("\n" + ("🎉 Тест успешен!" if result else "❌ Тест провален!")) 