#!/usr/bin/env python3
"""Создание коллекции docs_v2 в Qdrant"""

import qdrant_client
from qdrant_client.models import Distance, VectorParams

def create_docs_collection():
    try:
        print("🔌 Подключаемся к Qdrant...")
        
        client = qdrant_client.QdrantClient(
            host="localhost",
            port=6333,
            timeout=10,
            prefer_grpc=False
        )
        
        collection_name = "docs_v2"
        
        # Удаляем если существует (для чистого теста)
        try:
            client.delete_collection(collection_name)
            print(f"🗑️ Удалена существующая коллекция '{collection_name}'")
        except:
            pass
        
        # Создаем коллекцию
        print(f"🆕 Создаем коллекцию '{collection_name}'...")
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=1536,  # Azure OpenAI embedding size
                distance=Distance.COSINE
            )
        )
        
        # Проверяем что создалась
        info = client.get_collection(collection_name)
        print(f"✅ Коллекция '{collection_name}' создана успешно!")
        print(f"   📊 Размер векторов: {info.config.params.vectors.size}")
        print(f"   📏 Метрика расстояния: {info.config.params.vectors.distance}")
        print(f"   📈 Векторов в коллекции: {info.vectors_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = create_docs_collection()
    if success:
        print("\n✅ Готово! Можно тестировать LlamaIndex с Qdrant")
    else:
        print("\n❌ Не удалось создать коллекцию") 