// =============================================================================
// UDC Enterprise Platform — Container Apps Bicep Template
// =============================================================================

param prefix string
param location string
param acrName string
param imageTag string
param logAnalyticsWorkspaceId string
param appInsightsConnectionString string
param keyVaultName string
param azureOpenAIEndpoint string
param powerBITenantId string
param powerBIClientId string

// Container Apps Environment
resource containerAppEnv 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: '${prefix}-env'
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: reference(logAnalyticsWorkspaceId, '2022-10-01').customerId
        sharedKey: listKeys(logAnalyticsWorkspaceId, '2022-10-01').primarySharedKey
      }
    }
  }
}

// Service definitions
var services = [
  {
    name: 'classifier'
    image: '${acrName}.azurecr.io/udc-classifier:${imageTag}'
    port: 8080
    cpu: '1.0'
    memory: '2Gi'
    env: [
      { name: 'ASPNETCORE_ENVIRONMENT', value: 'Production' }
      { name: 'AzureOpenAI__Endpoint', value: azureOpenAIEndpoint }
      { name: 'PowerBI__TenantId', value: powerBITenantId }
      { name: 'PowerBI__ClientId', value: powerBIClientId }
      { name: 'APPLICATIONINSIGHTS_CONNECTION_STRING', value: appInsightsConnectionString }
    ]
  }
  {
    name: 'metacatalog'
    image: '${acrName}.azurecr.io/udc-metacatalog:${imageTag}'
    port: 8001
    cpu: '0.5'
    memory: '1Gi'
    env: [
      { name: 'PORT', value: '8001' }
      { name: 'AZURE_OPENAI_ENDPOINT', value: azureOpenAIEndpoint }
      { name: 'APPLICATIONINSIGHTS_CONNECTION_STRING', value: appInsightsConnectionString }
    ]
  }
  {
    name: 'contextvault'
    image: '${acrName}.azurecr.io/udc-contextvault:${imageTag}'
    port: 8002
    cpu: '0.5'
    memory: '1Gi'
    env: [
      { name: 'PORT', value: '8002' }
      { name: 'AZURE_OPENAI_ENDPOINT', value: azureOpenAIEndpoint }
      { name: 'APPLICATIONINSIGHTS_CONNECTION_STRING', value: appInsightsConnectionString }
    ]
  }
  {
    name: 'policyguard'
    image: '${acrName}.azurecr.io/udc-policyguard:${imageTag}'
    port: 8005
    cpu: '0.25'
    memory: '0.5Gi'
    env: [
      { name: 'PORT', value: '8005' }
      { name: 'APPLICATIONINSIGHTS_CONNECTION_STRING', value: appInsightsConnectionString }
    ]
  }
  {
    name: 'orchestrator'
    image: '${acrName}.azurecr.io/udc-orchestrator:${imageTag}'
    port: 8006
    cpu: '0.5'
    memory: '1Gi'
    env: [
      { name: 'PORT', value: '8006' }
      { name: 'AZURE_OPENAI_ENDPOINT', value: azureOpenAIEndpoint }
      { name: 'APPLICATIONINSIGHTS_CONNECTION_STRING', value: appInsightsConnectionString }
    ]
  }
]

// Deploy each container app
resource containerApps 'Microsoft.App/containerApps@2024-03-01' = [for service in services: {
  name: '${prefix}-${service.name}'
  location: location
  properties: {
    managedEnvironmentId: containerAppEnv.id
    configuration: {
      ingress: {
        external: service.name == 'orchestrator'
        targetPort: service.port
        transport: 'http'
      }
      registries: [
        {
          server: '${acrName}.azurecr.io'
          identity: 'system'
        }
      ]
    }
    template: {
      containers: [
        {
          name: service.name
          image: service.image
          resources: {
            cpu: json(service.cpu)
            memory: service.memory
          }
          env: service.env
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 5
        rules: [
          {
            name: 'http-scaling'
            http: {
              metadata: {
                concurrentRequests: '50'
              }
            }
          }
        ]
      }
    }
  }
  identity: {
    type: 'SystemAssigned'
  }
}]

output environmentId string = containerAppEnv.id
