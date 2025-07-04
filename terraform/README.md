# RAG Crawl - Terraform Infrastructure

Этот каталог содержит Terraform конфигурацию для развертывания RAG Crawl приложения в Azure Container Apps.

## Структура файлов

- `variables.tf` - Определения всех переменных
- `provider.tf` - Настройка Azure провайдеров и backend
- `main.tf` - Основная конфигурация инфраструктуры
- `outputs.tf` - Выходные значения
- `terraform.tfvars` - Значения переменных (НЕ коммитить!)
- `terraform.tfvars.example` - Пример файла с переменными

## Архитектура

Terraform создает Azure Container App с несколькими контейнерами:

1. **Nginx** - Reverse proxy и основная точка входа (порт 80)
2. **Frontend** - Next.js приложение (порт 3000)
3. **Backend** - FastAPI сервер (порт 8000)
4. **PostgreSQL** - База данных (порт 5432)
5. **Qdrant** - Векторная база данных (порт 6333)

Все контейнеры работают в одном поде и могут общаться через `localhost`.

## Предварительные требования

1. **Azure CLI** - установлен и авторизован
2. **Terraform** >= 1.0
3. **Docker образы** - собраны и загружены в Azure Container Registry

## Локальная настройка

1. Скопируйте пример переменных:
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   ```

2. Заполните реальные значения в `terraform.tfvars`

3. Инициализация Terraform:
   ```bash
   terraform init
   ```

4. Планирование развертывания:
   ```bash
   terraform plan
   ```

5. Применение изменений:
   ```bash
   terraform apply
   ```

## GitHub Actions Deployment

Для автоматического развертывания через GitHub Actions настроены следующие секреты:

### GitHub Secrets

```bash
# Azure credentials
AZURE_CLIENT_ID=<service-principal-client-id>
AZURE_CLIENT_SECRET=<service-principal-client-secret>
AZURE_TENANT_ID=<azure-tenant-id>
AZURE_SUBSCRIPTION_ID=<azure-subscription-id>

# Container Registry
CONTAINER_REGISTRY_NAME=crawl4aiacr6c07cdcc
CONTAINER_REGISTRY_USERNAME=crawl4aiacr6c07cdcc
CONTAINER_REGISTRY_PASSWORD=<registry-password>

# Application secrets
POSTGRES_PASSWORD=<postgres-password>
AZURE_OPENAI_API_KEY=<openai-api-key>
AZURE_OPENAI_ENDPOINT=<openai-endpoint>
```

### Workflow triggers

- Push в `main` ветку
- Pull Request в `main` ветку (план только)
- Ручной запуск через GitHub UI

## Переменные окружения

Все конфигурационные параметры определены в `variables.tf` и могут быть переопределены через:

1. `terraform.tfvars` файл (локально)
2. GitHub Secrets (CI/CD)
3. Переменные окружения `TF_VAR_*`

## Outputs

После успешного развертывания Terraform выводит:

- URL приложения
- FQDN Container App
- Информация о ресурсах
- Сводка развертывания

## Troubleshooting

### Проблемы с Container Registry

```bash
# Проверка доступа к registry
az acr login --name crawl4aiacr6c07cdcc
```

### Проблемы с Container App

```bash
# Просмотр логов
az containerapp logs show --name rag-crawl-app --resource-group davai_poigraem

# Перезапуск приложения
az containerapp revision restart --name rag-crawl-app --resource-group davai_poigraem
```

### Отладка Terraform

```bash
# Детальные логи
export TF_LOG=DEBUG
terraform apply

# Проверка состояния
terraform show
terraform state list
```

## Очистка ресурсов

```bash
# Удаление всех ресурсов
terraform destroy
```

⚠️ **Внимание**: Это удалит все данные включая базы данных!

## Backend Configuration

Для продакшена рекомендуется настроить remote backend:

```hcl
terraform {
  backend "azurerm" {
    resource_group_name  = "tfstate-rg"
    storage_account_name = "tfstatestg"
    container_name       = "tfstate"
    key                  = "rag-crawl.terraform.tfstate"
  }
}
```

## Безопасность

- `terraform.tfvars` добавлен в `.gitignore`
- Чувствительные переменные помечены как `sensitive = true`
- Секреты хранятся в Azure Key Vault через Container App secrets
- Container Registry credentials управляются автоматически 