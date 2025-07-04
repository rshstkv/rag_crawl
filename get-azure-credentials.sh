#!/bin/bash

# Скрипт для получения Azure credentials для развертывания RAG Crawl

# Цвета для логов
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

echo_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

echo_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Настройки
RESOURCE_GROUP="davai_poigraem"
REGISTRY_NAME="crawl4aiacr6c07cdcc"
SUBSCRIPTION_ID=""

echo_info "🔍 Получение Azure credentials для развертывания RAG Crawl"
echo ""

# 1. Получение credentials для Container Registry
echo_info "1. Получение credentials для Container Registry '$REGISTRY_NAME'"
echo ""

# Проверка, что пользователь авторизован
if ! az account show &> /dev/null; then
    echo_error "❌ Не авторизован в Azure. Выполните 'az login'"
    exit 1
fi

# Получение admin credentials для Container Registry
echo_info "Получение admin credentials для Container Registry..."
REGISTRY_USERNAME=$(az acr credential show --name $REGISTRY_NAME --query username --output tsv)
REGISTRY_PASSWORD=$(az acr credential show --name $REGISTRY_NAME --query passwords[0].value --output tsv)

if [ -n "$REGISTRY_USERNAME" ] && [ -n "$REGISTRY_PASSWORD" ]; then
    echo_info "✅ Container Registry credentials получены:"
    echo "REGISTRY_USERNAME=$REGISTRY_USERNAME"
    echo "REGISTRY_PASSWORD=$REGISTRY_PASSWORD"
else
    echo_error "❌ Не удалось получить Container Registry credentials"
    echo_warn "Возможно, admin пользователь не включен. Включите его командой:"
    echo "az acr update --name $REGISTRY_NAME --admin-enabled true"
    exit 1
fi

echo ""

# 2. Получение Azure OpenAI API Key
echo_info "2. Получение Azure OpenAI API Key для 'openai-totchka'"
echo ""

OPENAI_API_KEY=$(az cognitiveservices account keys list --name openai-totchka --resource-group $RESOURCE_GROUP --query key1 --output tsv)

if [ -n "$OPENAI_API_KEY" ]; then
    echo_info "✅ Azure OpenAI API Key получен:"
    echo "AZURE_OPENAI_API_KEY=$OPENAI_API_KEY"
else
    echo_error "❌ Не удалось получить Azure OpenAI API Key"
    echo_warn "Проверьте доступ к ресурсу 'openai-totchka' в группе '$RESOURCE_GROUP'"
fi

echo ""

# 3. Получение Azure credentials для GitHub Actions
echo_info "3. Создание Service Principal для GitHub Actions"
echo ""

# Получение subscription ID
SUBSCRIPTION_ID=$(az account show --query id --output tsv)
echo_info "Subscription ID: $SUBSCRIPTION_ID"

# Создание Service Principal
echo_info "Создание Service Principal для GitHub Actions..."
SP_NAME="sp-rag-crawl-github-actions"

# Проверяем, существует ли уже Service Principal
if az ad sp show --id "http://$SP_NAME" &> /dev/null; then
    echo_warn "Service Principal '$SP_NAME' уже существует. Используем существующий."
    APP_ID=$(az ad sp show --id "http://$SP_NAME" --query appId --output tsv)
else
    # Создаем новый Service Principal
    SP_OUTPUT=$(az ad sp create-for-rbac --name $SP_NAME --role contributor --scopes /subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP --sdk-auth)
    APP_ID=$(echo "$SP_OUTPUT" | jq -r '.clientId')
    
    if [ -n "$APP_ID" ]; then
        echo_info "✅ Service Principal создан:"
        echo "AZURE_CREDENTIALS (JSON для GitHub Secrets):"
        echo "$SP_OUTPUT"
    else
        echo_error "❌ Не удалось создать Service Principal"
        exit 1
    fi
fi

echo ""

# 4. Обновление .env.prod файла
echo_info "4. Обновление .env.prod файла"
echo ""

# Создаем .env.prod файл с полными данными
cat > .env.prod << EOF
# PostgreSQL
POSTGRES_PASSWORD=1234

# Azure OpenAI
AZURE_OPENAI_API_KEY=$OPENAI_API_KEY
AZURE_OPENAI_ENDPOINT=https://openai-totchka.openai.azure.com/
AZURE_OPENAI_CHAT_DEPLOYMENT=gpt-4o-depl
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada
AZURE_OPENAI_CHAT_MODEL=gpt-4o
AZURE_OPENAI_EMBEDDING_MODEL=text-embedding-ada-002
AZURE_OPENAI_API_VERSION=2024-05-01-preview

# Container Registry
REGISTRY_USERNAME=$REGISTRY_USERNAME
REGISTRY_PASSWORD=$REGISTRY_PASSWORD

# Azure
SUBSCRIPTION_ID=$SUBSCRIPTION_ID
EOF

echo_info "✅ .env.prod файл обновлен с полными данными"

echo ""
echo_info "🎯 Следующие шаги:"
echo "1. Проверьте .env.prod файл: cat .env.prod"
echo "2. Добавьте GitHub Secrets в репозиторий (если нужно автоматическое развертывание)"
echo "3. Запустите развертывание: ./azure/deploy.sh"
echo ""
echo_info "📋 GitHub Secrets для добавления:"
echo "AZURE_CREDENTIALS - JSON из вывода выше"
echo "REGISTRY_USERNAME - $REGISTRY_USERNAME"
echo "REGISTRY_PASSWORD - $REGISTRY_PASSWORD"
echo "POSTGRES_PASSWORD - 1234"
echo "AZURE_OPENAI_API_KEY - $OPENAI_API_KEY"
echo "AZURE_OPENAI_ENDPOINT - https://openai-totchka.openai.azure.com/"
echo "AZURE_OPENAI_CHAT_DEPLOYMENT - gpt-4o-depl"
echo "AZURE_OPENAI_EMBEDDING_DEPLOYMENT - text-embedding-ada"
echo "AZURE_OPENAI_CHAT_MODEL - gpt-4o"
echo "AZURE_OPENAI_EMBEDDING_MODEL - text-embedding-ada-002"
echo "AZURE_OPENAI_API_VERSION - 2024-05-01-preview" 