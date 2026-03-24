#!/usr/bin/env python3
"""Export OpenAPI JSON specs from all FastAPI services.

Usage:
    python scripts/generate_openapi.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Add src to path so we can import service apps
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

SERVICES = [
    ("udc_metacatalog", "udc_metacatalog.api.app", "app"),
    ("udc_contextvault", "udc_contextvault.api.app", "app"),
    ("udc_visionlens", "udc_visionlens.api.app", "app"),
    ("udc_desktopagent", "udc_desktopagent.api.app", "app"),
    ("udc_policyguard", "udc_policyguard.api.app", "app"),
    ("udc_orchestrator", "udc_orchestrator.api.app", "app"),
]

OUTPUT_DIR = ROOT / "docs" / "openapi"


def export_specs() -> None:
    """Export OpenAPI specs for all services."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    success = 0
    failed = 0

    for service_name, module_path, app_attr in SERVICES:
        try:
            module = __import__(module_path, fromlist=[app_attr])
            app = getattr(module, app_attr)
            spec = app.openapi()

            output_file = OUTPUT_DIR / f"{service_name}.json"
            output_file.write_text(json.dumps(spec, indent=2))

            print(f"  [OK] {service_name} → {output_file.relative_to(ROOT)}")
            success += 1
        except Exception as e:
            print(f"  [FAIL] {service_name}: {e}")
            failed += 1

    print(f"\nExported {success}/{len(SERVICES)} specs to {OUTPUT_DIR.relative_to(ROOT)}/")
    if failed:
        print(f"  {failed} service(s) failed — ensure dependencies are installed")


if __name__ == "__main__":
    print("=== UDC Enterprise Platform — OpenAPI Exporter ===\n")
    export_specs()
