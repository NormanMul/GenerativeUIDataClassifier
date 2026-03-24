# UDC Enterprise Platform — Architecture

## System Context

The UDC Enterprise Platform is a modular monorepo consisting of **6 integrated subsystems** designed for enterprise retail data management. It targets organizations running 57–100 stores with PostgreSQL-based WMS, SAP S/4HANA ERP, and Microsoft Fabric Lakehouse.

```mermaid
graph TB
    subgraph Users["👤 Users"]
        BA["🧑‍💼 Business Analyst<br/><small>Dashboards & data exploration</small>"]
        DE["🧑‍💻 Data Engineer<br/><small>Pipelines & lineage</small>"]
        DS["🛡️ Data Steward<br/><small>Governance & quality</small>"]
    end

    subgraph UDC["UDC Enterprise Platform"]
        Portal["🌐 UDC Portal<br/><small>React SPA</small>"]
        Orch["⚡ Orchestrator<br/><small>Copilot SDK Gateway</small>"]

        subgraph Core["AI & Data Services"]
            Classifier["🤖 Classifier<br/><small>.NET Semantic Kernel</small>"]
            Meta["📂 MetaCatalog<br/><small>Metadata & Lineage</small>"]
            Context["🧠 ContextVault<br/><small>Memory & Vectors</small>"]
            Policy["🛡️ PolicyGuard<br/><small>Governance & Audit</small>"]
        end

        subgraph Desktop["Desktop Automation"]
            Vision["👁️ VisionLens<br/><small>Screen Parsing</small>"]
            Agent["🖥️ DesktopAgent<br/><small>Automation</small>"]
        end
    end

    subgraph External["External Systems"]
        PG[("🐘 PostgreSQL WMS<br/><small>57-100 stores</small>")]
        SAP["📦 SAP S/4HANA<br/><small>ERP — OData</small>"]
        Fabric["🔷 MS Fabric<br/><small>Lakehouse</small>"]
        AOAI["🧠 Azure OpenAI<br/><small>GPT-4o</small>"]
        PBI["📊 Power BI<br/><small>Dashboards</small>"]
    end

    BA & DE & DS --> Portal
    Portal -->|REST / WS| Orch
    Orch -->|gRPC| Classifier
    Orch -->|gRPC| Meta
    Orch -->|gRPC| Context
    Orch -->|gRPC| Policy
    Agent -->|gRPC| Vision
    Meta -->|SQL| PG
    Classifier -->|OData| SAP
    Classifier -->|REST| Fabric
    Classifier -->|HTTPS| AOAI
    Classifier -->|REST| PBI

    style UDC fill:#1e3a5f,stroke:#3b82f6,color:#fff
    style Core fill:#1e40af,stroke:#60a5fa,color:#fff
    style Desktop fill:#1e40af,stroke:#60a5fa,color:#fff
    style Users fill:#f0f9ff,stroke:#3b82f6,color:#1e3a5f
    style External fill:#fefce8,stroke:#ca8a04,color:#713f12
```

## Container Diagram

```mermaid
graph LR
    subgraph Frontend
        Portal["🌐 React Portal<br/><small>TypeScript + Vite + TailwindCSS</small>"]
    end

    subgraph Gateway
        Nginx["Nginx<br/><small>Reverse Proxy</small>"]
        Orch["Orchestrator<br/><small>FastAPI + Copilot SDK</small>"]
    end

    subgraph Services["Backend Services"]
        Classifier[".NET Classifier<br/><small>Semantic Kernel</small>"]
        Meta["MetaCatalog<br/><small>FastAPI + SQLAlchemy</small>"]
        Context["ContextVault<br/><small>FastAPI + ChromaDB</small>"]
        Policy["PolicyGuard<br/><small>FastAPI</small>"]
        Vision["VisionLens<br/><small>FastAPI + YOLO</small>"]
        Desktop["DesktopAgent<br/><small>FastAPI + VNC</small>"]
    end

    subgraph Data["Data Stores"]
        PG[("PostgreSQL 16")]
        Redis[("Redis 7")]
        Chroma[("ChromaDB")]
    end

    Portal -->|HTTPS| Nginx
    Nginx --> Orch
    Orch -->|":50051"| Classifier
    Orch -->|":50052"| Meta
    Orch -->|":50053"| Context
    Orch -->|":50054"| Policy
    Desktop -->|":50055"| Vision
    Meta --> PG
    Context --> PG
    Context --> Chroma
    Policy --> PG
    Orch --> Redis
    Meta --> Redis

    style Frontend fill:#0ea5e9,stroke:#0284c7,color:#fff
    style Gateway fill:#8b5cf6,stroke:#7c3aed,color:#fff
    style Services fill:#1e40af,stroke:#3b82f6,color:#fff
    style Data fill:#059669,stroke:#047857,color:#fff
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
