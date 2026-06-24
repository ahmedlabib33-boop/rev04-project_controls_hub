"""
Tests for Project Isolation
"""
import pytest
import tempfile
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from construction_system.project_catalog import ProjectCatalog
from construction_system.project_context import ProjectContext
from construction_system.importers import DataImporter

class TestProjectIsolation:
    def test_no_cross_project_data(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            projects_dir = Path(tmpdir) / "projects"
            projects_dir.mkdir()
            (projects_dir / "Proj1").mkdir()
            (projects_dir / "Proj2").mkdir()

            catalog = ProjectCatalog(tmpdir)
            projs = catalog.get_catalog()

            ctx1 = ProjectContext(projs[0]["project_id"], tmpdir)
            ctx2 = ProjectContext(projs[1]["project_id"], tmpdir)

            # Verify paths are different
            assert str(ctx1.import_templates_path) != str(ctx2.import_templates_path)
            assert str(ctx1.outputs_path) != str(ctx2.outputs_path)

    def test_empty_data_state(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            projects_dir = Path(tmpdir) / "projects"
            projects_dir.mkdir()
            (projects_dir / "EmptyProject").mkdir()

            catalog = ProjectCatalog(tmpdir)
            proj = catalog.get_catalog()[0]
            ctx = ProjectContext(proj["project_id"], tmpdir)
            importer = DataImporter(ctx)

            data = importer.load_all_project_data()

            # All dataframes should be empty but not None
            for key, df in data.items():
                assert isinstance(df, pd.DataFrame)
                assert "project_id" not in df.columns or df.empty
