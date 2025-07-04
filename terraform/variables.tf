# Azure Configuration Variables
variable "subscription_id" {
  description = "Azure Subscription ID"
  type        = string
}

variable "resource_group_name" {
  description = "Azure Resource Group name"
  type        = string
  default     = "davai_poigraem"
}

variable "location" {
  description = "Azure location"
  type        = string
  default     = "West Europe"
}

# Container Registry Configuration
variable "container_registry_name" {
  description = "Azure Container Registry name"
  type        = string
  default     = "crawl4aiacr6c07cdcc"
}

variable "container_registry_username" {
  description = "Azure Container Registry username"
  type        = string
}

variable "container_registry_password" {
  description = "Azure Container Registry password"
  type        = string
  sensitive   = true
}

# Container App Environment
variable "container_app_environment_name" {
  description = "Container Apps Environment name"
  type        = string
  default     = "crawl4ai-env"
}

# Application Configuration
variable "app_name" {
  description = "Application name"
  type        = string
  default     = "rag-crawl-app"
}

variable "app_version" {
  description = "Application version tag"
  type        = string
  default     = "latest"
}

# Database Configuration
variable "postgres_password" {
  description = "PostgreSQL database password"
  type        = string
  sensitive   = true
}

variable "postgres_user" {
  description = "PostgreSQL database user"
  type        = string
  default     = "postgres"
}

variable "postgres_database" {
  description = "PostgreSQL database name"
  type        = string
  default     = "rag_crawl"
}

# Azure OpenAI Configuration
variable "azure_openai_api_key" {
  description = "Azure OpenAI API key"
  type        = string
  sensitive   = true
}

variable "azure_openai_endpoint" {
  description = "Azure OpenAI endpoint"
  type        = string
}

variable "azure_openai_chat_deployment" {
  description = "Azure OpenAI chat deployment name"
  type        = string
  default     = "gpt-4o-depl"
}

variable "azure_openai_embedding_deployment" {
  description = "Azure OpenAI embedding deployment name"
  type        = string
  default     = "text-embedding-ada"
}

variable "azure_openai_chat_model" {
  description = "Azure OpenAI chat model"
  type        = string
  default     = "gpt-4o"
}

variable "azure_openai_embedding_model" {
  description = "Azure OpenAI embedding model"
  type        = string
  default     = "text-embedding-ada-002"
}

variable "azure_openai_api_version" {
  description = "Azure OpenAI API version"
  type        = string
  default     = "2024-05-01-preview"
}

# Qdrant Configuration
variable "qdrant_url" {
  description = "Qdrant vector database URL"
  type        = string
  default     = "http://qdrant:6333"
}

variable "qdrant_collection_name" {
  description = "Qdrant collection name"
  type        = string
  default     = "documents"
}

# Application Scaling Configuration
variable "min_replicas" {
  description = "Minimum number of replicas"
  type        = number
  default     = 0
}

variable "max_replicas" {
  description = "Maximum number of replicas"
  type        = number
  default     = 3
}

variable "cpu_requests" {
  description = "CPU requests"
  type        = number
  default     = 1.0
}

variable "memory_requests" {
  description = "Memory requests"
  type        = string
  default     = "2Gi"
}

# Container Images Configuration
variable "frontend_image" {
  description = "Frontend container image"
  type        = string
  default     = "rag-crawl-frontend"
}

variable "backend_image" {
  description = "Backend container image"
  type        = string
  default     = "rag-crawl-backend"
}

variable "nginx_image" {
  description = "Nginx container image"
  type        = string
  default     = "rag-crawl-nginx"
}

# Networking Configuration
variable "target_port" {
  description = "Target port for ingress"
  type        = number
  default     = 80
}

variable "external_ingress" {
  description = "Enable external ingress"
  type        = bool
  default     = true
} 