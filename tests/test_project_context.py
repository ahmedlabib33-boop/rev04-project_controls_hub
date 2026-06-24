"""
Tests for Project Context
"""
import pytest
import tempfile
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from construction_system.project_catalog import ProjectCatalog
from construction_system.project_context import ProjectContext

class TestProjectContext:
    def test_path_resolution(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            catalog = ProjectCatalog(tmpdir)
            projects_dir = Path(tmpdir) / "projects"
            projects_dir.mkdir()
            (projects_dir / "TestProject").mkdir()

            catalog = ProjectCatalog(tmpdir)
            proj = catalog.get_catalog()[0]

            ctx = ProjectContext(proj["project_id"], tmpdir)

            assert ctx.project_id == proj["project_id"]
            assert ctx.branding_path.exists()
            assert ctx.contracts_source_path.exists()
            assert ctx.import_templates_path.exists()

    def test_project_isolation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            projects_dir = Path(tmpdir) / "projects"
            projects_dir.mkdir()
            (projects_dir / "Proj1").mkdir()
            (projects_dir / "Proj2").mkdir()

            catalog = ProjectCatalog(tmpdir)
            projs = catalog.get_catalog()

            ctx1 = ProjectContext(projs[0]["project_id"], tmpdir)
            ctx2 = ProjectContext(projs[1]["project_id"], tmpdir)

            assert ctx1.project_id != ctx2.project_id
            assert ctx1.project_folder_path != ctx2.project_folder_path
