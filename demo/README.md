# UDC Enterprise Platform — Self-Service Dashboard Builder Demo

## Instant Demo (1 command, no dependencies)

```bash
pip install fastapi uvicorn
python demo/mock_backend.py
# Open http://localhost:8006/demo
```

This launches a **self-contained HTML demo** with Chart.js visualizations — no React build, no Node.js, no database required.

---

## Full React Portal (2 commands)

### Terminal 1: Start Backend
```bash
cd udc-enterprise-platform
pip install fastapi uvicorn
python demo/mock_backend.py
```

### Terminal 2: Start Frontend
```bash
cd udc-enterprise-platform/src/udc_portal
npm install
npm run dev
```

### Open Browser
- **Dashboard Builder**: http://localhost:5173/dashboard
- **Data Catalog**: http://localhost:5173/
- **Pipeline Explorer**: http://localhost:5173/pipeline
- **Governance Center**: http://localhost:5173/governance
- **Chat**: http://localhost:5173/chat

---

## Demo Walkthrough — Self-Service Dashboard Builder for Business Users

### Scenario
You are a **Business Analyst** at a retail company with 57 stores across Southeast Asia. You want to create dashboards from your data without writing SQL or waiting for the data team.

### Step 1: Browse the Data Catalog
1. Open http://localhost:5173/
2. See **55 data assets** across 3 sources: PostgreSQL WMS (50), SAP S/4HANA (2), Microsoft Fabric (3)
3. Use the **search bar** to find "sales" or "inventory"
4. Click **source filter chips** (PostgreSQL / SAP / Fabric) to narrow results
5. Click a row to **expand column details** — see data types, PII classification, quality scores

### Step 2: Build a Dashboard (Natural Language)
1. Navigate to http://localhost:5173/dashboard
2. Select your role: **📊 Business Analyst**
3. Try these natural language prompts:

   **Sales Dashboard:**
   > "Show me a sales by region dashboard for Q4 2024 with top 10 stores"

   Generates a 6-visual dashboard:
   - Total Revenue by Region (bar chart)
   - Monthly Sales Trend (line chart)
   - Top 10 Stores by Revenue (bar chart)
   - Revenue KPI Card
   - Sales by Product Category (pie chart)
   - Average Order Value Trend (line chart)

   **Inventory Dashboard:**
   > "Build an inventory health dashboard with low-stock alerts and reorder points"

   Generates a 4-visual dashboard:
   - Stock Levels by Store
   - Low Stock Alerts (table)
   - Inventory Value by Category (pie)
   - Restock Frequency (line)

   **Customer Dashboard:**
   > "Create a customer loyalty analysis with tier breakdown and registration trends"

   Generates a 4-visual dashboard with **quality warning** (PII data quality < 70%)

   **Data Quality Dashboard:**
   > "Show me data quality scores across all sources with trend analysis"

### Step 3: Review Dashboard Preview
- The generated dashboard shows in a **visual grid layout**
- Each visual card shows: chart type icon, title, data source, measures, dimensions
- **Quality warnings** appear in yellow if any data source has quality < 70%
- History sidebar shows all previous requests

### Step 4: Explore Pipeline Lineage
1. Navigate to http://localhost:5173/pipeline
2. Select a pipeline (e.g., "WMS → Fabric Sales ETL")
3. View the **D3.js lineage graph** showing data flow:
   - WMS source tables → ETL transformations → Fabric targets
4. Click nodes to see details
5. View the quality scorecard at the bottom

### Step 5: Check Governance
1. Navigate to http://localhost:5173/governance
2. **Stats cards**: Total evaluations, approval rate, avg trust score
3. **Policies tab**: 5 active policies including PII Access Control, Quality Gate
4. **Audit Trail**: 50+ events with actor, action, resource, decision (allow/deny)
5. **Trust Scores**: User/service trust scores (0-1000) with factor breakdown

### Step 6: Chat with the Assistant
1. Navigate to http://localhost:5173/chat
2. Ask: "What can you help me with?"
3. Try: "Tell me about data quality across our sources"
4. Try: "Show me PII data in our catalog"

---

## Architecture in Action

```
Browser (React + TypeScript)         Mock Backend (FastAPI)
┌──────────────────────────┐        ┌──────────────────────────┐
│  Dashboard Builder Page  │  ──→   │  POST /api/workflow       │
│  - NL textarea           │  ←──   │  → keyword → template    │
│  - Role selector         │        │  → customize per prompt   │
│  - DashboardPreview      │        │  → return DashboardSpec   │
├──────────────────────────┤        ├──────────────────────────┤
│  Data Catalog Page       │  ──→   │  GET /api/meta/assets    │
│  - Search + filters      │  ←──   │  → 55 WMS/SAP/Fabric    │
│  - Column expansion      │        │    assets with columns   │
├──────────────────────────┤        ├──────────────────────────┤
│  Pipeline Explorer       │  ──→   │  GET /api/meta/lineage/  │
│  - D3 lineage graph      │  ←──   │  → 8 nodes, 6 edges     │
├──────────────────────────┤        ├──────────────────────────┤
│  Governance Center       │  ──→   │  GET /api/policy/*       │
│  - Policies / Audit /    │  ←──   │  → 5 policies, 50+ audit│
│    Trust Scores          │        │    events, 4 trust scores│
├──────────────────────────┤        ├──────────────────────────┤
│  Chat Interface          │  ──→   │  POST /api/chat          │
│  - Contextual responses  │  ←──   │  → keyword-based mock AI │
└──────────────────────────┘        └──────────────────────────┘
```

## Demo Data Summary

| Source | Assets | Stores | Tables |
|--------|--------|--------|--------|
| PostgreSQL WMS | 50 | 10 | orders, order_items, products, customers, inventory |
| SAP S/4HANA | 2 | — | A_SalesOrder, A_Product |
| Microsoft Fabric | 3 | — | sales_fact, store_dim, product_dim |
| **Total** | **55** | | |

| Governance | Count |
|---|---|
| Policies | 5 (PII, Quality Gate, Read-Only, Rate Limit, Fabric Approval) |
| Audit Events | 50+ |
| Trust Entities | 4 (3 users + 1 service) |
| Glossary Terms | 8 (GMV, AOV, SKU, Shrinkage, Fill Rate, Basket Size, COGS, Dwell Time) |

## Ports

| Service | Port | URL |
|---|---|---|
| Mock Backend | 8006 | http://localhost:8006/docs |
| Frontend Portal | 5173 | http://localhost:5173 |
