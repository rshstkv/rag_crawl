#!/bin/bash

# Создание .env.prod файла для развертывания RAG Crawl на Azure
cat > .env.prod << EOF
# PostgreSQL
POSTGRES_PASSWORD=1234

# Azure OpenAI
AZURE_OPENAI_API_KEY=your_api_key_here
AZURE_OPENAI_ENDPOINT=https://openai-totchka.openai.azure.com/
AZURE_OPENAI_CHAT_DEPLOYMENT=gpt-4o-depl
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada
AZURE_OPENAI_CHAT_MODEL=gpt-4o
AZURE_OPENAI_EMBEDDING_MODEL=text-embedding-ada-002
AZURE_OPENAI_API_VERSION=2024-05-01-preview
EOF

echo "✅ .env.prod файл создан. Не забудьте добавить AZURE_OPENAI_API_KEY!" 