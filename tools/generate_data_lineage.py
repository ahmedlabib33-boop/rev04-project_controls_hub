"""
Data Lineage Generator
"""
import json
from pathlib import Path
from datetime import datetime

LINEAGE = {
    "generated_at": datetime.now().isoformat(),
    "version": "1.0.0",
    "sources": [
        {
            "file": "activities.csv",
            "required_columns": ["activity_id", "activity_name", "wbs_code"],
            "consumed_by": ["importers.py", "analytics.py", "steel_delay_tia.py"],
            "output_tables": ["activities"],
            "validation_rules": ["activity_id must be unique", "wbs_code must exist in wbs table"]
        },
        {
            "file": "wbs.csv",
            "required_columns": ["wbs_code", "wbs_name"],
            "consumed_by": ["importers.py", "analytics.py"],
            "output_tables": ["wbs"],
            "validation_rules": ["wbs_code must be unique"]
        },
        {
            "file": "contracts.csv",
            "required_columns": ["contract_id", "contract_name", "contract_value"],
            "consumed_by": ["importers.py", "analytics.py", "contract_matcher.py"],
            "output_tables": ["contracts"],
            "validation_rules": ["contract_value must be numeric"]
        },
        {
            "file": "payments.csv",
            "required_columns": ["payment_id", "amount_certified"],
            "consumed_by": ["importers.py", "analytics.py"],
            "output_tables": ["payments"],
            "validation_rules": ["amount_certified must be positive"]
        },
        {
            "file": "risks.csv",
            "required_columns": ["risk_id", "risk_description"],
            "consumed_by": ["importers.py", "analytics.py"],
            "output_tables": ["risks"],
            "validation_rules": ["probability and impact must be 1-5 scale"]
        },
        {
            "file": "steel_supply.csv",
            "required_columns": ["material_type", "quantity", "delivery_date"],
            "consumed_by": ["importers.py", "steel_delay_tia.py"],
            "output_tables": ["steel_supply"],
            "validation_rules": ["quantity must be positive", "delivery_date must be valid"]
        },
        {
            "file": "delay_events.csv",
            "required_columns": ["event_id", "event_description", "duration_days"],
            "consumed_by": ["importers.py", "steel_delay_tia.py", "contract_matcher.py"],
            "output_tables": ["delay_events"],
            "validation_rules": ["duration_days must be positive"]
        },
        {
            "file": "letters/",
            "required_columns": [],
            "consumed_by": ["letters_auto_ingest.py"],
            "output_tables": ["letters"],
            "validation_rules": ["supported formats: PDF, DOCX, TXT, XLSX"]
        }
    ],
    "modules": [
        {
            "name": "project_catalog.py",
            "purpose": "Auto-discover and manage projects",
            "inputs": [],
            "outputs": ["project_manifest.json"]
        },
        {
            "name": "project_context.py",
            "purpose": "Resolve project-specific paths",
            "inputs": ["project_id"],
            "outputs": ["path_resolution"]
        },
        {
            "name": "importers.py",
            "purpose": "Import and validate CSV/XLSX data",
            "inputs": ["*.csv", "*.xlsx"],
            "outputs": ["validated_dataframes"]
        },
        {
            "name": "analytics.py",
            "purpose": "Calculate project control KPIs",
            "inputs": ["activities", "payments", "contracts", "risks"],
            "outputs": ["progress_metrics", "cost_metrics", "risk_metrics"]
        },
        {
            "name": "steel_delay_tia.py",
            "purpose": "Steel delay time impact analysis",
            "inputs": ["steel_supply", "steel_demand", "activities"],
            "outputs": ["delay_windows", "affected_activities", "tia_summary"]
        },
        {
            "name": "contract_matcher.py",
            "purpose": "Claims evaluation and contract matching",
            "inputs": ["contract_clauses", "evidence", "delay_events"],
            "outputs": ["claim_evaluations", "recommendations"]
        },
        {
            "name": "letters_auto_ingest.py",
            "purpose": "Correspondence ingestion and classification",
            "inputs": ["letters_inbox/*"],
            "outputs": ["letters_register", "classifications"]
        }
    ],
    "project_isolation_rules": [
        "Every table includes project_id column",
        "All queries filter by project_id",
        "No fallback to other projects when data missing",
        "Cache keys include project_id",
        "Output files saved to selected project folder only",
        "Folder rename preserves project_id in manifest"
    ]
}

def generate_lineage():
    output_path = Path("data_lineage.json")
    with open(output_path, "w") as f:
        json.dump(LINEAGE, f, indent=2)

    # Generate markdown version
    md_path = Path("data_to_program.md")
    with open(md_path, "w") as f:
        f.write("# Data to Program Lineage\n\n")
        f.write(f"Generated: {LINEAGE['generated_at']}\n\n")

        f.write("## Source Files\n\n")
        for src in LINEAGE["sources"]:
            f.write(f"### {src['file']}\n")
            f.write(f"- **Required Columns:** {', '.join(src['required_columns'])}\n")
            f.write(f"- **Consumed By:** {', '.join(src['consumed_by'])}\n")
            f.write(f"- **Output Tables:** {', '.join(src['output_tables'])}\n")
            f.write(f"- **Validation:** {', '.join(src['validation_rules'])}\n\n")

        f.write("## Modules\n\n")
        for mod in LINEAGE["modules"]:
            f.write(f"### {mod['name']}\n")
            f.write(f"- **Purpose:** {mod['purpose']}\n")
            f.write(f"- **Inputs:** {', '.join(mod['inputs'])}\n")
            f.write(f"- **Outputs:** {', '.join(mod['outputs'])}\n\n")

        f.write("## Project Isolation Rules\n\n")
        for rule in LINEAGE["project_isolation_rules"]:
            f.write(f"- ✅ {rule}\n")

    print(f"✅ Generated {output_path}")
    print(f"✅ Generated {md_path}")

if __name__ == "__main__":
    generate_lineage()
