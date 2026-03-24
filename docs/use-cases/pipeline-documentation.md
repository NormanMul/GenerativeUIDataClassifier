# Use Case 2 — Automated Pipeline Documentation

## Overview

A Data Engineer triggers automated documentation of an existing data pipeline. The system discovers data sources, profiles columns, extracts lineage, classifies data, maps to business glossary, and generates a comprehensive HTML report.

## Trigger

```
User: "Document the inventory pipeline from WMS stores to Fabric lakehouse"
```

## Workflow Steps

### Step 1: Parse Request
**Service**: Orchestrator  
**Action**: NL parsing to extract pipeline name, source/target hints  
**Output**: `{ pipeline: "inventory", sources: ["wms"], targets: ["fabric"] }`

### Step 2: Discover Data Sources
**Service**: MetaCatalog (via PostgresIngester + FabricIngester)  
**Action**: Scan WMS stores for inventory-related tables, scan Fabric lakehouse  
**Output**: List of DataAsset objects with column metadata

### Step 3: Profile Columns
**Service**: Classifier (DataProfilingSkill)  
**Action**: For each table, compute column statistics: null%, unique%, min, max, patterns  
**Output**: ColumnProfile objects for all discovered columns

### Step 4: Extract Lineage
**Service**: MetaCatalog (LineageParser)  
**Action**: Parse SQL transformations to build a directed acyclic graph of data flow  
**Tool**: sqlglot library parses SQL into AST, extracts source→target relationships  
**Output**: LineageGraph with nodes (tables) and edges (transformations)

### Step 5: Classify Columns
**Service**: Classifier (ClassifierAgent)  
**Action**: Use Azure OpenAI to classify each column (PII, financial, operational, etc.)  
**Output**: ClassificationResult per column with confidence scores

### Step 6: Map to Business Glossary
**Service**: MetaCatalog (AutoTagger)  
**Action**: Match columns to existing glossary terms using embedding similarity  
**Output**: Updated DataAssets with glossary_term_ids

### Step 7: Quality Gate
**Service**: PolicyGuard  
**Action**: Evaluate pipeline against quality policies (completeness, freshness, accuracy)  
**Output**: QualityReport with pass/fail, individual check results

### Step 8: Publish Report
**Service**: MetaCatalog  
**Action**: Store quality report, lineage graph, and classifications in PostgreSQL  
**Output**: Persistent records accessible via API

### Step 9: Cache Documentation
**Service**: ContextVault  
**Action**: Store generated documentation as L1 curated content for future retrieval  
**Output**: vault:// URI for the cached document

### Step 10: Policy Audit
**Service**: PolicyGuard  
**Action**: Log the entire pipeline documentation run as an audit entry  
**Output**: Append-only audit record

## Output Artifacts

1. **HTML Report**: Rendered documentation with:
   - Pipeline overview and description
   - Source/target table listing with column details
   - Interactive lineage visualization (D3.js)
   - Quality scorecard
   - Glossary term mappings
   - Classification summary (PII highlights)

2. **Quality Report**: JSON with individual check results

3. **Lineage Graph**: JSON DAG structure displayable in the Portal

## Error Handling

| Error | Recovery |
|-------|----------|
| Store unreachable | Skip store, log warning, continue with available stores |
| Classification timeout | Use rule-based fallback classification |
| Quality gate failure | Generate report with warnings, do not block documentation |
| Glossary match < 0.7 confidence | Flag as "unmatched", suggest manual review |
