// =============================================================================
// UDC Enterprise Platform — Main Bicep Template
// =============================================================================

targetScope = 'resourceGroup'

@description('Environment name')
@allowed(['dev', 'staging', 'prod'])
param environment string = 'dev'

@description('Azure region for all resources')
param location string = resourceGroup().location

@description('ACR registry name')
param acrName string

@description('Image tag to deploy')
param imageTag string = 'latest'

@description('PostgreSQL admin password')
@secure()
param postgresPassword string

@description('Azure OpenAI endpoint')
param azureOpenAIEndpoint string

@description('Azure OpenAI API key')
@secure()
param azureOpenAIKey string

@description('Power BI tenant ID')
param powerBITenantId string = ''

@description('Power BI client ID')
param powerBIClientId string = ''

@description('Power BI client secret')
@secure()
param powerBIClientSecret string = ''

var prefix = 'udc-${environment}'

// Key Vault for secrets
module keyvault 'keyvault.bicep' = {
  name: '${prefix}-keyvault'
  params: {
    name: '${prefix}-kv'
    location: location
    postgresPassword: postgresPassword
    azureOpenAIKey: azureOpenAIKey
    powerBIClientSecret: powerBIClientSecret
  }
}

// Monitoring (Application Insights + Log Analytics)
module monitoring 'monitoring.bicep' = {
  name: '${prefix}-monitoring'
  params: {
    name: prefix
    location: location
  }
}

// Container Apps Environment + all services
module containerApps 'container-apps.bicep' = {
  name: '${prefix}-container-apps'
  params: {
    prefix: prefix
    location: location
    acrName: acrName
    imageTag: imageTag
    logAnalyticsWorkspaceId: monitoring.outputs.logAnalyticsWorkspaceId
    appInsightsConnectionString: monitoring.outputs.appInsightsConnectionString
    keyVaultName: keyvault.outputs.keyVaultName
    azureOpenAIEndpoint: azureOpenAIEndpoint
    powerBITenantId: powerBITenantId
    powerBIClientId: powerBIClientId
  }
}

output containerAppEnvironmentId string = containerApps.outputs.environmentId
output keyVaultName string = keyvault.outputs.keyVaultName
output appInsightsName string = monitoring.outputs.appInsightsName
