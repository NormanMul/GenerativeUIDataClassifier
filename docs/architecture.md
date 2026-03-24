# UDC Enterprise Platform — Architecture

## System Context

The UDC Enterprise Platform is a modular monorepo consisting of **6 integrated subsystems** designed for enterprise retail data management. It targets organizations running 57–100 stores with PostgreSQL-based WMS, SAP S/4HANA ERP, and Microsoft Fabric Lakehouse.

```mermaid
C4Context
    title System Context — UDC Enterprise Platform

    Person(analyst, "Business Analyst", "Requests dashboards, queries catalog")
    Person(engineer, "Data Engineer", "Documents pipelines, tracks lineage")
    Person(steward, "Data Steward", "Manages governance, glossary, quality")

    System_Boundary(udc, "UDC Enterprise Platform") {
        System(orchestrator, "UDC Orchestrator", "Copilot-powered workflow engine")
    }

    System_Ext(wms, "PostgreSQL WMS", "57-100 store databases")
    System_Ext(sap, "SAP S/4HANA", "ERP OData API")
    System_Ext(fabric, "Microsoft Fabric", "Lakehouse / OneLake")
    System_Ext(azure, "Azure OpenAI", "GPT-4o / Embeddings")
    System_Ext(powerbi, "Power BI REST API", "Dashboard rendering")

    Rel(analyst, orchestrator, "Natural language requests")
    Rel(engineer, orchestrator, "Pipeline documentation")
    Rel(steward, orchestrator, "Policy & glossary management")
    Rel(orchestrator, wms, "SQL queries")
    Rel(orchestrator, sap, "OData calls")
    Rel(orchestrator, fabric, "OneLake REST")
    Rel(orchestrator, azure, "LLM inference")
    Rel(orchestrator, powerbi, "Dashboard creation")
```

## Container Diagram

```mermaid
C4Container
    title Container Diagram — UDC Enterprise Platform

    Container(portal, "UDC Portal", "React 18 / TypeScript", "Web interface for all users")
    Container(orchestrator, "UDC Orchestrator", "Python / FastAPI", "Copilot bridge + workflow engine")
    Container(classifier, "UDC Classifier", ".NET 8 / Semantic Kernel", "AI data classification agents")
    Container(metacatalog, "UDC MetaCatalog", "Python / FastAPI", "Metadata, lineage, glossary, quality")
    Container(contextvault, "UDC ContextVault", "Python / FastAPI", "3-layer context management")
    Container(visionlens, "UDC VisionLens", "Python / FastAPI", "Screen parsing + OCR + captioning")
    Container(desktopagent, "UDC DesktopAgent", "Python / FastAPI", "Desktop automation via VNC")
    Container(policyguard, "UDC PolicyGuard", "Python / FastAPI", "Governance, trust scoring, audit")

    ContainerDb(postgres, "PostgreSQL 16", "Primary database")
    ContainerDb(redis, "Redis 7", "Cache + Pub/Sub")
    ContainerDb(chromadb, "ChromaDB", "Vector store")

    Rel(portal, orchestrator, "REST / SSE", "/api/chat, /api/workflow")
    Rel(orchestrator, classifier, "gRPC", "Classification requests")
    Rel(orchestrator, metacatalog, "gRPC", "Metadata operations")
    Rel(orchestrator, contextvault, "gRPC", "Context retrieval")
    Rel(orchestrator, visionlens, "gRPC", "Screen analysis")
    Rel(orchestrator, desktopagent, "gRPC + WebSocket", "Desktop actions")
    Rel(orchestrator, policyguard, "gRPC", "Policy evaluation")
    Rel(metacatalog, postgres, "asyncpg")
    Rel(contextvault, chromadb, "HTTP")
    Rel(policyguard, postgres, "asyncpg")
```

## Subsystem Descriptions

### 1. UDC Classifier (.NET 8 / Semantic Kernel)
AI agent for data classification. Uses Semantic Kernel to orchestrate skills for profiling, schema inference, lineage tracking, and dashboard generation. Agents: ClassifierAgent, PipelineDocAgent, DashboardBuilderAgent, QualityGateAgent.

### 2. UDC MetaCatalog (Python / FastAPI)
Central metadata repository. Manages data assets, column profiles, lineage graphs, business glossary terms, KPI formulas, and quality reports. Provides ingesters for PostgreSQL, SAP, and Fabric sources.

### 3. UDC ContextVault (Python / FastAPI)
Three-layer context management: L0 (raw documents), L1 (curated chunks), L2 (synthesized summaries). Uses ChromaDB for vector search, Redis for caching, addressable via `vault://` URIs.

### 4. UDC VisionLens (Python / FastAPI)
Screen understanding pipeline: YOLO element detection → Azure AI Vision OCR → VLM captioning → NL grounding. Processes desktop screenshots for the Desktop Agent.

### 5. UDC DesktopAgent (Python / FastAPI)
Autonomous desktop automation using Perceive-Plan-Act-Reflect loop. Operates via VNC bridge in containerized Ubuntu+LXDE environment. Supports Chrome, LibreOffice, SAP GUI.

### 6. UDC PolicyGuard (Python / FastAPI)
Governance engine with deterministic policy evaluation (<1ms), trust scoring (0–1000), sandboxed preview, and append-only audit logging. Evaluates all actions before execution.

## Communication Patterns

| Pattern | Protocol | Use |
|---------|----------|-----|
| Synchronous internal | gRPC (Protobuf) | Service-to-service calls |
| Synchronous external | REST (OpenAPI 3.1) | Portal → Orchestrator |
| Async events | Redis Pub/Sub | Asset registration, quality reports |
| Streaming | SSE (Server-Sent Events) | Chat responses to portal |
| Desktop control | WebSocket | Real-time desktop agent feedback |

## Data Flow: Use Case 2 — Pipeline Documentation

```mermaid
sequenceDiagram
    participant U as Data Engineer
    participant O as Orchestrator
    participant MC as MetaCatalog
    participant CV as ContextVault
    participant CL as Classifier
    participant PG as PolicyGuard

    U->>O: "Document the inventory pipeline"
    O->>MC: Discover data sources
    MC-->>O: Asset list
    O->>CL: Profile & classify columns
    CL-->>O: Classification results
    O->>MC: Extract lineage (SQL parsing)
    MC-->>O: Lineage graph
    O->>MC: Auto-tag with glossary
    MC-->>O: Updated assets
    O->>PG: Quality gate check
    PG-->>O: Pass/fail + trust score
    O->>MC: Publish quality report
    O->>CV: Cache documentation
    O-->>U: HTML report + lineage visualization
```

## Data Flow: Use Case 4 — Dashboard Builder

```mermaid
sequenceDiagram
    participant U as Business Analyst
    participant O as Orchestrator
    participant CL as Classifier
    participant MC as MetaCatalog
    participant CV as ContextVault
    participant PG as PolicyGuard

    U->>O: "Build a sales by region dashboard"
    O->>CL: Parse NL request → intent
    CL-->>O: Dashboard spec draft
    O->>MC: Resolve data sources & KPIs
    MC-->>O: Matched assets + formulas
    O->>CV: Retrieve relevant context
    CV-->>O: Related docs & history
    O->>PG: Validate data access policy
    PG-->>O: Approved
    O->>MC: Check data quality
    MC-->>O: Quality scores
    O->>CL: Generate final dashboard spec
    CL-->>O: Power BI / HTML spec
    O-->>U: Rendered dashboard
```
