"""
Initialize Database for a Project
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from construction_system.project_catalog import ProjectCatalog
from construction_system.project_context import ProjectContext
from construction_system.database import ProjectDatabase

def init_db(project_id=None):
    catalog = ProjectCatalog()

    if project_id:
        projects = [catalog.get_project(project_id)]
    else:
        projects = catalog.get_catalog()

    for proj in projects:
        if not proj:
            continue
        ctx = ProjectContext(proj["project_id"])
        db = ProjectDatabase(ctx.contracts_db_path)
        print(f"✅ Initialized database for {proj['project_display_name']}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-id", help="Specific project ID")
    args = parser.parse_args()
    init_db(args.project_id)
