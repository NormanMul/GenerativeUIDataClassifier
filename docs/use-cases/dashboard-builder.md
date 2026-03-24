# Use Case 4 — Natural Language Dashboard Builder

## Overview

A Business Analyst describes a desired dashboard in natural language. The system interprets the request, resolves data sources, validates access policies, checks data quality, generates a dashboard specification, and renders it as a Power BI dashboard (or HTML fallback with Chart.js).

## Trigger

```
User: "Build a sales by region dashboard for Q4 2024 showing top 10 stores"
```

## Workflow Steps

### Step 1: Parse NL Request
**Service**: Orchestrator → Classifier (DashboardBuilderAgent)  
**Action**: Azure OpenAI extracts intent, measures, dimensions, filters, time range  
**Output**:
```json
{
  "intent": "dashboard",
  "measures": ["sales_amount"],
  "dimensions": ["region", "store"],
  "filters": { "quarter": "Q4", "year": 2024 },
  "aggregation": "top_10",
  "sort": "sales_amount DESC"
}
```

### Step 2: Resolve Data Sources
**Service**: MetaCatalog  
**Action**: Search catalog for assets matching measures/dimensions. Resolve KPI formulas.  
**Output**: Matched DataAssets + KPIFormula objects

### Step 3: Retrieve Context
**Service**: ContextVault  
**Action**: Semantic search for related dashboards, reports, or documentation  
**Output**: Historical context that helps refine the spec

### Step 4: Validate Access Policy
**Service**: PolicyGuard  
**Action**: Check if user's role permits access to the resolved data sources  
**Rules**: data_access.yaml policies evaluated against user role + data classification  
**Output**: Approved / Denied with reason

### Step 5: Check Data Quality
**Service**: MetaCatalog  
**Action**: Retrieve latest quality reports for resolved assets  
**Decision**: If quality score < threshold → warn user, suggest data cleansing  
**Output**: Quality scores per asset

### Step 6: Generate Dashboard Spec
**Service**: Classifier (DashboardRenderSkill)  
**Action**: Azure OpenAI generates DashboardSpec with visuals, layout, formatting  
**Output**: DashboardSpec JSON with measures, axes, chart types, filters

### Step 7: Render Dashboard
**Service**: Classifier (DashboardRenderSkill)  
**Primary**: Power BI REST API → create dataset, create report, embed  
**Fallback**: Generate HTML with Chart.js visualizations  
**Output**: Power BI embed URL or HTML file

### Step 8: Store Result
**Service**: ContextVault + MetaCatalog  
**Action**: Cache dashboard spec and rendered output for future reference  
**Output**: Persistent record + vault:// URI

### Step 9: Policy Audit
**Service**: PolicyGuard  
**Action**: Log dashboard creation as audit entry with data access details  
**Output**: Append-only audit record

## Output Artifacts

1. **Power BI Dashboard** (primary): Embedded interactive dashboard
2. **HTML Dashboard** (fallback): Static HTML with Chart.js charts
3. **Dashboard Spec**: Reusable JSON specification for re-rendering

## Rendering Decision Tree

```
Is Power BI configured?
├── Yes → Can connect to Power BI API?
│   ├── Yes → Create Power BI dataset + report → Return embed URL
│   └── No → Fall back to HTML
└── No → Generate HTML with Chart.js
```

## Error Handling

| Error | Recovery |
|-------|----------|
| No matching data sources | Ask user to clarify measures/dimensions |
| Policy denial | Return denial reason, suggest alternative data sources |
| Poor data quality (< 0.5) | Warn user, offer to proceed with caveats |
| Power BI API failure | Automatic fallback to HTML rendering |
| Ambiguous NL request | Ask clarifying questions before proceeding |
