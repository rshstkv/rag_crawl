#!/usr/bin/env python3
"""Тест LlamaIndex QdrantVectorStore"""

import sys
sys.path.append("src")

import qdrant_client
from llama_index.vector_stores.qdrant import QdrantVectorStore

def test_llama_qdrant():
    try:
        print("🔌 Тестируем LlamaIndex QdrantVectorStore...")
        
        # Создаем client
        client = qdrant_client.QdrantClient(
            host="localhost",
            port=6333,
            timeout=10,
            prefer_grpc=False
        )
        
        print("✅ Qdrant client создан")
        
        # Создаем QdrantVectorStore
        vector_store = QdrantVectorStore(
            client=client,
            collection_name="docs_v2"
        )
        
        print("✅ QdrantVectorStore создан успешно!")
        print(f"   📚 Коллекция: {vector_store.collection_name}")
        
        # Проверим что коллекция существует
        info = client.get_collection("docs_v2")
        print(f"   📊 Векторов в коллекции: {info.vectors_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_llama_qdrant()
    if success:
        print("\n✅ LlamaIndex QdrantVectorStore работает!")
    else:
        print("\n❌ Проблема с LlamaIndex QdrantVectorStore") 