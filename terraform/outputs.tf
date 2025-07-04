# Data source to get Container App details
data "azurerm_container_app" "deployed" {
  name                = azapi_resource.container_app.name
  resource_group_name = data.azurerm_resource_group.main.name
  depends_on         = [azapi_resource.container_app]
}

# Container App outputs
output "container_app_id" {
  description = "The ID of the Container App"
  value       = azapi_resource.container_app.id
}

output "container_app_name" {
  description = "The name of the Container App"
  value       = azapi_resource.container_app.name
}

output "container_app_url" {
  description = "The URL of the Container App"
  value       = "https://${data.azurerm_container_app.deployed.latest_revision_fqdn}"
}

output "container_app_fqdn" {
  description = "The FQDN of the Container App"
  value       = data.azurerm_container_app.deployed.latest_revision_fqdn
}

# Resource Group outputs
output "resource_group_name" {
  description = "The name of the resource group"
  value       = data.azurerm_resource_group.main.name
}

output "resource_group_location" {
  description = "The location of the resource group"
  value       = data.azurerm_resource_group.main.location
}

# Container Registry outputs
output "container_registry_name" {
  description = "The name of the container registry"
  value       = data.azurerm_container_registry.main.name
}

output "container_registry_login_server" {
  description = "The login server of the container registry"
  value       = data.azurerm_container_registry.main.login_server
}

# Container App Environment outputs
output "container_app_environment_name" {
  description = "The name of the Container App Environment"
  value       = data.azurerm_container_app_environment.main.name
}

output "container_app_environment_id" {
  description = "The ID of the Container App Environment"
  value       = data.azurerm_container_app_environment.main.id
}

# Application configuration outputs
output "app_version" {
  description = "The deployed application version"
  value       = var.app_version
}

output "deployment_summary" {
  description = "Summary of the deployment"
  value = {
    app_name     = var.app_name
    app_version  = var.app_version
    app_url      = "https://${data.azurerm_container_app.deployed.latest_revision_fqdn}"
    app_fqdn     = data.azurerm_container_app.deployed.latest_revision_fqdn
    resource_group = data.azurerm_resource_group.main.name
    location     = data.azurerm_resource_group.main.location
    registry     = data.azurerm_container_registry.main.login_server
    environment  = data.azurerm_container_app_environment.main.name
  }
} 