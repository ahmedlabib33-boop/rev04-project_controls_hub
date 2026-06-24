
"""
Letters Intelligence Engine - Auto-ingest and classify correspondence.
"""
import os
import re
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import sqlite3

class LettersIntelligence:
    """Ingest, classify, and link project correspondence."""

    CLASSIFICATIONS = [
        "delay_notice",
        "eot_notice", 
        "claim_notice",
        "instruction",
        "warning",
        "payment_issue",
        "rfi_design_issue",
        "steel_material_issue",
        "site_handover_issue",
        "general_correspondence"
    ]

    def __init__(self, project_context):
        self.ctx = project_context

    def scan_inbox(self) -> List[Dict]:
        """Scan all inbox folders for documents."""
        letters = []
        inbox_path = self.ctx.letters_inbox_path

        if not inbox_path.exists():
            return letters

        for sender_folder in inbox_path.iterdir():
            if not sender_folder.is_dir():
                continue

            sender = sender_folder.name

            for file_path in sender_folder.rglob("*"):
                if file_path.is_file() and not file_path.name.startswith("."):
                    letter_info = self._process_file(file_path, sender)
                    if letter_info:
                        letters.append(letter_info)

        return letters

    def _process_file(self, file_path: Path, sender: str) -> Optional[Dict]:
        """Process a single file and extract metadata."""
        file_name = file_path.name
        file_ext = file_path.suffix.lower()

        # Extract date from filename
        date_match = re.search(r'(\d{4}[-_]?\d{2}[-_]?\d{2})', file_name)
        date_str = date_match.group(1).replace('_', '-').replace('-', '-') if date_match else None

        # Extract reference number
        ref_match = re.search(r'([A-Z]{2,5}[-_]?\d{2,6})', file_name)
        reference = ref_match.group(1) if ref_match else None

        # Extract subject from filename
        subject = file_name.replace(file_ext, "").replace("_", " ").replace("-", " ").title()

        # Classify document
        classification = self._classify_document(file_name, subject)

        # Detect document type
        doc_type = self._detect_document_type(file_ext)

        return {
            "project_id": self.ctx.project_id,
            "file_name": file_name,
            "file_path": str(file_path),
            "sender": sender,
            "date": date_str,
            "reference_number": reference,
            "subject": subject,
            "document_type": doc_type,
            "classification": classification,
            "linked_claim_id": None,
            "linked_delay_event_id": None,
            "content_summary": None,
            "processed_at": datetime.now().isoformat()
        }

    def _classify_document(self, file_name: str, subject: str) -> str:
        """Classify document based on content keywords."""
        text = (file_name + " " + subject).lower()

        keywords = {
            "delay_notice": ["delay", "late", "behind schedule", "time extension"],
            "eot_notice": ["eot", "extension of time", "time extension", "prolongation"],
            "claim_notice": ["claim", "dispute", "compensation", "damages"],
            "instruction": ["instruction", "directive", "order", "variation"],
            "warning": ["warning", "notice", "default", "breach"],
            "payment_issue": ["payment", "invoice", "certification", "retention"],
            "rfi_design_issue": ["rfi", "design", "drawing", "specification"],
            "steel_material_issue": ["steel", "rebar", "material", "supply"],
            "site_handover_issue": ["handover", "possession", "access", "mobilization"]
        }

        scores = {}
        for classification, words in keywords.items():
            scores[classification] = sum(1 for word in words if word in text)

        if max(scores.values()) > 0:
            return max(scores, key=scores.get)

        return "general_correspondence"

    def _detect_document_type(self, extension: str) -> str:
        """Detect document type from extension."""
        types = {
            ".pdf": "PDF",
            ".docx": "Word",
            ".doc": "Word",
            ".txt": "Text",
            ".xlsx": "Excel",
            ".xls": "Excel",
            ".csv": "CSV",
            ".eml": "Email",
            ".msg": "Email"
        }
        return types.get(extension.lower(), "Unknown")

    def link_to_claims(self, letters_df: pd.DataFrame, claims_df: pd.DataFrame) -> pd.DataFrame:
        """Link letters to claims based on reference numbers and keywords."""
        if letters_df.empty or claims_df.empty:
            return letters_df

        letters_df = letters_df.copy()
        letters_df["linked_claim_id"] = None

        for idx, letter in letters_df.iterrows():
            subject = str(letter.get("subject", "")).lower()
            ref = str(letter.get("reference_number", "")).lower()

            for _, claim in claims_df.iterrows():
                claim_id = str(claim.get("claim_id", ""))
                claim_title = str(claim.get("claim_title", "")).lower()

                if ref and ref in claim_id.lower():
                    letters_df.at[idx, "linked_claim_id"] = claim_id
                    break

                if any(word in claim_title for word in subject.split() if len(word) > 4):
                    letters_df.at[idx, "linked_claim_id"] = claim_id
                    break

        return letters_df

    def link_to_delays(self, letters_df: pd.DataFrame, delay_events_df: pd.DataFrame) -> pd.DataFrame:
        """Link letters to delay events."""
        if letters_df.empty or delay_events_df.empty:
            return letters_df

        letters_df = letters_df.copy()
        letters_df["linked_delay_event_id"] = None

        for idx, letter in letters_df.iterrows():
            subject = str(letter.get("subject", "")).lower()

            for _, event in delay_events_df.iterrows():
                event_id = str(event.get("event_id", ""))
                event_desc = str(event.get("event_description", "")).lower()

                if any(word in event_desc for word in subject.split() if len(word) > 4):
                    letters_df.at[idx, "linked_delay_event_id"] = event_id
                    break

        return letters_df

    def create_letters_register(self, letters: List[Dict]) -> pd.DataFrame:
        """Create a formal letters register."""
        if not letters:
            return pd.DataFrame()

        df = pd.DataFrame(letters)
        df["project_id"] = self.ctx.project_id
        df["register_date"] = datetime.now().isoformat()

        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
            df = df.sort_values("date", ascending=False)

        return df

    def export_register(self, register_df: pd.DataFrame, format: str = "excel") -> str:
        """Export letters register."""
        if register_df.empty:
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if format == "excel":
            output_path = self.ctx.exports_path / f"letters_register_{timestamp}.xlsx"
            register_df.to_excel(output_path, index=False, sheet_name="Letters Register")
            return str(output_path)

        elif format == "markdown":
            output_path = self.ctx.exports_path / f"letters_register_{timestamp}.md"
            with open(output_path, "w") as f:
                f.write("# Letters Intelligence Register\n\n")
                f.write(f"**Project:** {self.ctx.project_display_name}\n")
                f.write(f"**Generated:** {datetime.now().isoformat()}\n\n")
                f.write(f"**Total Letters:** {len(register_df)}\n\n")
                f.write("| Date | Reference | Sender | Subject | Classification | Type |\n")
                f.write("|------|-----------|--------|---------|----------------|------|\n")

                for _, row in register_df.iterrows():
                    date = str(row.get("date", ""))[:10] if pd.notna(row.get("date")) else "N/A"
                    ref = row.get("reference_number", "N/A") or "N/A"
                    sender = row.get("sender", "N/A")
                    subject = row.get("subject", "N/A")[:50]
                    classification = row.get("classification", "N/A")
                    doc_type = row.get("document_type", "N/A")
                    f.write(f"| {date} | {ref} | {sender} | {subject} | {classification} | {doc_type} |\n")

            return str(output_path)

        return None

    def run_full_ingest(self, data: Dict[str, pd.DataFrame]) -> Dict:
        """Run full letters intelligence pipeline."""
        letters = self.scan_inbox()

        if not letters:
            return {
                "status": "no_data",
                "message": "No letters found in inbox",
                "project_id": self.ctx.project_id,
                "register": pd.DataFrame(),
                "export_path": None
            }

        register = self.create_letters_register(letters)
        register = self.link_to_claims(register, data.get("claims", pd.DataFrame()))
        register = self.link_to_delays(register, data.get("delay_events", pd.DataFrame()))

        export_path = self.export_register(register, "excel")
        md_export = self.export_register(register, "markdown")

        return {
            "status": "complete",
            "project_id": self.ctx.project_id,
            "total_letters": len(register),
            "classifications": register["classification"].value_counts().to_dict() if not register.empty else {},
            "register": register,
            "excel_export": export_path,
            "markdown_export": md_export
        }
