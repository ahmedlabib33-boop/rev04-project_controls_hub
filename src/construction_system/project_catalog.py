"""
Project Catalog Engine - Auto-discovers and manages all projects.
"""
import os
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

class ProjectCatalog:
    """Scans projects/ folder, manages manifests, provides stable project IDs."""

    def __init__(self, root_path: str = "."):
        self.root_path = Path(root_path).resolve()
        self.projects_root = self.root_path / "projects"
        self._catalog: Dict[str, dict] = {}
        self._refresh()

    def _refresh(self):
        """Scan all project manifests recursively and auto-detect sector from folder structure."""
        self._catalog = {}

        if not self.projects_root.exists():
            return

        manifest_paths = sorted(self.projects_root.rglob("project_manifest.json"))

        for manifest_path in manifest_paths:
            folder = manifest_path.parent

            try:
                rel_parts = folder.relative_to(self.projects_root).parts
            except ValueError:
                continue

            # Skip templates and hidden/system folders
            if not rel_parts:
                continue

            if any(part.startswith(".") for part in rel_parts):
                continue

            if folder.name.startswith("_"):
                continue

            manifest = self._ensure_manifest(folder, manifest_path)

            # Folder sector rule:
            # projects/<Sector>/<Project>/project_manifest.json
            if len(rel_parts) >= 2:
                folder_sector = rel_parts[0]
                manifest["sector"] = folder_sector
                manifest["sector_source"] = "folder"
            else:
                # Backward compatibility for old one-level project folders
                manifest["sector"] = manifest.get("sector", "Unassigned")
                manifest["sector_source"] = manifest.get("sector_source", "manifest")

            manifest["project_folder_path"] = str(folder)
            manifest["project_folder_name"] = folder.name

            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2)

            project_id = manifest.get("project_id")
            if project_id:
                self._catalog[project_id] = manifest

    def _ensure_manifest(self, folder: Path, manifest_path: Path) -> dict:
        """Create manifest if missing, preserving existing project_id."""
        if manifest_path.exists():
            with open(manifest_path, "r") as f:
                manifest = json.load(f)
            # Ensure project_id exists
            if not manifest.get("project_id"):
                manifest["project_id"] = str(uuid.uuid4())
                manifest["created_at"] = datetime.now().isoformat()
            return manifest

        # Create new manifest
        manifest = {
            "project_id": str(uuid.uuid4()),
            "project_display_name": folder.name.replace("_", " ").title(),
            "status": "active",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "version": "1.0.0",
            "sector": "construction",
            "currency": "USD",
            "contract_type": "lump_sum",
            "parties": {
                "employer": "",
                "contractor": "",
                "consultant": ""
            }
        }

        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)

        # Create standard folders
        self._create_standard_folders(folder)
        return manifest

    def _create_standard_folders(self, folder: Path):
        """Create standard project folder structure."""
        subdirs = [
            "1-branding", "2-contracts/source", "2-contracts/evidence",
            "3-evidence", "4-notes", "data/import_templates",
            "data/delay_analysis/steel_delay_tia_templates", "data/methodology",
            "bl/fixed", "letters_intelligence/inbox/From Contractor",
            "letters_intelligence/inbox/From Consultant",
            "letters_intelligence/inbox/From Client", "source_excel",
            "outputs/reports", "outputs/slides", "outputs/exports", "logs"
        ]
        for subdir in subdirs:
            (folder / subdir).mkdir(parents=True, exist_ok=True)

    def get_catalog(self) -> List[dict]:
        """Return list of all projects."""
        self._refresh()
        return list(self._catalog.values())

    def get_project(self, project_id: str) -> Optional[dict]:
        """Get single project by ID."""
        self._refresh()
        return self._catalog.get(project_id)

    def get_project_by_folder(self, folder_name: str) -> Optional[dict]:
        """Find project by folder name."""
        for proj in self.get_catalog():
            if proj["project_folder_name"] == folder_name:
                return proj
        return None

    def get_all_project_ids(self) -> List[str]:
        """Return all project IDs."""
        return list(self._catalog.keys())

    def create_project(self, display_name: str, folder_name: str = None) -> dict:
        """Create a new project folder with manifest."""
        if folder_name is None:
            folder_name = display_name.lower().replace(" ", "_")

        folder = self.projects_root / folder_name
        if folder.exists():
            raise ValueError(f"Folder {folder_name} already exists")

        folder.mkdir(parents=True)
        manifest = self._ensure_manifest(folder, folder / "project_manifest.json")
        manifest["project_display_name"] = display_name
        with open(folder / "project_manifest.json", "w") as f:
            json.dump(manifest, f, indent=2)

        self._refresh()
        return self._catalog[manifest["project_id"]]
