"""
Import CSV Data into Project Database
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from construction_system.project_catalog import ProjectCatalog
from construction_system.project_context import ProjectContext
from construction_system.database import ProjectDatabase
from construction_system.importers import DataImporter

def import_data(project_id):
    catalog = ProjectCatalog()
    proj = catalog.get_project(project_id)

    if not proj:
        print(f"Project {project_id} not found")
        return

    ctx = ProjectContext(project_id)
    importer = DataImporter(ctx)
    db = ProjectDatabase(ctx.contracts_db_path)

    data = importer.load_all_project_data()

    # Import to database
    table_mapping = {
        "activities": "activities",
        "wbs": "wbs",
        "contracts": "contracts",
        "payments": "payments",
        "risks": "risks",
        "rfi_status": "rfi_status",
        "steel_status": "steel_supply",
        "delay_events": "delay_events",
    }

    for data_key, table_name in table_mapping.items():
        df = data.get(data_key, pd.DataFrame())
        if not df.empty:
            db.clear_project_data(table_name, project_id)
            db.insert_dataframe(table_name, df, project_id)
            print(f"  ✅ Imported {len(df)} records to {table_name}")

    # Log warnings
    for warning in importer.get_warnings():
        db.log_validation(project_id, warning["file_type"], warning["message"], warning["severity"])

    print(f"Import complete for {proj['project_display_name']}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-id", required=True, help="Project ID")
    args = parser.parse_args()

    import pandas as pd
    import_data(args.project_id)
