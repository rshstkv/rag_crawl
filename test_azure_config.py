#!/usr/bin/env python3
"""
Тестовый скрипт для проверки конфигурации Azure OpenAI.
Проверяет подтягивание параметров из .env и возможность подключения.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
import asyncio
from openai import AsyncAzureOpenAI
import sys

def load_env_config():
    """Загружает конфигурацию из .env файла."""
    env_path = Path('.env')
    if not env_path.exists():
        print("❌ Файл .env не найден!")
        return None
    
    load_dotenv(env_path)
    
    config = {
        'api_key': os.getenv('AZURE_OPENAI_API_KEY'),
        'endpoint': os.getenv('AZURE_OPENAI_ENDPOINT'), 
        'api_version': os.getenv('AZURE_OPENAI_API_VERSION', '2024-05-01-preview'),
        'chat_deployment': os.getenv('AZURE_OPENAI_CHAT_DEPLOYMENT'),
        'embedding_deployment': os.getenv('AZURE_OPENAI_EMBEDDING_DEPLOYMENT')
    }
    
    return config

def print_config(config):
    """Выводит конфигурацию (без API ключа)."""
    print("🔧 Конфигурация Azure OpenAI:")
    print(f"   Endpoint: {config['endpoint']}")
    print(f"   API Version: {config['api_version']}")
    print(f"   Chat Deployment: {config['chat_deployment']}")
    print(f"   Embedding Deployment: {config['embedding_deployment']}")
    print(f"   API Key: {'✅ Установлен' if config['api_key'] else '❌ Не установлен'}")
    print()

def validate_config(config):
    """Проверяет обязательные параметры."""
    required_fields = ['api_key', 'endpoint', 'chat_deployment', 'embedding_deployment']
    missing = [field for field in required_fields if not config.get(field)]
    
    if missing:
        print(f"❌ Отсутствуют обязательные параметры: {', '.join(missing)}")
        return False
    
    print("✅ Все обязательные параметры присутствуют")
    return True

async def test_embedding_deployment(config):
    """Тестирует embedding deployment."""
    print("🧪 Тестирую embedding deployment...")
    
    try:
        client = AsyncAzureOpenAI(
            api_key=config['api_key'],
            api_version=config['api_version'],
            azure_endpoint=config['endpoint']
        )
        
        # Простой тест с минимальным текстом
        response = await client.embeddings.create(
            model=config['embedding_deployment'],
            input="test"
        )
        
        print(f"✅ Embedding deployment '{config['embedding_deployment']}' работает!")
        print(f"   Размерность вектора: {len(response.data[0].embedding)}")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка embedding deployment: {e}")
        return False

async def test_chat_deployment(config):
    """Тестирует chat deployment."""
    print("🧪 Тестирую chat deployment...")
    
    try:
        client = AsyncAzureOpenAI(
            api_key=config['api_key'],
            api_version=config['api_version'],
            azure_endpoint=config['endpoint']
        )
        
        # Простой тест чата
        response = await client.chat.completions.create(
            model=config['chat_deployment'],
            messages=[{"role": "user", "content": "Привет! Это тест."}],
            max_tokens=50
        )
        
        print(f"✅ Chat deployment '{config['chat_deployment']}' работает!")
        print(f"   Ответ: {response.choices[0].message.content}")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка chat deployment: {e}")
        return False

async def list_deployments(config):
    """Пытается получить список доступных deployments."""
    print("📋 Пытаюсь получить список deployments...")
    
    try:
        import httpx
        
        headers = {
            'api-key': config['api_key'],
            'Content-Type': 'application/json'
        }
        
        # Формируем URL для получения списка deployments
        url = f"{config['endpoint'].rstrip('/')}/openai/deployments?api-version={config['api_version']}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            
            if response.status_code == 200:
                deployments = response.json()
                print("✅ Доступные deployments:")
                for deployment in deployments.get('data', []):
                    print(f"   - {deployment.get('id')} ({deployment.get('model')})")
                return True
            else:
                print(f"❌ Не удалось получить deployments: {response.status_code}")
                print(f"   Ответ: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Ошибка получения deployments: {e}")
        return False

async def main():
    """Основная функция тестирования."""
    print("🚀 Тестирование конфигурации Azure OpenAI")
    print("=" * 50)
    
    # Загружаем конфигурацию
    config = load_env_config()
    if not config:
        sys.exit(1)
    
    # Выводим конфигурацию
    print_config(config)
    
    # Проверяем обязательные параметры
    if not validate_config(config):
        sys.exit(1)
    
    print()
    
    # Тестируем deployments
    embedding_ok = await test_embedding_deployment(config)
    print()
    
    chat_ok = await test_chat_deployment(config)
    print()
    
    # Пытаемся получить список deployments
    await list_deployments(config)
    print()
    
    # Итоговый результат
    print("=" * 50)
    if embedding_ok and chat_ok:
        print("🎉 Все тесты прошли успешно! Azure OpenAI настроен правильно.")
    else:
        print("⚠️  Есть проблемы с конфигурацией Azure OpenAI.")
        if not embedding_ok:
            print("   - Проблема с embedding deployment")
        if not chat_ok:
            print("   - Проблема с chat deployment")

if __name__ == "__main__":
    asyncio.run(main()) 