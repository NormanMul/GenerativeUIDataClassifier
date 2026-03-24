#!/bin/bash
# =============================================================================
# UDC Enterprise Platform — Azure Deployment Script
# =============================================================================
set -euo pipefail

RESOURCE_GROUP="${RESOURCE_GROUP:-udc-enterprise-rg}"
LOCATION="${LOCATION:-southeastasia}"
ENVIRONMENT="${ENVIRONMENT:-dev}"
ACR_NAME="${ACR_NAME:-udcenterpriseacr}"
IMAGE_TAG="${IMAGE_TAG:-latest}"

echo "=== UDC Enterprise Platform — Deployment ==="
echo "Resource Group: $RESOURCE_GROUP"
echo "Location:       $LOCATION"
echo "Environment:    $ENVIRONMENT"
echo "ACR:            $ACR_NAME"
echo "Image Tag:      $IMAGE_TAG"
echo ""

# Create resource group if it doesn't exist
echo "Creating resource group..."
az group create \
  --name "$RESOURCE_GROUP" \
  --location "$LOCATION" \
  --output none

# Deploy Bicep template
echo "Deploying infrastructure..."
az deployment group create \
  --resource-group "$RESOURCE_GROUP" \
  --template-file "$(dirname "$0")/../bicep/main.bicep" \
  --parameters \
    environment="$ENVIRONMENT" \
    acrName="$ACR_NAME" \
    imageTag="$IMAGE_TAG" \
    azureOpenAIEndpoint="$AZURE_OPENAI_ENDPOINT" \
    azureOpenAIKey="$AZURE_OPENAI_API_KEY" \
    postgresPassword="$POSTGRES_PASSWORD" \
    powerBITenantId="${POWERBI_TENANT_ID:-}" \
    powerBIClientId="${POWERBI_CLIENT_ID:-}" \
    powerBIClientSecret="${POWERBI_CLIENT_SECRET:-}" \
  --output table

echo ""
echo "=== Deployment complete ==="
