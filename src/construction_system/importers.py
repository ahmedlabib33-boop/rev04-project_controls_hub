"""
Data Import Pipeline - CSV/XLSX loaders with validation.
"""
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

class DataImporter:
    """Import and validate project data files."""

    # Required columns for each data type
    SCHEMAS = {
        "activities": ["activity_id", "activity_name", "wbs_code"],
        "contracts": ["contract_id", "contract_name", "contract_value"],
        "payments": ["payment_id", "amount_certified"],
        "wbs": ["wbs_code", "wbs_name"],
        "risks": ["risk_id", "risk_description"],
        "rfi_status": ["rfi_id", "subject"],
        "steel_status": ["material_type", "quantity"],
        "steel_relationships": ["activity_id", "material_type"],
        "employer_steel_supply": ["material_type", "delivery_date", "quantity"],
        "contractor_steel_supply": ["material_type", "delivery_date", "quantity"],
        "p6_activity_export": ["activity_id", "activity_name"],
        "relationship_file": ["predecessor", "successor"],
        "ifc_conflict": ["conflict_id", "description"],
        "concurrency_matrix": ["activity_id", "concurrent_with"],
        "contract_library": ["clause_id", "clause_text"],
        "progress_updates": ["activity_id", "progress_percent", "report_date"],
        "s_curve": ["date", "planned_progress", "actual_progress"],
    }

    def __init__(self, project_context):
        self.ctx = project_context
        self.warnings: List[Dict] = []

    def _add_warning(self, file_type: str, message: str, severity: str = "WARNING"):
        """Add validation warning."""
        warning = {
            "timestamp": datetime.now().isoformat(),
            "file_type": file_type,
            "message": message,
            "severity": severity,
            "project_id": self.ctx.project_id
        }
        self.warnings.append(warning)
        # Log to project logs
        self.ctx.log(f"[{severity}] {file_type}: {message}", level=severity)

    def load_csv(self, filename: str, file_type: str, 
                 date_columns: List[str] = None,
                 numeric_columns: List[str] = None) -> pd.DataFrame:
        """Load CSV file with validation."""
        filepath = self.ctx.import_templates_path / filename

        if not filepath.exists():
            self._add_warning(file_type, f"File not found: {filename}", "WARNING")
            return pd.DataFrame()

        try:
            df = pd.read_csv(filepath)
            df = self._validate_and_clean(df, file_type, date_columns, numeric_columns)
            df["project_id"] = self.ctx.project_id
            return df
        except Exception as e:
            self._add_warning(file_type, f"Error loading {filename}: {str(e)}", "ERROR")
            return pd.DataFrame()

    def load_excel(self, filename: str, file_type: str,
                   sheet_name: str = 0,
                   date_columns: List[str] = None,
                   numeric_columns: List[str] = None) -> pd.DataFrame:
        """Load Excel file with validation."""
        filepath = self.ctx.import_templates_path / filename

        if not filepath.exists():
            self._add_warning(file_type, f"File not found: {filename}", "WARNING")
            return pd.DataFrame()

        try:
            df = pd.read_excel(filepath, sheet_name=sheet_name)
            df = self._validate_and_clean(df, file_type, date_columns, numeric_columns)
            df["project_id"] = self.ctx.project_id
            return df
        except Exception as e:
            self._add_warning(file_type, f"Error loading {filename}: {str(e)}", "ERROR")
            return pd.DataFrame()

    def _validate_and_clean(self, df: pd.DataFrame, file_type: str,
                            date_columns: List[str] = None,
                            numeric_columns: List[str] = None) -> pd.DataFrame:
        """Validate columns and clean data types."""
        if df.empty:
            self._add_warning(file_type, "File is empty", "WARNING")
            return df

        # Check required columns
        required = self.SCHEMAS.get(file_type, [])
        missing = [col for col in required if col not in df.columns]
        if missing:
            self._add_warning(
                file_type, 
                f"Missing required columns: {', '.join(missing)}",
                "ERROR"
            )

        # Normalize column names
        df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

        # Parse dates
        if date_columns:
            for col in date_columns:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors="coerce")

        # Parse numerics
        if numeric_columns:
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce")

        # Normalize activity IDs and WBS codes
        if "activity_id" in df.columns:
            df["activity_id"] = df["activity_id"].astype(str).str.strip().str.upper()
        if "wbs_code" in df.columns:
            df["wbs_code"] = df["wbs_code"].astype(str).str.strip().str.upper()

        return df

    def get_warnings(self) -> List[Dict]:
        """Return all warnings."""
        return self.warnings

    def load_all_project_data(self) -> Dict[str, pd.DataFrame]:
        """Load all standard data files for the project."""
        data = {}

        # Activities
        data["activities"] = self.load_csv(
            "activities.csv", "activities",
            date_columns=["planned_start", "planned_finish", "actual_start", "actual_finish"],
            numeric_columns=["duration_planned", "duration_actual", "progress_percent"]
        )

        # WBS
        data["wbs"] = self.load_csv(
            "wbs.csv", "wbs",
            numeric_columns=["weight", "level"]
        )

        # Contracts
        data["contracts"] = self.load_csv(
            "contracts.csv", "contracts",
            date_columns=["signed_date", "completion_date"],
            numeric_columns=["contract_value"]
        )

        # Payments
        data["payments"] = self.load_csv(
            "payments.csv", "payments",
            date_columns=["invoice_date"],
            numeric_columns=["amount_certified", "amount_paid", "retention"]
        )

        # S-Curve
        data["s_curve"] = self.load_csv(
            "s_curve.csv", "s_curve",
            date_columns=["date"],
            numeric_columns=["planned_progress", "actual_progress"]
        )

        # Risks
        data["risks"] = self.load_csv(
            "risks.csv", "risks",
            numeric_columns=["probability", "impact", "risk_score"]
        )

        # RFI Status
        data["rfi_status"] = self.load_csv(
            "rfi_status.csv", "rfi_status",
            date_columns=["date_submitted", "date_responded"],
            numeric_columns=["days_open"]
        )

        # Progress Updates
        data["progress_updates"] = self.load_csv(
            "progress_updates.csv", "progress_updates",
            date_columns=["report_date"],
            numeric_columns=["progress_percent"]
        )

        # Steel data
        data["steel_status"] = self.load_csv(
            "steel_status.csv", "steel_status",
            numeric_columns=["quantity"]
        )

        data["steel_relationships"] = self.load_csv(
            "steel_relationships.csv", "steel_relationships"
        )

        data["employer_steel_supply"] = self.load_csv(
            "employer_steel_supply.csv", "employer_steel_supply",
            date_columns=["delivery_date"],
            numeric_columns=["quantity"]
        )

        data["contractor_steel_supply"] = self.load_csv(
            "contractor_steel_supply.csv", "contractor_steel_supply",
            date_columns=["delivery_date"],
            numeric_columns=["quantity"]
        )

        # P6 and relationship files
        data["p6_activity_export"] = self.load_csv(
            "p6_activity_export.csv", "p6_activity_export",
            date_columns=["start_date", "finish_date"],
            numeric_columns=["original_duration", "remaining_duration"]
        )

        data["relationship_file"] = self.load_csv(
            "relationship_file.csv", "relationship_file",
            numeric_columns=["lag"]
        )

        data["concurrency_matrix"] = self.load_csv(
            "concurrency_matrix.csv", "concurrency_matrix"
        )

        data["contract_library"] = self.load_csv(
            "contract_library.csv", "contract_library"
        )

        return data
