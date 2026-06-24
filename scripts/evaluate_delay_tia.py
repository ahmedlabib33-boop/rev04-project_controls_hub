"""
Evaluate Delay TIA Module
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from construction_system.project_catalog import ProjectCatalog
from construction_system.project_context import ProjectContext
from construction_system.steel_delay_tia import SteelDelayTIA

def evaluate(label=""):
    print(f"Evaluating Delay TIA Module... (label: {label})")

    catalog = ProjectCatalog()
    projects = catalog.get_catalog()

    if not projects:
        print("No projects found")
        return False

    for proj in projects:
        ctx = ProjectContext(proj["project_id"])
        tia = SteelDelayTIA(ctx)
        print(f"  ✅ Project {proj['project_display_name']}: TIA engine initialized")

    print("Delay TIA evaluation complete")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", default="", help="Evaluation label")
    args = parser.parse_args()

    success = evaluate(args.label)
    sys.exit(0 if success else 1)
