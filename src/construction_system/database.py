"""
SQLite Database Layer - All tables scoped by project_id.
"""
import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Any
import pandas as pd

class ProjectDatabase:
    """SQLite database with project-scoped tables."""

    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_tables()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_tables(self):
        """Initialize all required tables."""
        with self._get_connection() as conn:
            # Projects metadata
            conn.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    project_id TEXT PRIMARY KEY,
                    display_name TEXT,
                    status TEXT,
                    sector TEXT,
                    currency TEXT,
                    created_at TEXT,
                    updated_at TEXT
                )
            """)

            # Activities
            conn.execute("""
                CREATE TABLE IF NOT EXISTS activities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id TEXT NOT NULL,
                    activity_id TEXT,
                    activity_name TEXT,
                    wbs_code TEXT,
                    planned_start TEXT,
                    planned_finish TEXT,
                    actual_start TEXT,
                    actual_finish TEXT,
                    duration_planned REAL,
                    duration_actual REAL,
                    progress_percent REAL,
                    status TEXT,
                    created_at TEXT
                )
            """)

            # WBS
            conn.execute("""
                CREATE TABLE IF NOT EXISTS wbs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id TEXT NOT NULL,
                    wbs_code TEXT,
                    wbs_name TEXT,
                    level INTEGER,
                    parent_code TEXT,
                    weight REAL,
                    created_at TEXT
                )
            """)

            # Contracts
            conn.execute("""
                CREATE TABLE IF NOT EXISTS contracts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id TEXT NOT NULL,
                    contract_id TEXT,
                    contract_name TEXT,
                    contract_value REAL,
                    signed_date TEXT,
                    completion_date TEXT,
                    status TEXT,
                    party_employer TEXT,
                    party_contractor TEXT,
                    created_at TEXT
                )
            """)

            # Payments
            conn.execute("""
                CREATE TABLE IF NOT EXISTS payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id TEXT NOT NULL,
                    payment_id TEXT,
                    invoice_date TEXT,
                    amount_certified REAL,
                    amount_paid REAL,
                    retention REAL,
                    status TEXT,
                    created_at TEXT
                )
            """)

            # Risks
            conn.execute("""
                CREATE TABLE IF NOT EXISTS risks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id TEXT NOT NULL,
                    risk_id TEXT,
                    risk_description TEXT,
                    probability REAL,
                    impact REAL,
                    risk_score REAL,
                    mitigation TEXT,
                    owner TEXT,
                    status TEXT,
                    created_at TEXT
                )
            """)

            # RFI Status
            conn.execute("""
                CREATE TABLE IF NOT EXISTS rfi_status (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id TEXT NOT NULL,
                    rfi_id TEXT,
                    subject TEXT,
                    date_submitted TEXT,
                    date_responded TEXT,
                    status TEXT,
                    days_open INTEGER,
                    created_at TEXT
                )
            """)

            # Steel Supply
            conn.execute("""
                CREATE TABLE IF NOT EXISTS steel_supply (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id TEXT NOT NULL,
                    supply_id TEXT,
                    material_type TEXT,
                    diameter TEXT,
                    quantity REAL,
                    delivery_date TEXT,
                    source TEXT,
                    status TEXT,
                    created_at TEXT
                )
            """)

            # Steel Demand
            conn.execute("""
                CREATE TABLE IF NOT EXISTS steel_demand (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id TEXT NOT NULL,
                    demand_id TEXT,
                    activity_id TEXT,
                    material_type TEXT,
                    diameter TEXT,
                    quantity_required REAL,
                    required_date TEXT,
                    created_at TEXT
                )
            """)

            # Delay Events
            conn.execute("""
                CREATE TABLE IF NOT EXISTS delay_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id TEXT NOT NULL,
                    event_id TEXT,
                    event_description TEXT,
                    event_type TEXT,
                    start_date TEXT,
                    end_date TEXT,
                    duration_days REAL,
                    responsibility TEXT,
                    entitlement TEXT,
                    affected_activities TEXT,
                    status TEXT,
                    created_at TEXT
                )
            """)

            # Letters
            conn.execute("""
                CREATE TABLE IF NOT EXISTS letters (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id TEXT NOT NULL,
                    letter_id TEXT,
                    file_name TEXT,
                    sender TEXT,
                    recipient TEXT,
                    date TEXT,
                    reference_number TEXT,
                    subject TEXT,
                    document_type TEXT,
                    classification TEXT,
                    linked_claim_id TEXT,
                    linked_delay_event_id TEXT,
                    content_summary TEXT,
                    created_at TEXT
                )
            """)

            # Claims
            conn.execute("""
                CREATE TABLE IF NOT EXISTS claims (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id TEXT NOT NULL,
                    claim_id TEXT,
                    claim_title TEXT,
                    claim_basis TEXT,
                    issue_description TEXT,
                    contract_clause TEXT,
                    evidence_refs TEXT,
                    missing_evidence TEXT,
                    responsibility TEXT,
                    time_impact_days REAL,
                    cost_impact REAL,
                    claim_strength TEXT,
                    recommendation TEXT,
                    status TEXT,
                    created_at TEXT
                )
            """)

            # Claim Evidence
            conn.execute("""
                CREATE TABLE IF NOT EXISTS claim_evidence (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id TEXT NOT NULL,
                    claim_id TEXT,
                    evidence_id TEXT,
                    evidence_type TEXT,
                    file_path TEXT,
                    description TEXT,
                    created_at TEXT
                )
            """)

            # Generated Outputs
            conn.execute("""
                CREATE TABLE IF NOT EXISTS generated_outputs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id TEXT NOT NULL,
                    output_type TEXT,
                    output_path TEXT,
                    source_data_status TEXT,
                    generated_at TEXT,
                    parameters TEXT
                )
            """)

            # Validation Logs
            conn.execute("""
                CREATE TABLE IF NOT EXISTS validation_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id TEXT NOT NULL,
                    validation_type TEXT,
                    message TEXT,
                    severity TEXT,
                    created_at TEXT
                )
            """)

            # Data Lineage Events
            conn.execute("""
                CREATE TABLE IF NOT EXISTS data_lineage_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id TEXT NOT NULL,
                    source_file TEXT,
                    module_name TEXT,
                    operation TEXT,
                    output_table TEXT,
                    record_count INTEGER,
                    timestamp TEXT
                )
            """)

            conn.commit()

    def insert_dataframe(self, table: str, df: pd.DataFrame, project_id: str):
        """Insert dataframe into table with project_id."""
        if df.empty:
            return

        df = df.copy()
        if "project_id" not in df.columns:
            df["project_id"] = project_id

        # Add created_at if missing
        if "created_at" not in df.columns:
            df["created_at"] = datetime.now().isoformat()

        with self._get_connection() as conn:
            df.to_sql(table, conn, if_exists="append", index=False)

    def query(self, sql: str, params: tuple = ()) -> pd.DataFrame:
        """Execute query and return dataframe."""
        with self._get_connection() as conn:
            return pd.read_sql_query(sql, conn, params=params)

    def execute(self, sql: str, params: tuple = ()):
        """Execute SQL statement."""
        with self._get_connection() as conn:
            conn.execute(sql, params)
            conn.commit()

    def get_project_data(self, table: str, project_id: str) -> pd.DataFrame:
        """Get all data for a specific project."""
        return self.query(
            f"SELECT * FROM {table} WHERE project_id = ?",
            (project_id,)
        )

    def clear_project_data(self, table: str, project_id: str):
        """Clear all data for a project from a table."""
        self.execute(f"DELETE FROM {table} WHERE project_id = ?", (project_id,))

    def log_validation(self, project_id: str, validation_type: str, message: str, severity: str = "INFO"):
        """Log a validation event."""
        self.execute("""
            INSERT INTO validation_logs (project_id, validation_type, message, severity, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (project_id, validation_type, message, severity, datetime.now().isoformat()))

    def log_lineage(self, project_id: str, source_file: str, module_name: str, 
                    operation: str, output_table: str, record_count: int):
        """Log data lineage event."""
        self.execute("""
            INSERT INTO data_lineage_events 
            (project_id, source_file, module_name, operation, output_table, record_count, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (project_id, source_file, module_name, operation, output_table, 
              record_count, datetime.now().isoformat()))
