#!/usr/bin/env python3
"""Seed demo data into PostgreSQL for local development.

Creates sample WMS tables, glossary terms, KPI formulas, and API keys.
Requires a running PostgreSQL instance (see docker-compose.yml).

Usage:
    python scripts/seed_data.py
"""

from __future__ import annotations

import asyncio
import os
import uuid
from datetime import datetime, timezone

import asyncpg


async def get_connection() -> asyncpg.Connection:
    """Connect to PostgreSQL using environment variables."""
    return await asyncpg.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        database=os.getenv("POSTGRES_DB", "udc"),
        user=os.getenv("POSTGRES_USER", "udc_admin"),
        password=os.getenv("POSTGRES_PASSWORD", "udc_secret"),
    )


async def create_tables(conn: asyncpg.Connection) -> None:
    """Create core schema tables if they don't exist."""
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS api_keys (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            key_hash VARCHAR(128) NOT NULL UNIQUE,
            name VARCHAR(255) NOT NULL,
            scopes TEXT[] DEFAULT '{}',
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            expires_at TIMESTAMPTZ
        );

        CREATE TABLE IF NOT EXISTS data_assets (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name VARCHAR(255) NOT NULL,
            qualified_name VARCHAR(512) NOT NULL UNIQUE,
            source_type VARCHAR(50) NOT NULL,
            source_instance VARCHAR(255),
            database_name VARCHAR(255),
            schema_name VARCHAR(128) DEFAULT 'public',
            description TEXT,
            tags TEXT[] DEFAULT '{}',
            quality_score DOUBLE PRECISION DEFAULT 0.0,
            row_count BIGINT,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS column_meta (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            asset_id UUID REFERENCES data_assets(id) ON DELETE CASCADE,
            name VARCHAR(255) NOT NULL,
            data_type VARCHAR(100),
            is_nullable BOOLEAN DEFAULT TRUE,
            is_primary_key BOOLEAN DEFAULT FALSE,
            is_foreign_key BOOLEAN DEFAULT FALSE,
            null_percentage DOUBLE PRECISION,
            unique_percentage DOUBLE PRECISION,
            is_pii BOOLEAN DEFAULT FALSE,
            pii_type VARCHAR(50),
            classification VARCHAR(100),
            sample_values JSONB
        );

        CREATE TABLE IF NOT EXISTS glossary_terms (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            term VARCHAR(255) NOT NULL UNIQUE,
            definition TEXT NOT NULL,
            domain VARCHAR(100),
            synonyms TEXT[] DEFAULT '{}',
            owner VARCHAR(255),
            status VARCHAR(50) DEFAULT 'draft',
            created_at TIMESTAMPTZ DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS kpi_formulas (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name VARCHAR(255) NOT NULL UNIQUE,
            formula TEXT NOT NULL,
            description TEXT,
            unit VARCHAR(50),
            domain VARCHAR(100),
            created_at TIMESTAMPTZ DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS quality_reports (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            asset_id UUID REFERENCES data_assets(id) ON DELETE CASCADE,
            overall_score DOUBLE PRECISION NOT NULL,
            passed BOOLEAN NOT NULL,
            checks JSONB DEFAULT '[]',
            generated_at TIMESTAMPTZ DEFAULT NOW(),
            generated_by VARCHAR(100) DEFAULT 'system'
        );
    """)
    print("[OK] Core tables created")


async def seed_api_keys(conn: asyncpg.Connection) -> None:
    """Insert demo API keys."""
    import hashlib

    keys = [
        ("demo-key-analyst", "Business Analyst Demo", ["read", "dashboard"]),
        ("demo-key-engineer", "Data Engineer Demo", ["read", "write", "pipeline"]),
        ("demo-key-steward", "Data Steward Demo", ["read", "write", "admin", "policy"]),
    ]
    for raw_key, name, scopes in keys:
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        await conn.execute(
            """INSERT INTO api_keys (key_hash, name, scopes)
               VALUES ($1, $2, $3)
               ON CONFLICT (key_hash) DO NOTHING""",
            key_hash,
            name,
            scopes,
        )
    print("[OK] API keys seeded (demo-key-analyst, demo-key-engineer, demo-key-steward)")


async def seed_wms_assets(conn: asyncpg.Connection) -> None:
    """Insert sample WMS store data assets."""
    stores = [f"store_{i:03d}" for i in range(1, 6)]
    tables = ["orders", "order_items", "products", "customers", "inventory"]

    for store in stores:
        for table in tables:
            asset_id = uuid.uuid4()
            qualified = f"postgresql://{store}_wms/public/{table}"
            await conn.execute(
                """INSERT INTO data_assets (id, name, qualified_name, source_type,
                   source_instance, database_name, schema_name, tags, row_count)
                   VALUES ($1, $2, $3, 'postgresql', $4, $5, 'public', $6, $7)
                   ON CONFLICT (qualified_name) DO NOTHING""",
                asset_id,
                table,
                qualified,
                f"{store}_wms",
                f"{store}_wms",
                ["wms", store, table],
                10000 + hash(store + table) % 50000,
            )

            # Seed columns for customer tables (PII-heavy)
            if table == "customers":
                columns = [
                    ("id", "uuid", False, True, False, 0.0, 100.0, False, None),
                    ("customer_name", "varchar", False, False, False, 0.5, 95.0, True, "name"),
                    ("email", "varchar", True, False, False, 5.0, 98.0, True, "email"),
                    ("phone", "varchar", True, False, False, 10.0, 90.0, True, "phone"),
                    ("address", "text", True, False, False, 15.0, 80.0, True, "address"),
                    ("created_at", "timestamptz", False, False, False, 0.0, 70.0, False, None),
                ]
                for col_name, dtype, nullable, pk, fk, null_pct, uniq_pct, is_pii, pii_type in columns:
                    await conn.execute(
                        """INSERT INTO column_meta (asset_id, name, data_type, is_nullable,
                           is_primary_key, is_foreign_key, null_percentage, unique_percentage,
                           is_pii, pii_type, classification)
                           VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)""",
                        asset_id,
                        col_name,
                        dtype,
                        nullable,
                        pk,
                        fk,
                        null_pct,
                        uniq_pct,
                        is_pii,
                        pii_type,
                        "pii" if is_pii else "operational",
                    )

    print(f"[OK] {len(stores) * len(tables)} WMS assets seeded across {len(stores)} stores")


async def seed_glossary(conn: asyncpg.Connection) -> None:
    """Insert sample business glossary terms."""
    terms = [
        ("GMV", "Gross Merchandise Value — total sales value before deductions", "finance", ["gross sales", "total sales"]),
        ("SKU", "Stock Keeping Unit — unique identifier for each product variant", "inventory", ["product code", "item code"]),
        ("COGS", "Cost of Goods Sold — direct costs of producing goods", "finance", ["cost of sales"]),
        ("Shrinkage", "Inventory loss due to theft, damage, or administrative error", "inventory", ["inventory loss"]),
        ("Fill Rate", "Percentage of customer orders fulfilled from available stock", "operations", ["order fulfillment rate"]),
        ("Basket Size", "Average number of items per transaction", "sales", ["items per transaction"]),
        ("AOV", "Average Order Value — mean transaction value", "sales", ["average transaction value"]),
        ("Dwell Time", "Average time a customer spends in store", "operations", ["visit duration"]),
    ]
    for term, definition, domain, synonyms in terms:
        await conn.execute(
            """INSERT INTO glossary_terms (term, definition, domain, synonyms, status)
               VALUES ($1, $2, $3, $4, 'approved')
               ON CONFLICT (term) DO NOTHING""",
            term,
            definition,
            domain,
            synonyms,
        )
    print(f"[OK] {len(terms)} glossary terms seeded")


async def seed_kpi_formulas(conn: asyncpg.Connection) -> None:
    """Insert sample KPI formulas."""
    formulas = [
        ("Gross Margin %", "(GMV - COGS) / GMV * 100", "Profitability percentage", "%", "finance"),
        ("Inventory Turnover", "COGS / AVG(inventory_value)", "How often inventory is sold and replaced", "x", "inventory"),
        ("Sales per Sqft", "total_sales / store_area_sqft", "Revenue per square foot of store space", "$/sqft", "sales"),
        ("Customer Retention Rate", "(end_customers - new_customers) / start_customers * 100", "Percentage of returning customers", "%", "customer"),
    ]
    for name, formula, desc, unit, domain in formulas:
        await conn.execute(
            """INSERT INTO kpi_formulas (name, formula, description, unit, domain)
               VALUES ($1, $2, $3, $4, $5)
               ON CONFLICT (name) DO NOTHING""",
            name,
            formula,
            desc,
            unit,
            domain,
        )
    print(f"[OK] {len(formulas)} KPI formulas seeded")


async def main() -> None:
    """Run all seed operations."""
    print("=== UDC Enterprise Platform — Data Seeder ===\n")

    conn = await get_connection()
    try:
        await create_tables(conn)
        await seed_api_keys(conn)
        await seed_wms_assets(conn)
        await seed_glossary(conn)
        await seed_kpi_formulas(conn)
        print("\n=== Seeding complete ===")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
