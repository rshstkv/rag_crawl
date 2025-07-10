terraform {
  required_version = ">= 1.0"
  
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
    azapi = {
      source  = "Azure/azapi"
      version = "~> 1.0"
    }
  }

  # Backend configuration for remote state storage
  # For local development, we'll use local state
  # For production, uncomment and configure azurerm backend
  # backend "azurerm" {
  #   # Configuration will be provided via:
  #   # - terraform init -backend-config=backend.conf
  #   # - Environment variables
  #   # - GitHub Actions will configure this automatically
  # }
}

# Configure the Microsoft Azure Provider
provider "azurerm" {
  features {
    resource_group {
      prevent_deletion_if_contains_resources = false
    }
  }

  subscription_id = var.subscription_id
  use_msi = false
}

# Configure the Azure API Provider for Container Apps
provider "azapi" {
  subscription_id = var.subscription_id
  use_msi = false
} 