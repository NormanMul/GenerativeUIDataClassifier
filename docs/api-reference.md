# UDC Enterprise Platform — API Reference

## Service Endpoints

All services expose interactive API documentation via Swagger/OpenAPI when running locally.

| Service | Base URL | Docs URL | Protocol |
|---------|----------|----------|----------|
| UDC Classifier | `http://localhost:8080` | [Swagger UI](http://localhost:8080/swagger) | REST + gRPC (:50051) |
| UDC MetaCatalog | `http://localhost:8001` | [FastAPI Docs](http://localhost:8001/docs) | REST + gRPC (:50052) |
| UDC ContextVault | `http://localhost:8002` | [FastAPI Docs](http://localhost:8002/docs) | REST + gRPC (:50053) |
| UDC VisionLens | `http://localhost:8003` | [FastAPI Docs](http://localhost:8003/docs) | REST + gRPC (:50054) |
| UDC DesktopAgent | `http://localhost:8004` | [FastAPI Docs](http://localhost:8004/docs) | REST + WebSocket + gRPC (:50055) |
| UDC PolicyGuard | `http://localhost:8005` | [FastAPI Docs](http://localhost:8005/docs) | REST + gRPC (:50056) |
| UDC Orchestrator | `http://localhost:8006` | [FastAPI Docs](http://localhost:8006/docs) | REST + SSE |
| UDC Portal | `http://localhost:5173` | — | Web UI |
| Nginx Gateway | `http://localhost:80` | — | Reverse Proxy |

## Authentication

All API requests require one of:

1. **API Key**: `X-API-Key` header with valid key from the `api_keys` table
2. **Bearer Token**: `Authorization: Bearer <JWT>` with Azure AD Service Principal token

Public paths excluded from authentication:
- `GET /health`
- `GET /docs`
- `GET /openapi.json`

## Common Response Format

```json
{
  "data": { ... },
  "meta": {
    "request_id": "uuid",
    "timestamp": "2024-01-01T00:00:00Z",
    "duration_ms": 42
  }
}
```

## Key Endpoints

### Classifier
- `POST /api/classify` — Classify a single data asset
- `POST /api/classify/batch` — Batch classification
- `POST /api/pipeline/document` — Document a pipeline (UC-2)
- `POST /api/dashboard/generate` — Generate dashboard spec (UC-4)
- `POST /api/quality/validate` — Run quality gate

### MetaCatalog
- `GET /api/meta/assets` — List data assets (paginated)
- `POST /api/meta/assets` — Register a new asset
- `GET /api/meta/assets/{id}` — Get asset details
- `GET /api/meta/lineage/{asset_id}` — Get lineage graph
- `GET /api/meta/glossary` — List glossary terms
- `POST /api/meta/glossary` — Create glossary term
- `GET /api/meta/quality/{asset_id}` — Get latest quality report
- `GET /api/meta/search?q={query}` — Full-text search

### ContextVault
- `POST /api/context/store` — Store a document
- `GET /api/context/retrieve?query={q}` — Semantic retrieval
- `GET /api/context/session/{id}` — Get session context
- `POST /api/context/session` — Create new session

### VisionLens
- `POST /api/vision/analyze` — Analyze screenshot (multipart)
- `POST /api/vision/ground` — Ground text to coordinates

### DesktopAgent
- `POST /api/desktop/task` — Execute a desktop task
- `GET /api/desktop/task/{id}` — Get task status
- `WS /api/desktop/stream` — Real-time desktop feed

### PolicyGuard
- `POST /api/policy/evaluate` — Evaluate action against policies
- `GET /api/policy/audit` — Get audit trail
- `GET /api/policy/trust/{entity}` — Get trust score

### Orchestrator
- `POST /api/workflow` — Execute a workflow
- `GET /api/workflow/{id}` — Get workflow status
- `POST /api/chat` — Chat with Copilot (SSE streaming)

## gRPC Services

Proto definitions in `shared/proto/`. Each service listens on its gRPC port:

```
classifier.proto  → :50051 — ClassifierService
metadata.proto    → :50052 — MetadataService
context.proto     → :50053 — ContextService
vision.proto      → :50054 — VisionService
desktop.proto     → :50055 — DesktopService
policy.proto      → :50056 — PolicyService
```

## Generating OpenAPI Specs

```bash
python scripts/generate_openapi.py
```

Exports JSON specs to `docs/openapi/{service}.json`.
