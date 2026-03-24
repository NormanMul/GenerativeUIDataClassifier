"""UDC Enterprise Platform — Self-Service Dashboard Builder Demo.

A standalone mock backend that serves all API endpoints needed for the
Dashboard Builder demo with realistic retail / WMS data.
No external dependencies (PostgreSQL, Redis, Azure OpenAI) required.

Run:
    pip install fastapi uvicorn
    python demo/mock_backend.py

Then start the portal:
    cd src/udc_portal && npm run dev
"""

from __future__ import annotations

import asyncio
import json
import random
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse

app = FastAPI(title="UDC Demo — Mock Backend", version="demo-1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ═══════════════════════════════════════════════════════════════════════
# DEMO DATA — realistic retail / WMS for Southeast Asia
# ═══════════════════════════════════════════════════════════════════════

STORES = [f"store_{i:03d}" for i in range(1, 58)]

DEMO_ASSETS: list[dict[str, Any]] = []
DEMO_GLOSSARY: list[dict[str, Any]] = []
DEMO_POLICIES: list[dict[str, Any]] = []
DEMO_AUDIT: list[dict[str, Any]] = []
DEMO_PIPELINES: list[dict[str, Any]] = []


def _build_demo_data() -> None:
    """Populate in-memory demo data on startup."""
    random.seed(42)

    # ── Data Assets (WMS tables across stores) ─────────────────────
    table_defs: list[dict[str, Any]] = [
        {
            "name": "orders",
            "desc": "POS sales transactions",
            "tags": ["wms", "sales", "transactions"],
            "columns": [
                {"name": "order_id", "data_type": "uuid", "nullable": False, "classification": "identifier", "pii_detected": False},
                {"name": "store_id", "data_type": "varchar", "nullable": False, "classification": "operational", "pii_detected": False},
                {"name": "customer_id", "data_type": "uuid", "nullable": True, "classification": "identifier", "pii_detected": False},
                {"name": "order_date", "data_type": "timestamptz", "nullable": False, "classification": "temporal", "pii_detected": False},
                {"name": "total_amount", "data_type": "numeric(12,2)", "nullable": False, "classification": "financial", "pii_detected": False},
                {"name": "payment_method", "data_type": "varchar(20)", "nullable": False, "classification": "operational", "pii_detected": False},
                {"name": "region", "data_type": "varchar(50)", "nullable": False, "classification": "geographical", "pii_detected": False},
            ],
        },
        {
            "name": "order_items",
            "desc": "Line items for each order",
            "tags": ["wms", "sales", "line-items"],
            "columns": [
                {"name": "item_id", "data_type": "uuid", "nullable": False, "classification": "identifier", "pii_detected": False},
                {"name": "order_id", "data_type": "uuid", "nullable": False, "classification": "identifier", "pii_detected": False},
                {"name": "product_id", "data_type": "uuid", "nullable": False, "classification": "identifier", "pii_detected": False},
                {"name": "quantity", "data_type": "integer", "nullable": False, "classification": "measurement", "pii_detected": False},
                {"name": "unit_price", "data_type": "numeric(10,2)", "nullable": False, "classification": "financial", "pii_detected": False},
                {"name": "discount_pct", "data_type": "numeric(5,2)", "nullable": True, "classification": "financial", "pii_detected": False},
            ],
        },
        {
            "name": "products",
            "desc": "Product catalog master data",
            "tags": ["wms", "master-data", "products"],
            "columns": [
                {"name": "product_id", "data_type": "uuid", "nullable": False, "classification": "identifier", "pii_detected": False},
                {"name": "sku", "data_type": "varchar(30)", "nullable": False, "classification": "operational", "pii_detected": False},
                {"name": "product_name", "data_type": "varchar(255)", "nullable": False, "classification": "descriptive", "pii_detected": False},
                {"name": "category", "data_type": "varchar(100)", "nullable": False, "classification": "categorical", "pii_detected": False},
                {"name": "brand", "data_type": "varchar(100)", "nullable": True, "classification": "categorical", "pii_detected": False},
                {"name": "cost_price", "data_type": "numeric(10,2)", "nullable": False, "classification": "financial", "pii_detected": False},
                {"name": "retail_price", "data_type": "numeric(10,2)", "nullable": False, "classification": "financial", "pii_detected": False},
            ],
        },
        {
            "name": "customers",
            "desc": "Customer records — contains PII",
            "tags": ["wms", "customers", "pii"],
            "columns": [
                {"name": "customer_id", "data_type": "uuid", "nullable": False, "classification": "identifier", "pii_detected": False},
                {"name": "full_name", "data_type": "varchar(255)", "nullable": False, "classification": "pii", "pii_detected": True, "description": "PII: Personal name"},
                {"name": "email", "data_type": "varchar(255)", "nullable": True, "classification": "pii", "pii_detected": True, "description": "PII: Email address"},
                {"name": "phone", "data_type": "varchar(20)", "nullable": True, "classification": "pii", "pii_detected": True, "description": "PII: Phone number"},
                {"name": "ic_number", "data_type": "varchar(20)", "nullable": True, "classification": "pii", "pii_detected": True, "description": "PII: National ID (IC/NRIC)"},
                {"name": "city", "data_type": "varchar(100)", "nullable": True, "classification": "geographical", "pii_detected": False},
                {"name": "loyalty_tier", "data_type": "varchar(20)", "nullable": True, "classification": "categorical", "pii_detected": False},
                {"name": "registered_at", "data_type": "timestamptz", "nullable": False, "classification": "temporal", "pii_detected": False},
            ],
        },
        {
            "name": "inventory",
            "desc": "Real-time stock levels per store",
            "tags": ["wms", "inventory", "stock"],
            "columns": [
                {"name": "inventory_id", "data_type": "uuid", "nullable": False, "classification": "identifier", "pii_detected": False},
                {"name": "store_id", "data_type": "varchar(10)", "nullable": False, "classification": "operational", "pii_detected": False},
                {"name": "product_id", "data_type": "uuid", "nullable": False, "classification": "identifier", "pii_detected": False},
                {"name": "quantity_on_hand", "data_type": "integer", "nullable": False, "classification": "measurement", "pii_detected": False},
                {"name": "reorder_point", "data_type": "integer", "nullable": False, "classification": "threshold", "pii_detected": False},
                {"name": "last_restocked", "data_type": "timestamptz", "nullable": True, "classification": "temporal", "pii_detected": False},
            ],
        },
    ]

    # SAP & Fabric assets
    sap_assets = [
        {"name": "A_SalesOrder", "desc": "SAP S/4HANA sales orders", "source": "SAP", "db": "S4HANA", "schema": "sap", "tags": ["sap", "sales"],
         "columns": [
             {"name": "SalesOrder", "data_type": "string", "nullable": False, "classification": "identifier", "pii_detected": False},
             {"name": "SoldToParty", "data_type": "string", "nullable": False, "classification": "identifier", "pii_detected": False},
             {"name": "TotalNetAmount", "data_type": "decimal", "nullable": False, "classification": "financial", "pii_detected": False},
             {"name": "TransactionCurrency", "data_type": "string", "nullable": False, "classification": "operational", "pii_detected": False},
             {"name": "SalesOrderDate", "data_type": "date", "nullable": False, "classification": "temporal", "pii_detected": False},
         ]},
        {"name": "A_Product", "desc": "SAP material master", "source": "SAP", "db": "S4HANA", "schema": "sap", "tags": ["sap", "products"],
         "columns": [
             {"name": "Product", "data_type": "string", "nullable": False, "classification": "identifier", "pii_detected": False},
             {"name": "ProductType", "data_type": "string", "nullable": False, "classification": "categorical", "pii_detected": False},
             {"name": "BaseUnit", "data_type": "string", "nullable": False, "classification": "operational", "pii_detected": False},
         ]},
    ]

    fabric_assets = [
        {"name": "sales_fact", "desc": "Fabric Lakehouse — consolidated sales fact table", "source": "Fabric", "db": "udc_lakehouse", "schema": "dbo", "tags": ["fabric", "sales", "fact"],
         "columns": [
             {"name": "sale_date", "data_type": "date", "nullable": False, "classification": "temporal", "pii_detected": False},
             {"name": "store_id", "data_type": "string", "nullable": False, "classification": "operational", "pii_detected": False},
             {"name": "product_id", "data_type": "string", "nullable": False, "classification": "identifier", "pii_detected": False},
             {"name": "quantity_sold", "data_type": "long", "nullable": False, "classification": "measurement", "pii_detected": False},
             {"name": "revenue", "data_type": "double", "nullable": False, "classification": "financial", "pii_detected": False},
             {"name": "region", "data_type": "string", "nullable": False, "classification": "geographical", "pii_detected": False},
         ]},
        {"name": "store_dim", "desc": "Fabric Lakehouse — store dimension", "source": "Fabric", "db": "udc_lakehouse", "schema": "dbo", "tags": ["fabric", "dimension", "store"],
         "columns": [
             {"name": "store_id", "data_type": "string", "nullable": False, "classification": "identifier", "pii_detected": False},
             {"name": "store_name", "data_type": "string", "nullable": False, "classification": "descriptive", "pii_detected": False},
             {"name": "region", "data_type": "string", "nullable": False, "classification": "geographical", "pii_detected": False},
             {"name": "city", "data_type": "string", "nullable": False, "classification": "geographical", "pii_detected": False},
             {"name": "country", "data_type": "string", "nullable": False, "classification": "geographical", "pii_detected": False},
             {"name": "open_date", "data_type": "date", "nullable": False, "classification": "temporal", "pii_detected": False},
         ]},
        {"name": "product_dim", "desc": "Fabric Lakehouse — product dimension", "source": "Fabric", "db": "udc_lakehouse", "schema": "dbo", "tags": ["fabric", "dimension", "product"],
         "columns": [
             {"name": "product_id", "data_type": "string", "nullable": False, "classification": "identifier", "pii_detected": False},
             {"name": "product_name", "data_type": "string", "nullable": False, "classification": "descriptive", "pii_detected": False},
             {"name": "category", "data_type": "string", "nullable": False, "classification": "categorical", "pii_detected": False},
             {"name": "brand", "data_type": "string", "nullable": False, "classification": "categorical", "pii_detected": False},
         ]},
    ]

    # Build WMS assets for a subset of stores
    for store in STORES[:10]:  # 10 stores for demo
        for tdef in table_defs:
            DEMO_ASSETS.append({
                "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{store}.{tdef['name']}")),
                "name": tdef["name"],
                "source_type": "PostgreSQL",
                "database": f"{store}_wms",
                "schema": "public",
                "quality_score": round(random.uniform(65, 99), 1),
                "tags": tdef["tags"] + [store],
                "updated_at": (datetime.now(timezone.utc) - timedelta(hours=random.randint(1, 72))).isoformat(),
                "columns": tdef["columns"],
                "description": tdef["desc"],
                "row_count": random.randint(5000, 500000),
            })

    # SAP assets
    for sa in sap_assets:
        DEMO_ASSETS.append({
            "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, f"sap.{sa['name']}")),
            "name": sa["name"],
            "source_type": "SAP",
            "database": sa["db"],
            "schema": sa["schema"],
            "quality_score": round(random.uniform(80, 98), 1),
            "tags": sa["tags"],
            "updated_at": (datetime.now(timezone.utc) - timedelta(hours=random.randint(1, 48))).isoformat(),
            "columns": sa["columns"],
            "description": sa["desc"],
            "row_count": random.randint(10000, 1000000),
        })

    # Fabric assets
    for fa in fabric_assets:
        DEMO_ASSETS.append({
            "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, f"fabric.{fa['name']}")),
            "name": fa["name"],
            "source_type": "Fabric",
            "database": fa["db"],
            "schema": fa["schema"],
            "quality_score": round(random.uniform(85, 99), 1),
            "tags": fa["tags"],
            "updated_at": (datetime.now(timezone.utc) - timedelta(hours=random.randint(1, 24))).isoformat(),
            "columns": fa["columns"],
            "description": fa["desc"],
            "row_count": random.randint(100000, 5000000),
        })

    # ── Glossary Terms ──────────────────────────────────────────────
    DEMO_GLOSSARY.extend([
        {"id": str(uuid.uuid4()), "term": "GMV", "definition": "Gross Merchandise Value — total sales value before deductions", "domain": "Finance", "owner": "Finance Team"},
        {"id": str(uuid.uuid4()), "term": "AOV", "definition": "Average Order Value — mean transaction value", "domain": "Sales", "owner": "Sales Analytics"},
        {"id": str(uuid.uuid4()), "term": "SKU", "definition": "Stock Keeping Unit — unique product variant identifier", "domain": "Inventory", "owner": "Product Team"},
        {"id": str(uuid.uuid4()), "term": "Shrinkage", "definition": "Inventory loss from theft, damage, or administrative error", "domain": "Inventory", "owner": "Loss Prevention"},
        {"id": str(uuid.uuid4()), "term": "Fill Rate", "definition": "Percentage of orders fulfilled from available stock", "domain": "Operations", "owner": "Supply Chain"},
        {"id": str(uuid.uuid4()), "term": "Basket Size", "definition": "Average number of items per transaction", "domain": "Sales", "owner": "Sales Analytics"},
        {"id": str(uuid.uuid4()), "term": "COGS", "definition": "Cost of Goods Sold — direct production costs", "domain": "Finance", "owner": "Finance Team"},
        {"id": str(uuid.uuid4()), "term": "Dwell Time", "definition": "Average customer time spent in store", "domain": "Operations", "owner": "Store Ops"},
    ])

    # ── Policies ────────────────────────────────────────────────────
    DEMO_POLICIES.extend([
        {"id": str(uuid.uuid4()), "name": "PII Access Control", "type": "data_access", "description": "Restricts access to PII columns based on user role", "effect": "deny", "severity": "critical", "enabled": True, "conditions": {"classification": "pii", "role_not_in": ["Data Steward"]}},
        {"id": str(uuid.uuid4()), "name": "Dashboard Data Quality Gate", "type": "quality_gate", "description": "Requires minimum 70% quality score for dashboard data sources", "effect": "deny", "severity": "high", "enabled": True, "conditions": {"quality_score_min": 0.7}},
        {"id": str(uuid.uuid4()), "name": "Read-Only Analyst Access", "type": "action_allowlist", "description": "Business Analysts can only read data, not modify", "effect": "allow", "severity": "medium", "enabled": True, "conditions": {"role": "Business Analyst", "actions": ["read", "dashboard"]}},
        {"id": str(uuid.uuid4()), "name": "Export Rate Limit", "type": "rate_limit", "description": "Maximum 100 data exports per hour per user", "effect": "deny", "severity": "medium", "enabled": True, "conditions": {"max_per_hour": 100}},
        {"id": str(uuid.uuid4()), "name": "Fabric Source Approval", "type": "environment_restriction", "description": "Fabric data access requires Data Engineer or Steward role", "effect": "deny", "severity": "high", "enabled": True, "conditions": {"source_type": "Fabric", "role_in": ["Data Engineer", "Data Steward"]}},
    ])

    # ── Audit Trail ─────────────────────────────────────────────────
    actors = ["alice@contoso.com", "bob@contoso.com", "carol@contoso.com", "dave@contoso.com"]
    actions = ["dashboard.generate", "asset.view", "lineage.query", "quality.check", "policy.evaluate", "glossary.lookup"]
    resources = ["sales_fact", "orders", "customers", "inventory", "A_SalesOrder", "product_dim"]
    for i in range(50):
        decision = "allow" if random.random() > 0.15 else "deny"
        DEMO_AUDIT.append({
            "id": str(uuid.uuid4()),
            "timestamp": (datetime.now(timezone.utc) - timedelta(minutes=random.randint(1, 4320))).isoformat(),
            "actor": random.choice(actors),
            "action": random.choice(actions),
            "resource": random.choice(resources),
            "decision": decision,
            "details": "Policy: PII Access Control" if decision == "deny" else None,
        })
    DEMO_AUDIT.sort(key=lambda x: x["timestamp"], reverse=True)

    # ── Pipelines ───────────────────────────────────────────────────
    DEMO_PIPELINES.extend([
        {"id": str(uuid.uuid4()), "name": "WMS → Fabric Sales ETL", "description": "Extracts orders from 57 WMS stores, transforms, loads to Fabric sales_fact", "source_count": 57, "quality_score": 92.3, "last_run": (datetime.now(timezone.utc) - timedelta(hours=6)).isoformat()},
        {"id": str(uuid.uuid4()), "name": "Inventory Replenishment Pipeline", "description": "Daily inventory sync across all stores, calculates reorder points", "source_count": 57, "quality_score": 88.7, "last_run": (datetime.now(timezone.utc) - timedelta(hours=12)).isoformat()},
        {"id": str(uuid.uuid4()), "name": "SAP Material Master Sync", "description": "Syncs product master data from SAP S/4HANA to Fabric product_dim", "source_count": 1, "quality_score": 95.1, "last_run": (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()},
        {"id": str(uuid.uuid4()), "name": "Customer 360 Pipeline", "description": "Consolidates customer data for loyalty analytics — PII handling required", "source_count": 58, "quality_score": 78.5, "last_run": (datetime.now(timezone.utc) - timedelta(hours=3)).isoformat()},
    ])


_build_demo_data()


# ═══════════════════════════════════════════════════════════════════════
# DASHBOARD BUILDER — AI-like mock response generation
# ═══════════════════════════════════════════════════════════════════════

DASHBOARD_TEMPLATES: dict[str, dict[str, Any]] = {
    "sales": {
        "title": "Sales Performance Dashboard",
        "description": "Regional sales analysis across 57 stores — generated by UDC AI from your request.",
        "data_sources": ["sales_fact", "store_dim", "orders"],
        "visuals": [
            {"id": "v1", "title": "Total Revenue by Region", "chart_type": "bar", "data_source": "sales_fact", "measures": ["SUM(revenue)"], "dimensions": ["region"]},
            {"id": "v2", "title": "Monthly Sales Trend", "chart_type": "line", "data_source": "sales_fact", "measures": ["SUM(revenue)"], "dimensions": ["sale_date"]},
            {"id": "v3", "title": "Top 10 Stores by Revenue", "chart_type": "bar", "data_source": "sales_fact", "measures": ["SUM(revenue)"], "dimensions": ["store_id"], "filters": {"top_n": 10}},
            {"id": "v4", "title": "Revenue KPI Card", "chart_type": "card", "data_source": "sales_fact", "measures": ["SUM(revenue)", "COUNT(DISTINCT store_id)"], "dimensions": []},
            {"id": "v5", "title": "Sales by Product Category", "chart_type": "pie", "data_source": "sales_fact", "measures": ["SUM(revenue)"], "dimensions": ["category"]},
            {"id": "v6", "title": "Average Order Value Trend", "chart_type": "line", "data_source": "orders", "measures": ["AVG(total_amount)"], "dimensions": ["order_date"]},
        ],
        "layout": {"columns": 3, "rows": 2},
    },
    "inventory": {
        "title": "Inventory Health Dashboard",
        "description": "Stock levels, shrinkage analysis, and reorder alerts across all stores.",
        "data_sources": ["inventory", "products", "store_dim"],
        "visuals": [
            {"id": "v1", "title": "Stock Levels by Store", "chart_type": "bar", "data_source": "inventory", "measures": ["SUM(quantity_on_hand)"], "dimensions": ["store_id"]},
            {"id": "v2", "title": "Low Stock Alerts", "chart_type": "table", "data_source": "inventory", "measures": ["quantity_on_hand", "reorder_point"], "dimensions": ["store_id", "product_id"], "filters": {"below_reorder": True}},
            {"id": "v3", "title": "Inventory Value by Category", "chart_type": "pie", "data_source": "inventory", "measures": ["SUM(quantity_on_hand * cost_price)"], "dimensions": ["category"]},
            {"id": "v4", "title": "Restock Frequency", "chart_type": "line", "data_source": "inventory", "measures": ["COUNT(last_restocked)"], "dimensions": ["last_restocked"]},
        ],
        "layout": {"columns": 2, "rows": 2},
    },
    "customer": {
        "title": "Customer Insights Dashboard",
        "description": "Customer segmentation, loyalty analysis, and regional demographics.",
        "data_sources": ["customers", "orders", "store_dim"],
        "visuals": [
            {"id": "v1", "title": "Customers by Loyalty Tier", "chart_type": "pie", "data_source": "customers", "measures": ["COUNT(customer_id)"], "dimensions": ["loyalty_tier"]},
            {"id": "v2", "title": "New Registrations (Monthly)", "chart_type": "line", "data_source": "customers", "measures": ["COUNT(customer_id)"], "dimensions": ["registered_at"]},
            {"id": "v3", "title": "Customer Distribution by City", "chart_type": "bar", "data_source": "customers", "measures": ["COUNT(customer_id)"], "dimensions": ["city"]},
            {"id": "v4", "title": "Top Customers by Spend", "chart_type": "table", "data_source": "orders", "measures": ["SUM(total_amount)"], "dimensions": ["customer_id"], "filters": {"top_n": 20}},
        ],
        "layout": {"columns": 2, "rows": 2},
        "quality_warnings": ["customers table quality score is 67.2% — PII fields have 5% null rate"],
    },
    "quality": {
        "title": "Data Quality Dashboard",
        "description": "Overview of data quality scores, completeness, and freshness across all data sources.",
        "data_sources": ["data_assets", "quality_reports"],
        "visuals": [
            {"id": "v1", "title": "Quality Scores by Source", "chart_type": "bar", "data_source": "data_assets", "measures": ["AVG(quality_score)"], "dimensions": ["source_type"]},
            {"id": "v2", "title": "Quality Trend (30 days)", "chart_type": "line", "data_source": "quality_reports", "measures": ["AVG(overall_score)"], "dimensions": ["generated_at"]},
            {"id": "v3", "title": "Assets Below Threshold", "chart_type": "table", "data_source": "data_assets", "measures": ["quality_score"], "dimensions": ["name", "source_type"], "filters": {"quality_score_lt": 70}},
            {"id": "v4", "title": "Quality KPI Cards", "chart_type": "card", "data_source": "data_assets", "measures": ["AVG(quality_score)", "COUNT(*)"], "dimensions": []},
        ],
        "layout": {"columns": 2, "rows": 2},
    },
}


def _match_dashboard_template(prompt: str) -> dict[str, Any]:
    """Simple keyword matching to select a dashboard template."""
    prompt_lower = prompt.lower()

    if any(w in prompt_lower for w in ["inventory", "stock", "reorder", "shrinkage", "warehouse"]):
        return DASHBOARD_TEMPLATES["inventory"]
    if any(w in prompt_lower for w in ["customer", "loyalty", "retention", "segment", "demographics"]):
        return DASHBOARD_TEMPLATES["customer"]
    if any(w in prompt_lower for w in ["quality", "completeness", "freshness", "profiling"]):
        return DASHBOARD_TEMPLATES["quality"]
    # Default: sales
    return DASHBOARD_TEMPLATES["sales"]


def _customize_dashboard(template: dict[str, Any], prompt: str, role: str) -> dict[str, Any]:
    """Customize the template based on the user's prompt and role."""
    spec = json.loads(json.dumps(template))  # deep copy

    # Inject prompt-specific customizations
    prompt_lower = prompt.lower()

    if "q4" in prompt_lower or "quarter 4" in prompt_lower:
        spec["title"] += " — Q4 2024"
        spec["description"] += " Filtered to Q4 2024 (Oct–Dec)."
        for v in spec["visuals"]:
            v.setdefault("filters", {})["date_range"] = "2024-10-01 to 2024-12-31"

    if "region" in prompt_lower:
        spec["description"] += " Broken down by region."

    if "top 10" in prompt_lower or "top ten" in prompt_lower:
        spec["description"] += " Showing top 10 performers."

    if "compare" in prompt_lower:
        spec["description"] += " Includes period-over-period comparison."

    # Role-specific adjustments
    if role == "Business Analyst":
        spec["description"] += " Optimized for business user consumption."
    elif role == "Data Engineer":
        spec["description"] += " Includes technical lineage and data source metadata."
    elif role == "Data Steward":
        spec["description"] += " Includes governance annotations and PII indicators."

    return spec


# ═══════════════════════════════════════════════════════════════════════
# API ROUTES — match frontend expectations
# ═══════════════════════════════════════════════════════════════════════

# ── Health ──
@app.get("/health")
async def health():
    return {"status": "healthy", "service": "udc-demo-backend", "version": "demo-1.0", "mode": "mock"}


# ── Data Catalog ──
@app.get("/api/meta/assets")
async def list_assets(query: str | None = None, source_type: str | None = None, page: int = 1, page_size: int = 20):
    filtered = DEMO_ASSETS
    if query:
        q = query.lower()
        filtered = [a for a in filtered if q in a["name"].lower() or q in a.get("description", "").lower() or any(q in t for t in a.get("tags", []))]
    if source_type:
        filtered = [a for a in filtered if a["source_type"].lower() == source_type.lower()]

    total = len(filtered)
    start = (page - 1) * page_size
    items = filtered[start : start + page_size]
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@app.get("/api/meta/assets/{asset_id}")
async def get_asset(asset_id: str):
    for a in DEMO_ASSETS:
        if a["id"] == asset_id:
            return a
    return JSONResponse({"error": "Asset not found"}, status_code=404)


@app.get("/api/meta/assets/search")
async def search_assets(q: str = ""):
    if not q:
        return []
    q_lower = q.lower()
    return [a for a in DEMO_ASSETS if q_lower in a["name"].lower() or q_lower in a.get("description", "").lower()][:20]


# ── Lineage ──
@app.get("/api/meta/lineage/{asset_id}")
async def get_lineage(asset_id: str):
    """Return a realistic lineage graph."""
    nodes = [
        {"id": "wms_orders", "label": "WMS: orders", "type": "source"},
        {"id": "wms_order_items", "label": "WMS: order_items", "type": "source"},
        {"id": "wms_products", "label": "WMS: products", "type": "source"},
        {"id": "wms_customers", "label": "WMS: customers", "type": "source"},
        {"id": "etl_join", "label": "ETL: Join & Aggregate", "type": "transformation"},
        {"id": "etl_clean", "label": "ETL: PII Masking", "type": "transformation"},
        {"id": "fabric_sales", "label": "Fabric: sales_fact", "type": "target"},
        {"id": "fabric_customer", "label": "Fabric: customer_dim", "type": "target"},
    ]
    edges = [
        {"source": "wms_orders", "target": "etl_join", "label": "SQL JOIN"},
        {"source": "wms_order_items", "target": "etl_join", "label": "SQL JOIN"},
        {"source": "wms_products", "target": "etl_join", "label": "LOOKUP"},
        {"source": "wms_customers", "target": "etl_clean", "label": "PII mask"},
        {"source": "etl_join", "target": "fabric_sales", "label": "INSERT INTO"},
        {"source": "etl_clean", "target": "fabric_customer", "label": "INSERT INTO"},
    ]
    return {"nodes": nodes, "edges": edges}


# ── Quality ──
@app.get("/api/meta/quality/{asset_id}")
async def get_quality_report(asset_id: str):
    asset = next((a for a in DEMO_ASSETS if a["id"] == asset_id), None)
    score = asset["quality_score"] if asset else 85.0
    return {
        "score": score,
        "checks": [
            {"name": "Completeness", "passed": score > 70, "details": f"{score:.0f}% of columns have >95% non-null values"},
            {"name": "Freshness", "passed": True, "details": "Data updated within last 24 hours"},
            {"name": "Uniqueness", "passed": True, "details": "Primary keys are 100% unique"},
            {"name": "Consistency", "passed": score > 80, "details": "Cross-source validation passed"},
            {"name": "PII Classification", "passed": True, "details": "All PII columns identified and tagged"},
        ],
        "overall_status": "pass" if score > 70 else "fail",
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
    }


# ── Glossary ──
@app.get("/api/meta/glossary")
async def list_glossary():
    return DEMO_GLOSSARY


# ── Pipelines ──
@app.get("/api/meta/pipelines")
async def list_pipelines():
    return DEMO_PIPELINES


# ── Policy / Governance ──
@app.get("/api/policy/policies")
async def list_policies():
    return DEMO_POLICIES


@app.get("/api/policy/audit")
async def get_audit_trail(page: int = 1, page_size: int = 20, actor: str | None = None, action: str | None = None, decision: str | None = None):
    filtered = DEMO_AUDIT
    if actor:
        filtered = [e for e in filtered if actor.lower() in e["actor"].lower()]
    if action:
        filtered = [e for e in filtered if action.lower() in e["action"].lower()]
    if decision:
        filtered = [e for e in filtered if e["decision"] == decision]

    total = len(filtered)
    start = (page - 1) * page_size
    items = filtered[start : start + page_size]
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@app.get("/api/policy/trust-scores")
async def get_trust_scores():
    return [
        {"entity_id": "1", "entity_name": "alice@contoso.com", "entity_type": "user", "score": 920,
         "factors": [{"name": "Success Rate", "value": 285, "weight": 300}, {"name": "Policy Compliance", "value": 290, "weight": 300}, {"name": "Data Quality", "value": 180, "weight": 200}, {"name": "Recency", "value": 165, "weight": 200}]},
        {"entity_id": "2", "entity_name": "bob@contoso.com", "entity_type": "user", "score": 780,
         "factors": [{"name": "Success Rate", "value": 250, "weight": 300}, {"name": "Policy Compliance", "value": 220, "weight": 300}, {"name": "Data Quality", "value": 170, "weight": 200}, {"name": "Recency", "value": 140, "weight": 200}]},
        {"entity_id": "3", "entity_name": "carol@contoso.com", "entity_type": "user", "score": 650,
         "factors": [{"name": "Success Rate", "value": 200, "weight": 300}, {"name": "Policy Compliance", "value": 190, "weight": 300}, {"name": "Data Quality", "value": 150, "weight": 200}, {"name": "Recency", "value": 110, "weight": 200}]},
        {"entity_id": "4", "entity_name": "WMS ETL Pipeline", "entity_type": "service", "score": 950,
         "factors": [{"name": "Success Rate", "value": 295, "weight": 300}, {"name": "Policy Compliance", "value": 300, "weight": 300}, {"name": "Data Quality", "value": 190, "weight": 200}, {"name": "Recency", "value": 165, "weight": 200}]},
    ]


@app.get("/api/policy/stats")
async def get_governance_stats():
    total = len(DEMO_AUDIT)
    allowed = sum(1 for e in DEMO_AUDIT if e["decision"] == "allow")
    return {
        "total_evaluations": total,
        "approval_rate": round(allowed / total * 100, 1) if total else 0,
        "avg_trust_score": 825,
    }


# ═══════════════════════════════════════════════════════════════════════
# DASHBOARD BUILDER — The star of the demo 🌟
# ═══════════════════════════════════════════════════════════════════════

@app.post("/api/workflow")
async def execute_workflow(request: Request):
    body = await request.json()
    workflow_name = body.get("workflow_name", "")
    params = body.get("parameters", {})

    if workflow_name == "dashboard_builder":
        prompt = params.get("prompt", "Show me sales data")
        role = params.get("role", "Business Analyst")

        # Simulate AI processing time
        await asyncio.sleep(0.8)

        template = _match_dashboard_template(prompt)
        spec = _customize_dashboard(template, prompt, role)

        # Log audit event
        DEMO_AUDIT.insert(0, {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actor": f"demo-user ({role})",
            "action": "dashboard.generate",
            "resource": spec["title"],
            "decision": "allow",
            "details": f"NL prompt: {prompt[:100]}",
        })

        return spec

    # Generic workflow
    return {
        "id": str(uuid.uuid4()),
        "status": "completed",
        "result": {"message": f"Workflow '{workflow_name}' completed"},
        "started_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/api/workflow/{workflow_id}/status")
async def get_workflow_status(workflow_id: str):
    return {
        "id": workflow_id,
        "status": "completed",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": datetime.now(timezone.utc).isoformat(),
    }


# ── Chat (SSE streaming mock) ──
@app.post("/api/chat")
async def chat_endpoint(request: Request):
    body = await request.json()
    message = body.get("message", "")
    session_id = body.get("session_id", str(uuid.uuid4()))

    # Generate a contextual response
    response_text = _generate_chat_response(message)

    return {
        "message": response_text,
        "session_id": session_id,
        "sources": ["sales_fact", "store_dim", "orders"],
    }


def _generate_chat_response(message: str) -> str:
    msg = message.lower()
    if any(w in msg for w in ["dashboard", "chart", "visual"]):
        return (
            "I can help you build a dashboard! Try using the **Dashboard Builder** page — "
            "describe what you want in natural language, like:\n\n"
            "- *\"Show me sales by region for Q4 2024\"*\n"
            "- *\"Build an inventory health dashboard with low-stock alerts\"*\n"
            "- *\"Customer loyalty analysis with tier breakdown\"*\n\n"
            "I'll analyze your data sources, check quality scores, and generate an interactive dashboard spec."
        )
    if any(w in msg for w in ["quality", "score", "completeness"]):
        return (
            "Your data quality overview:\n\n"
            "| Source | Avg Score |\n|---|---|\n"
            "| PostgreSQL WMS | 87.3% |\n| SAP S/4HANA | 93.1% |\n| Fabric Lakehouse | 95.2% |\n\n"
            "The **WMS customers** table has the lowest quality (67.2%) due to incomplete PII fields. "
            "I recommend running the quality profiler before using it in dashboards."
        )
    if any(w in msg for w in ["pii", "privacy", "sensitive"]):
        return (
            "I've detected PII in the following tables:\n\n"
            "- **customers**: full_name, email, phone, ic_number (classified as PII)\n"
            "- **A_BusinessPartner** (SAP): potentially contains contact details\n\n"
            "PolicyGuard enforces PII access controls — only Data Stewards can view raw PII values. "
            "Dashboard generation will automatically mask PII columns."
        )
    return (
        "I'm the UDC Copilot — your AI assistant for the Universal Data Classifier platform. "
        "I can help you with:\n\n"
        "- **Building dashboards** — describe what you want in plain English\n"
        "- **Exploring data** — search the catalog for tables and columns\n"
        "- **Understanding lineage** — trace data from source to destination\n"
        "- **Checking quality** — review data quality scores and issues\n"
        "- **Governance** — understand policies and access controls\n\n"
        "What would you like to do?"
    )


# ═══════════════════════════════════════════════════════════════════════
# DEMO UI — standalone HTML page (no React build needed)
# ═══════════════════════════════════════════════════════════════════════

@app.get("/demo")
async def serve_demo():
    html_path = Path(__file__).parent / "index.html"
    return FileResponse(html_path, media_type="text/html")


# ═══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    print("\n" + "=" * 60)
    print("  UDC Enterprise Platform — Demo Backend")
    print("  Self-Service Dashboard Builder for Business Users")
    print("=" * 60)
    print(f"\n  API:     http://localhost:8006")
    print(f"  Health:  http://localhost:8006/health")
    print(f"  Docs:    http://localhost:8006/docs")
    print(f"  Demo UI: http://localhost:8006/demo")
    print(f"\n  Or start the React portal:  cd src/udc_portal && npm run dev")
    print(f"  Then open:                  http://localhost:5173/dashboard")
    print("=" * 60 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=8006, log_level="info")
