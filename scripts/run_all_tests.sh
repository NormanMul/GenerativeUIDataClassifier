#!/usr/bin/env bash
set -euo pipefail

# UDC Enterprise Platform — Run All Tests
# Usage: bash scripts/run_all_tests.sh

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PASS=0
FAIL=0

echo "============================================"
echo "  UDC Enterprise Platform — Test Runner"
echo "============================================"
echo ""

# ---- Python Tests ----
echo "--- Python Tests (pytest) ---"
PYTHON_SERVICES=(
    "udc_metacatalog"
    "udc_contextvault"
    "udc_visionlens"
    "udc_desktopagent"
    "udc_policyguard"
    "udc_orchestrator"
)

for svc in "${PYTHON_SERVICES[@]}"; do
    echo -n "  $svc: "
    if cd "src/$svc" && python -m pytest tests/ -q --tb=short 2>/dev/null; then
        echo "PASS"
        ((PASS++))
    else
        echo "FAIL"
        ((FAIL++))
    fi
    cd "$ROOT_DIR"
done
echo ""

# ---- .NET Tests ----
echo "--- .NET Tests (dotnet test) ---"
echo -n "  UDC.Classifier: "
if cd "src/UDC.Classifier" && dotnet test --nologo --verbosity quiet 2>/dev/null; then
    echo "PASS"
    ((PASS++))
else
    echo "FAIL"
    ((FAIL++))
fi
cd "$ROOT_DIR"
echo ""

# ---- TypeScript Tests ----
echo "--- TypeScript Tests (vitest) ---"
echo -n "  udc_portal: "
if cd "src/udc_portal" && npm run test -- --run 2>/dev/null; then
    echo "PASS"
    ((PASS++))
else
    echo "FAIL"
    ((FAIL++))
fi
cd "$ROOT_DIR"
echo ""

# ---- Summary ----
TOTAL=$((PASS + FAIL))
echo "============================================"
echo "  Results: $PASS/$TOTAL passed, $FAIL failed"
echo "============================================"

if [ "$FAIL" -gt 0 ]; then
    exit 1
fi
