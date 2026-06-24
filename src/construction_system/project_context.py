"""
Project Context Engine - Resolves all paths for a selected project.
"""
from pathlib import Path
from typing import Optional
from .project_catalog import ProjectCatalog

class ProjectContext:
    """Receives project_id and resolves all project-specific paths."""

    def __init__(self, project_id: str, root_path: str = "."):
        self.catalog = ProjectCatalog(root_path)
        self.project_id = project_id
        self.project_data = self.catalog.get_project(project_id)

        if not self.project_data:
            raise ValueError(f"Project {project_id} not found")

        self.root_path = Path(root_path).resolve()
        self.projects_root = self.root_path / "projects"
        self.project_folder_path = Path(self.project_data["project_folder_path"])

        # Resolve all standard paths
        self.branding_path = self.project_folder_path / "1-branding"
        self.contracts_source_path = self.project_folder_path / "2-contracts" / "source"
        self.contracts_evidence_path = self.project_folder_path / "2-contracts" / "evidence"
        self.evidence_path = self.project_folder_path / "3-evidence"
        self.notes_path = self.project_folder_path / "4-notes"
        self.import_templates_path = self.project_folder_path / "data" / "import_templates"
        self.delay_tia_path = self.project_folder_path / "data" / "delay_analysis"
        self.delay_methodology_path = self.project_folder_path / "data" / "methodology"
        self.baseline_path = self.project_folder_path / "bl"
        self.fixed_path = self.project_folder_path / "bl" / "fixed"
        self.letters_path = self.project_folder_path / "letters_intelligence"
        self.letters_inbox_path = self.project_folder_path / "letters_intelligence" / "inbox"
        self.source_excel_path = self.project_folder_path / "source_excel"
        self.outputs_path = self.project_folder_path / "outputs"
        self.reports_path = self.project_folder_path / "outputs" / "reports"
        self.slides_path = self.project_folder_path / "outputs" / "slides"
        self.exports_path = self.project_folder_path / "outputs" / "exports"
        self.logs_path = self.project_folder_path / "logs"
        self.contracts_db_path = self.project_folder_path / "2-contracts" / "contract_claims.db"

        # Ensure directories exist
        for path in [
            self.branding_path, self.contracts_source_path, self.contracts_evidence_path,
            self.evidence_path, self.notes_path, self.import_templates_path,
            self.delay_tia_path, self.delay_methodology_path, self.baseline_path,
            self.fixed_path, self.letters_path, self.letters_inbox_path,
            self.source_excel_path, self.outputs_path, self.reports_path,
            self.slides_path, self.exports_path, self.logs_path
        ]:
            path.mkdir(parents=True, exist_ok=True)

    @property
    def project_display_name(self) -> str:
        return self.project_data.get("project_display_name", "Unknown")

    @property
    def status(self) -> str:
        return self.project_data.get("status", "active")

    @property
    def sector(self) -> str:
        return self.project_data.get("sector", "construction")

    @property
    def currency(self) -> str:
        return self.project_data.get("currency", "USD")

    def get_data_file(self, filename: str) -> Path:
        """Get path to a data file in import_templates."""
        return self.import_templates_path / filename

    def get_source_file(self, filename: str) -> Path:
        """Get path to a source excel file."""
        return self.source_excel_path / filename

    def get_output_file(self, filename: str, subfolder: str = "reports") -> Path:
        """Get path for output file."""
        folder = self.project_folder_path / "outputs" / subfolder
        folder.mkdir(parents=True, exist_ok=True)
        return folder / filename

    def log(self, message: str, level: str = "INFO"):
        """Write to project log file."""
        from datetime import datetime
        log_file = self.logs_path / "system.log"
        timestamp = datetime.now().isoformat()
        with open(log_file, "a") as f:
            f.write(f"[{timestamp}] [{level}] {message}\n")
