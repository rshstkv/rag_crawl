#!/bin/bash

# Настройки
RESOURCE_GROUP="davai_poigraem"
CONTAINER_APP_NAME="rag-crawl-app"
CONTAINER_APP_ENVIRONMENT="crawl4ai-env"
AZURE_CONTAINER_REGISTRY="crawl4aiacr6c07cdcc.azurecr.io"
LOCATION="westeurope"

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

# Проверка переменных окружения
check_env_vars() {
    local required_vars=(
        "POSTGRES_PASSWORD"
        "AZURE_OPENAI_API_KEY"
        "AZURE_OPENAI_ENDPOINT"
        "AZURE_OPENAI_CHAT_DEPLOYMENT"
        "AZURE_OPENAI_EMBEDDING_DEPLOYMENT"
        "AZURE_OPENAI_CHAT_MODEL"
        "AZURE_OPENAI_EMBEDDING_MODEL"
        "AZURE_OPENAI_API_VERSION"
    )
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            echo_error "Переменная окружения $var не установлена"
            exit 1
        fi
    done
    
    echo_info "Все необходимые переменные окружения установлены"
}

# Проверка Azure CLI
check_azure_cli() {
    if ! command -v az &> /dev/null; then
        echo_error "Azure CLI не установлен. Установите его с https://docs.microsoft.com/cli/azure/install-azure-cli"
        exit 1
    fi
    
    echo_info "Azure CLI найден"
}

# Проверка авторизации в Azure
check_azure_auth() {
    if ! az account show &> /dev/null; then
        echo_error "Не авторизован в Azure. Выполните 'az login'"
        exit 1
    fi
    
    echo_info "Авторизация в Azure проверена"
}

# Сборка и пуш Docker образов
build_and_push() {
    echo_info "Начинаем сборку и пуш Docker образов..."
    
    # Получаем commit hash для тегов
    COMMIT_HASH=$(git rev-parse --short HEAD)
    
    # Авторизация в Container Registry
    az acr login --name crawl4aiacr6c07cdcc
    
    # Сборка и пуш Frontend
    echo_info "Сборка Frontend образа..."
    docker build -t $AZURE_CONTAINER_REGISTRY/rag-crawl-frontend:$COMMIT_HASH \
        -f deployment/dockerfiles/frontend.Dockerfile .
    docker push $AZURE_CONTAINER_REGISTRY/rag-crawl-frontend:$COMMIT_HASH
    
    # Сборка и пуш Backend  
    echo_info "Сборка Backend образа..."
    docker build -t $AZURE_CONTAINER_REGISTRY/rag-crawl-backend:$COMMIT_HASH \
        -f deployment/dockerfiles/backend.Dockerfile .
    docker push $AZURE_CONTAINER_REGISTRY/rag-crawl-backend:$COMMIT_HASH
    
    # Сборка и пуш Nginx
    echo_info "Сборка Nginx образа..."
    docker build -t $AZURE_CONTAINER_REGISTRY/rag-crawl-nginx:$COMMIT_HASH \
        -f deployment/dockerfiles/nginx.Dockerfile .
    docker push $AZURE_CONTAINER_REGISTRY/rag-crawl-nginx:$COMMIT_HASH
    
    echo_info "Все образы собраны и загружены"
}

# Создание Container App
create_container_app() {
    echo_info "Создание Container App..."
    
    COMMIT_HASH=$(git rev-parse --short HEAD)
    
    # Проверяем, существует ли Container App
    if az containerapp show --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP &> /dev/null; then
        echo_warn "Container App уже существует. Обновляем..."
        update_container_app
        return
    fi
    
    # Создаем Container App
    az containerapp create \
        --name $CONTAINER_APP_NAME \
        --resource-group $RESOURCE_GROUP \
        --environment $CONTAINER_APP_ENVIRONMENT \
        --image $AZURE_CONTAINER_REGISTRY/rag-crawl-nginx:$COMMIT_HASH \
        --registry-server $AZURE_CONTAINER_REGISTRY \
        --secrets \
            postgres-password="$POSTGRES_PASSWORD" \
            azure-openai-api-key="$AZURE_OPENAI_API_KEY" \
            azure-openai-endpoint="$AZURE_OPENAI_ENDPOINT" \
            azure-openai-chat-deployment="$AZURE_OPENAI_CHAT_DEPLOYMENT" \
            azure-openai-embedding-deployment="$AZURE_OPENAI_EMBEDDING_DEPLOYMENT" \
            azure-openai-chat-model="$AZURE_OPENAI_CHAT_MODEL" \
            azure-openai-embedding-model="$AZURE_OPENAI_EMBEDDING_MODEL" \
            azure-openai-api-version="$AZURE_OPENAI_API_VERSION" \
        --env-vars \
            POSTGRES_PASSWORD=secretref:postgres-password \
            AZURE_OPENAI_API_KEY=secretref:azure-openai-api-key \
            AZURE_OPENAI_ENDPOINT=secretref:azure-openai-endpoint \
            AZURE_OPENAI_CHAT_DEPLOYMENT=secretref:azure-openai-chat-deployment \
            AZURE_OPENAI_EMBEDDING_DEPLOYMENT=secretref:azure-openai-embedding-deployment \
            AZURE_OPENAI_CHAT_MODEL=secretref:azure-openai-chat-model \
            AZURE_OPENAI_EMBEDDING_MODEL=secretref:azure-openai-embedding-model \
            AZURE_OPENAI_API_VERSION=secretref:azure-openai-api-version \
        --target-port 80 \
        --ingress external \
        --cpu 1.0 \
        --memory 2.0Gi \
        --min-replicas 0 \
        --max-replicas 3 \
        --scale-rule-name http-scale-rule \
        --scale-rule-type http \
        --scale-rule-metadata concurrentRequests=10
    
    echo_info "Container App создан успешно"
}

# Обновление Container App
update_container_app() {
    echo_info "Обновление Container App..."
    
    COMMIT_HASH=$(git rev-parse --short HEAD)
    
    az containerapp update \
        --name $CONTAINER_APP_NAME \
        --resource-group $RESOURCE_GROUP \
        --image $AZURE_CONTAINER_REGISTRY/rag-crawl-nginx:$COMMIT_HASH
    
    echo_info "Container App обновлен успешно"
}

# Получение URL приложения
get_app_url() {
    echo_info "Получение URL приложения..."
    
    URL=$(az containerapp show \
        --name $CONTAINER_APP_NAME \
        --resource-group $RESOURCE_GROUP \
        --query properties.configuration.ingress.fqdn \
        --output tsv)
    
    if [ -n "$URL" ]; then
        echo_info "Приложение доступно по адресу: https://$URL"
    else
        echo_error "Не удалось получить URL приложения"
    fi
}

# Основная функция
main() {
    echo_info "Начинаем развертывание RAG Crawl на Azure"
    
    # Загружаем переменные окружения из .env.prod
    if [ -f ".env.prod" ]; then
        echo_info "Загружаем переменные окружения из .env.prod"
        export $(cat .env.prod | grep -v ^# | xargs)
    else
        echo_error "Файл .env.prod не найден"
        exit 1
    fi
    
    check_env_vars
    check_azure_cli
    check_azure_auth
    
    echo_info "Все проверки пройдены успешно"
    
    build_and_push
    create_container_app
    get_app_url
    
    echo_info "Развертывание завершено!"
}

# Проверка аргументов
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "Использование: $0 [опции]"
    echo ""
    echo "Опции:"
    echo "  --help, -h     Показать это сообщение"
    echo "  --build-only   Только собрать и загрузить образы"
    echo "  --deploy-only  Только развернуть (без сборки)"
    echo ""
    echo "Переменные окружения:"
    echo "  POSTGRES_PASSWORD               - Пароль для PostgreSQL"
    echo "  AZURE_OPENAI_API_KEY           - API ключ Azure OpenAI"
    echo "  AZURE_OPENAI_ENDPOINT          - Endpoint Azure OpenAI"
    echo "  AZURE_OPENAI_CHAT_DEPLOYMENT   - Deployment для chat модели"
    echo "  AZURE_OPENAI_EMBEDDING_DEPLOYMENT - Deployment для embedding модели"
    echo "  AZURE_OPENAI_CHAT_MODEL        - Имя chat модели"
    echo "  AZURE_OPENAI_EMBEDDING_MODEL   - Имя embedding модели"
    echo "  AZURE_OPENAI_API_VERSION       - Версия API"
    exit 0
fi

if [ "$1" = "--build-only" ]; then
    check_env_vars
    check_azure_cli
    check_azure_auth
    build_and_push
    exit 0
fi

if [ "$1" = "--deploy-only" ]; then
    check_env_vars
    check_azure_cli
    check_azure_auth
    create_container_app
    get_app_url
    exit 0
fi

# Запуск основной функции
main 