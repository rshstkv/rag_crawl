# Data sources to get existing resources
data "azurerm_resource_group" "main" {
  name = var.resource_group_name
}

data "azurerm_container_registry" "main" {
  name                = var.container_registry_name
  resource_group_name = data.azurerm_resource_group.main.name
}

data "azurerm_container_app_environment" "main" {
  name                = var.container_app_environment_name
  resource_group_name = data.azurerm_resource_group.main.name
}

# Local values for computed configurations
locals {
  container_registry_server = data.azurerm_container_registry.main.login_server
  
  # Image tags with registry prefix
  frontend_image_full = "${local.container_registry_server}/${var.frontend_image}:${var.app_version}"
  backend_image_full  = "${local.container_registry_server}/${var.backend_image}:${var.app_version}"
  nginx_image_full    = "${local.container_registry_server}/${var.nginx_image}:${var.app_version}"
  
  # PostgreSQL connection configuration
  postgres_host = "localhost"  # All containers in the same pod
  postgres_port = "5432"
  database_url = "postgresql://${var.postgres_user}:${var.postgres_password}@${local.postgres_host}:${local.postgres_port}/${var.postgres_database}"
  
  # Qdrant configuration
  qdrant_host = "localhost"  # Same pod
  qdrant_url  = "http://${local.qdrant_host}:6333"
}

# Container App with multiple containers (sidecar pattern)
resource "azapi_resource" "container_app" {
  type      = "Microsoft.App/containerApps@2023-05-01"
  name      = var.app_name
  location  = var.location
  parent_id = data.azurerm_resource_group.main.id

  body = jsonencode({
    properties = {
      environmentId = data.azurerm_container_app_environment.main.id
      
      configuration = {
        activeRevisionsMode = "Single"
        
        ingress = {
          external   = var.external_ingress
          targetPort = var.target_port
          transport  = "Auto"
          
          traffic = [{
            weight         = 100
            latestRevision = true
          }]
        }
        
        registries = [{
          server            = local.container_registry_server
          username          = var.container_registry_username
          passwordSecretRef = "registry-password"
        }]
        
        secrets = [
          {
            name  = "registry-password"
            value = var.container_registry_password
          },
          {
            name  = "postgres-password"
            value = var.postgres_password
          },
          {
            name  = "azure-openai-api-key"
            value = var.azure_openai_api_key
          },
          {
            name  = "database-url"
            value = local.database_url
          }
        ]
      }
      
      template = {
        revisionSuffix = ""
        
        scale = {
          minReplicas = var.min_replicas
          maxReplicas = var.max_replicas
          
          rules = [{
            name = "http-scale-rule"
            http = {
              metadata = {
                concurrentRequests = "100"
              }
            }
          }]
        }
        
        containers = [
          # Nginx reverse proxy (main container)
          {
            name  = "nginx"
            image = local.nginx_image_full
            
            resources = {
              cpu    = var.cpu_requests
              memory = var.memory_requests
            }
            
            probes = [{
              type = "Liveness"
              httpGet = {
                path = "/"
                port = 80
              }
              initialDelaySeconds = 30
              periodSeconds       = 10
            }]
          },
          
          # Frontend container
          {
            name  = "frontend"
            image = local.frontend_image_full
            
            resources = {
              cpu    = 0.5
              memory = "1Gi"
            }
            
            env = [
              {
                name  = "NODE_ENV"
                value = "production"
              },
              {
                name  = "NEXT_PUBLIC_API_URL"
                value = "/api"
              }
            ]
            
            probes = [{
              type = "Liveness"
              httpGet = {
                path = "/"
                port = 3000
              }
              initialDelaySeconds = 45
              periodSeconds       = 30
            }]
          },
          
          # Backend container
          {
            name  = "backend"
            image = local.backend_image_full
            
            resources = {
              cpu    = 1.0
              memory = "2Gi"
            }
            
            env = [
              {
                name        = "DATABASE_URL"
                secretRef   = "database-url"
              },
              {
                name        = "POSTGRES_PASSWORD"
                secretRef   = "postgres-password"
              },
              {
                name  = "POSTGRES_USER"
                value = var.postgres_user
              },
              {
                name  = "POSTGRES_DATABASE"
                value = var.postgres_database
              },
              {
                name  = "POSTGRES_HOST"
                value = local.postgres_host
              },
              {
                name  = "POSTGRES_PORT"
                value = local.postgres_port
              },
              {
                name        = "AZURE_OPENAI_API_KEY"
                secretRef   = "azure-openai-api-key"
              },
              {
                name  = "AZURE_OPENAI_ENDPOINT"
                value = var.azure_openai_endpoint
              },
              {
                name  = "AZURE_OPENAI_CHAT_DEPLOYMENT"
                value = var.azure_openai_chat_deployment
              },
              {
                name  = "AZURE_OPENAI_EMBEDDING_DEPLOYMENT"
                value = var.azure_openai_embedding_deployment
              },
              {
                name  = "AZURE_OPENAI_CHAT_MODEL"
                value = var.azure_openai_chat_model
              },
              {
                name  = "AZURE_OPENAI_EMBEDDING_MODEL"
                value = var.azure_openai_embedding_model
              },
              {
                name  = "AZURE_OPENAI_API_VERSION"
                value = var.azure_openai_api_version
              },
              {
                name  = "QDRANT_URL"
                value = local.qdrant_url
              },
              {
                name  = "QDRANT_COLLECTION_NAME"
                value = var.qdrant_collection_name
              }
            ]
            
            probes = [{
              type = "Liveness"
              httpGet = {
                path = "/api/health"
                port = 8000
              }
              initialDelaySeconds = 60
              periodSeconds       = 30
            }]
          },
          
          # PostgreSQL database
          {
            name  = "postgres"
            image = "postgres:15-alpine"
            
            resources = {
              cpu    = 0.5
              memory = "1Gi"
            }
            
            env = [
              {
                name  = "POSTGRES_USER"
                value = var.postgres_user
              },
              {
                name        = "POSTGRES_PASSWORD"
                secretRef   = "postgres-password"
              },
              {
                name  = "POSTGRES_DB"
                value = var.postgres_database
              },
              {
                name  = "PGDATA"
                value = "/var/lib/postgresql/data/pgdata"
              }
            ]
            
            volumeMounts = [{
              volumeName = "postgres-data"
              mountPath  = "/var/lib/postgresql/data"
            }]
            
            probes = [{
              type = "Liveness"
              tcpSocket = {
                port = 5432
              }
              initialDelaySeconds = 30
              periodSeconds       = 10
            }]
          },
          
          # Qdrant vector database
          {
            name  = "qdrant"
            image = "qdrant/qdrant:latest"
            
            resources = {
              cpu    = 0.5
              memory = "1Gi"
            }
            
            volumeMounts = [{
              volumeName = "qdrant-data"
              mountPath  = "/qdrant/storage"
            }]
            
            probes = [{
              type = "Liveness"
              httpGet = {
                path = "/healthz"
                port = 6333
              }
              initialDelaySeconds = 30
              periodSeconds       = 10
            }]
          }
        ]
        
        volumes = [
          {
            name        = "postgres-data"
            storageType = "EmptyDir"
          },
          {
            name        = "qdrant-data"
            storageType = "EmptyDir"
          }
        ]
      }
    }
  })
} 