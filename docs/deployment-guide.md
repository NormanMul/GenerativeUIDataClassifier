# UDC Enterprise Platform — Deployment Guide

## Prerequisites

- Docker Desktop 4.x (Docker Compose v2)
- .NET SDK 8.0
- Python 3.11+ with uv
- Node.js 20+ with npm
- Azure CLI (`az`) for cloud deployment

## Local Development

### Quick Start

```bash
# Clone and configure
cp .env.example .env
# Edit .env with your Azure OpenAI keys and other credentials

# Start all services
docker compose up -d

# Verify health
curl http://localhost:80/health
```

### Individual Service Development

```bash
# Python service (e.g., MetaCatalog)
cd src/udc_metacatalog
uv sync
uv run uvicorn udc_metacatalog.api.app:app --reload --port 8001

# .NET Classifier
cd src/UDC.Classifier
dotnet run --project UDC.Classifier.Api

# Frontend Portal
cd src/udc_portal
npm install
npm run dev
```

### Seeding Demo Data

```bash
python scripts/seed_data.py
```

## Azure Container Apps Deployment

### 1. Authenticate

```bash
az login
az account set --subscription <subscription-id>
```

### 2. Deploy Infrastructure

```bash
cd infra/azure
./scripts/deploy.sh \
  --resource-group udc-rg \
  --environment production \
  --acr-name udcacr
```

This deploys:
- Azure Container Apps Environment
- 5 container apps (MetaCatalog, ContextVault, VisionLens, PolicyGuard, Orchestrator)
- Azure Key Vault with secrets
- Log Analytics + Application Insights

### 3. Build and Push Images

```bash
ACR_NAME=udcacr

# Python services
for svc in udc_metacatalog udc_contextvault udc_visionlens udc_desktopagent udc_policyguard udc_orchestrator; do
  az acr build --registry $ACR_NAME \
    --image $svc:latest \
    --file Dockerfile.python \
    --build-arg SERVICE_NAME=$svc .
done

# .NET Classifier
az acr build --registry $ACR_NAME \
  --image udc-classifier:latest \
  --file Dockerfile.dotnet .

# Portal
az acr build --registry $ACR_NAME \
  --image udc-portal:latest \
  --file src/udc_portal/Dockerfile \
  src/udc_portal/
```

### 4. Update Container Apps

```bash
for app in metacatalog contextvault visionlens policyguard orchestrator; do
  az containerapp update \
    --name udc-$app \
    --resource-group udc-rg \
    --image $ACR_NAME.azurecr.io/udc_$app:latest
done
```

## Environment Variables

See `.env.example` for the full list. Key groups:

| Group | Variables | Description |
|-------|-----------|-------------|
| PostgreSQL | `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` | Primary database |
| Redis | `REDIS_URL` | Cache and Pub/Sub |
| ChromaDB | `CHROMADB_URL` | Vector store |
| Azure OpenAI | `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_DEPLOYMENT_*` | LLM inference |
| Power BI | `POWERBI_TENANT_ID`, `POWERBI_CLIENT_ID`, `POWERBI_CLIENT_SECRET` | Dashboard rendering |
| SAP | `SAP_ODATA_BASE_URL`, `SAP_ODATA_USERNAME`, `SAP_ODATA_PASSWORD` | ERP connector |
| Fabric | `FABRIC_WORKSPACE_ID`, `FABRIC_LAKEHOUSE_ID`, `FABRIC_TENANT_ID` | Lakehouse connector |

## Monitoring

### Application Insights

All services emit structured logs (structlog for Python, Serilog for .NET) that stream to Application Insights via the Container Apps platform.

### Health Checks

Every service exposes `GET /health` returning:
```json
{
  "status": "healthy",
  "service": "udc-metacatalog",
  "version": "1.0.0",
  "uptime_seconds": 3600
}
```

Docker Compose uses these for container health checks. Azure Container Apps uses them for liveness/readiness probes.

### Log Analytics Queries

```kusto
// Error rate by service
ContainerAppConsoleLogs_CL
| where Log_s contains "ERROR"
| summarize count() by ContainerAppName_s, bin(TimeGenerated, 5m)

// Request latency P95
ContainerAppConsoleLogs_CL
| where Log_s contains "duration_ms"
| extend duration = extract("duration_ms=([0-9.]+)", 1, Log_s)
| summarize percentile(todouble(duration), 95) by ContainerAppName_s
```

## SSL/TLS

### Local Development
The nginx reverse proxy handles HTTP only in development. For HTTPS testing:
```bash
mkcert -install
mkcert localhost 127.0.0.1
# Update infra/docker/nginx.conf with cert paths
```

### Azure
Container Apps provides automatic TLS termination. Custom domains can be added via:
```bash
az containerapp hostname add \
  --name udc-orchestrator \
  --resource-group udc-rg \
  --hostname api.yourdomain.com
```
