# UDC Enterprise Platform — Data Source Connectors

## Overview

The platform connects to three enterprise data sources commonly found in Southeast Asian retail operations:

| Source | Protocol | Connector | Service |
|--------|----------|-----------|---------|
| PostgreSQL WMS | TCP/SQL | `PostgresConnector` (.NET) / `PostgresIngester` (Python) | Classifier / MetaCatalog |
| SAP S/4HANA | HTTPS/OData | `SapS4HanaConnector` (.NET) / `SapIngester` (Python) | Classifier / MetaCatalog |
| Microsoft Fabric | HTTPS/REST | `FabricLakehouseConnector` (.NET) / `FabricIngester` (Python) | Classifier / MetaCatalog |

## PostgreSQL WMS (57–100 Stores)

### Architecture

Each store runs an independent PostgreSQL database with a standard WMS schema:

```
store_001_wms/
├── public.orders          ← POS transactions
├── public.order_items     ← Line items
├── public.products        ← Product catalog
├── public.customers       ← Customer records (PII)
├── public.inventory       ← Stock levels
├── public.suppliers       ← Supplier directory
└── public.warehouses      ← Warehouse locations
```

### Connection Pattern

The connector uses a **multi-store scanning** approach:

1. Accept a list of connection strings (one per store)
2. Iterate through stores concurrently (asyncio.gather / Task.WhenAll)
3. For each store: `information_schema.tables` → `information_schema.columns` → sample data
4. Aggregate results into unified DataAsset objects

### Schema Discovery

```sql
SELECT table_name, column_name, data_type, is_nullable,
       column_default, character_maximum_length
FROM information_schema.columns
WHERE table_schema = 'public'
ORDER BY table_name, ordinal_position;
```

### PII Detection

The classifier scans for columns matching PII patterns:
- **Names**: `customer_name`, `first_name`, `last_name`
- **Contact**: `email`, `phone`, `address`
- **Financial**: `credit_card`, `bank_account`
- **Identity**: `ic_number`, `passport`, `nric` (SEA-specific)

## SAP S/4HANA (OData v2/v4)

### Entity Sets

Key OData entity sets for retail:

| Entity Set | Description | Key Fields |
|------------|-------------|------------|
| `A_Product` | Material master | `Product`, `ProductType`, `BaseUnit` |
| `A_SalesOrder` | Sales orders | `SalesOrder`, `SoldToParty`, `TotalNetAmount` |
| `A_PurchaseOrder` | Purchase orders | `PurchaseOrder`, `Supplier`, `PurchasingOrganization` |
| `A_BusinessPartner` | Customers/Vendors | `BusinessPartner`, `BusinessPartnerName` |
| `A_ProfitCenter` | Cost centers | `ProfitCenter`, `ProfitCenterName` |

### Authentication

SAP uses **Basic Auth** or **OAuth2 Client Credentials**:

```
SAP_ODATA_BASE_URL=https://sap-host:443/sap/opu/odata/sap/
SAP_ODATA_USERNAME=UDC_TECH_USER
SAP_ODATA_PASSWORD=<secret>
```

### Query Pattern

```http
GET /sap/opu/odata/sap/API_PRODUCT_SRV/A_Product
    ?$select=Product,ProductType,BaseUnit
    &$filter=LastChangeDate gt datetime'2024-01-01T00:00:00'
    &$top=1000
    &$skip=0
Accept: application/json
```

Pagination: SAP uses `$skip`/`$top` with `__next` links in `__metadata`.

## Microsoft Fabric Lakehouse (OneLake)

### Architecture

Fabric organizes data into:
```
Workspace (FABRIC_WORKSPACE_ID)
└── Lakehouse (FABRIC_LAKEHOUSE_ID)
    ├── Tables/           ← Delta tables (structured)
    │   ├── sales_fact
    │   ├── product_dim
    │   └── store_dim
    └── Files/            ← Unstructured files
        ├── reports/
        └── raw_data/
```

### Authentication

Uses **Azure AD Service Principal** with `Storage Blob Data Reader` role:

```
FABRIC_TENANT_ID=<azure-ad-tenant>
FABRIC_CLIENT_ID=<sp-client-id>
FABRIC_CLIENT_SECRET=<sp-secret>
FABRIC_WORKSPACE_ID=<workspace-guid>
FABRIC_LAKEHOUSE_ID=<lakehouse-guid>
```

### OneLake REST API

```http
# List tables
GET https://onelake.dfs.fabric.microsoft.com/{workspace_id}/{lakehouse_id}/Tables
Authorization: Bearer <token>

# Read Delta table
GET https://onelake.dfs.fabric.microsoft.com/{workspace_id}/{lakehouse_id}/Tables/{table_name}/_delta_log/
Authorization: Bearer <token>
```

### Data Profiling

For Fabric tables, the connector:
1. Lists tables via OneLake API
2. Reads Delta log to extract schema (column names, types)
3. Samples first N rows for profiling
4. Maps Spark types → common type system
