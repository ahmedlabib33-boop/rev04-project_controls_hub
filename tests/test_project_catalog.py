"""
Tests for Project Catalog
"""
import pytest
import tempfile
import shutil
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from construction_system.project_catalog import ProjectCatalog

class TestProjectCatalog:
    def test_catalog_discovery(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test projects
            projects_dir = Path(tmpdir) / "projects"
            projects_dir.mkdir()

            (projects_dir / "Project_Alpha").mkdir()
            (projects_dir / "Project_Beta").mkdir()
            (projects_dir / "_PROJECT_TEMPLATE").mkdir()

            catalog = ProjectCatalog(tmpdir)
            projects = catalog.get_catalog()

            assert len(projects) == 2
            assert all(p["project_id"] for p in projects)

    def test_stable_project_id(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            projects_dir = Path(tmpdir) / "projects"
            projects_dir.mkdir()
            (projects_dir / "TestProject").mkdir()

            catalog1 = ProjectCatalog(tmpdir)
            proj1 = catalog1.get_catalog()[0]
            original_id = proj1["project_id"]

            # Rename folder
            (projects_dir / "TestProject").rename(projects_dir / "RenamedProject")

            catalog2 = ProjectCatalog(tmpdir)
            proj2 = catalog2.get_catalog()[0]

            assert proj2["project_id"] == original_id
            assert proj2["project_folder_name"] == "RenamedProject"

    def test_no_cross_project_fallback(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            projects_dir = Path(tmpdir) / "projects"
            projects_dir.mkdir()
            (projects_dir / "Proj1").mkdir()
            (projects_dir / "Proj2").mkdir()

            catalog = ProjectCatalog(tmpdir)
            proj1 = catalog.get_project_by_folder("Proj1")
            proj2 = catalog.get_project_by_folder("Proj2")

            assert proj1["project_id"] != proj2["project_id"]
