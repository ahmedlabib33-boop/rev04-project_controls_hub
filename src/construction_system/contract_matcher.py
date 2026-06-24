"""
Claims Intelligence Engine - Contract clause matching and claim evaluation.
"""
import pandas as pd
import numpy as np
import sqlite3
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime

class ClaimsIntelligence:
    """Evaluate claims using contract clauses, evidence, and structured decision matrix."""

    DECISION_MATRIX = {
        "YES_VALID": "YES valid - Strong contractual basis with complete evidence",
        "YES_SUPPORTING": "YES supporting - Valid but needs additional evidence",
        "NO": "NO - No contractual basis or evidence",
        "NOT_ENOUGH_DATA": "NOT ENOUGH DATA - Insufficient information to evaluate",
        "COMMERCIAL_ONLY": "COMMERCIAL ONLY - Commercial negotiation recommended"
    }

    def __init__(self, project_context):
        self.ctx = project_context

    def load_contract_clauses(self) -> pd.DataFrame:
        """Load contract clauses from contract library."""
        # Try database first
        db_path = self.ctx.contracts_db_path
        if db_path.exists():
            try:
                conn = sqlite3.connect(db_path)
                df = pd.read_sql_query(
                    "SELECT * FROM contract_clauses WHERE project_id = ?",
                    conn, params=(self.ctx.project_id,)
                )
                conn.close()
                if not df.empty:
                    return df
            except:
                pass

        # Try CSV
        csv_path = self.ctx.contracts_source_path / "contract_library.csv"
        if csv_path.exists():
            return pd.read_csv(csv_path)

        return pd.DataFrame()

    def load_claims_data(self) -> pd.DataFrame:
        """Load existing claims data."""
        db_path = self.ctx.contracts_db_path
        if db_path.exists():
            try:
                conn = sqlite3.connect(db_path)
                df = pd.read_sql_query(
                    "SELECT * FROM claims WHERE project_id = ?",
                    conn, params=(self.ctx.project_id,)
                )
                conn.close()
                return df
            except:
                pass
        return pd.DataFrame()

    def evaluate_issue(self,
                      issue_title: str,
                      issue_description: str,
                      contract_clauses_df: pd.DataFrame,
                      evidence_df: pd.DataFrame,
                      delay_events_df: pd.DataFrame,
                      payment_records_df: pd.DataFrame,
                      letters_df: pd.DataFrame) -> Dict:
        """Evaluate a single claim issue using structured decision matrix."""

        # Search for relevant contract clauses
        relevant_clauses = self._find_relevant_clauses(issue_description, contract_clauses_df)

        # Gather evidence
        evidence_used = self._gather_evidence(issue_description, evidence_df, letters_df)

        # Check delay events
        related_delays = self._find_related_delays(issue_description, delay_events_df)

        # Check payment records
        related_payments = self._find_related_payments(issue_description, payment_records_df)

        # Decision logic
        has_contract_basis = len(relevant_clauses) > 0
        has_evidence = len(evidence_used) > 0
        has_delay_impact = len(related_delays) > 0
        has_cost_impact = len(related_payments) > 0

        if not has_contract_basis and not has_evidence:
            decision = "NOT_ENOUGH_DATA"
        elif has_contract_basis and has_evidence and (has_delay_impact or has_cost_impact):
            decision = "YES_VALID"
        elif has_contract_basis and has_evidence:
            decision = "YES_SUPPORTING"
        elif has_contract_basis and not has_evidence:
            decision = "NOT_ENOUGH_DATA"
        elif not has_contract_basis and has_evidence:
            decision = "COMMERCIAL_ONLY"
        else:
            decision = "NO"

        # Calculate impacts
        time_impact = sum(d.get("duration_days", 0) for d in related_delays)
        cost_impact = sum(p.get("amount", 0) for p in related_payments)

        # Determine responsibility
        responsibility = self._determine_responsibility(related_delays, relevant_clauses)

        # Missing evidence
        missing_evidence = []
        if not has_evidence:
            missing_evidence.append("Supporting documentation")
        if has_delay_impact and not any("delay" in e.get("evidence_type", "") for e in evidence_used):
            missing_evidence.append("Delay event documentation")
        if has_cost_impact and not any("cost" in e.get("evidence_type", "") for e in evidence_used):
            missing_evidence.append("Cost breakdown documentation")

        # Recommendation
        recommendation = self._generate_recommendation(decision, missing_evidence)

        return {
            "project_id": self.ctx.project_id,
            "issue_title": issue_title,
            "issue_description": issue_description,
            "contract_basis": relevant_clauses,
            "evidence_used": evidence_used,
            "missing_evidence": missing_evidence,
            "related_delays": related_delays,
            "related_payments": related_payments,
            "responsibility": responsibility,
            "time_impact_potential": time_impact,
            "cost_impact_potential": cost_impact,
            "claim_strength": self.DECISION_MATRIX[decision],
            "decision": decision,
            "recommended_next_action": recommendation,
            "evaluated_at": datetime.now().isoformat()
        }

    def _find_relevant_clauses(self, issue_description: str, clauses_df: pd.DataFrame) -> List[Dict]:
        """Find contract clauses relevant to the issue."""
        if clauses_df.empty:
            return []

        relevant = []
        issue_lower = issue_description.lower()

        for _, clause in clauses_df.iterrows():
            clause_text = str(clause.get("clause_text", "")).lower()
            clause_id = str(clause.get("clause_id", ""))

            # Simple keyword matching
            keywords = issue_lower.split()
            match_score = sum(1 for kw in keywords if len(kw) > 3 and kw in clause_text)

            if match_score > 0 or any(kw in clause_id.lower() for kw in keywords if len(kw) > 2):
                relevant.append({
                    "clause_id": clause_id,
                    "clause_text": clause.get("clause_text", "")[:500],
                    "relevance_score": match_score
                })

        return sorted(relevant, key=lambda x: x["relevance_score"], reverse=True)[:5]

    def _gather_evidence(self, issue_description: str, evidence_df: pd.DataFrame, letters_df: pd.DataFrame) -> List[Dict]:
        """Gather relevant evidence."""
        evidence = []

        if not evidence_df.empty:
            for _, row in evidence_df.iterrows():
                evidence.append({
                    "evidence_id": row.get("evidence_id", ""),
                    "evidence_type": row.get("evidence_type", ""),
                    "description": row.get("description", "")[:200]
                })

        if not letters_df.empty:
            issue_lower = issue_description.lower()
            for _, letter in letters_df.iterrows():
                subject = str(letter.get("subject", "")).lower()
                if any(kw in subject for kw in issue_lower.split() if len(kw) > 3):
                    evidence.append({
                        "evidence_id": letter.get("letter_id", ""),
                        "evidence_type": "letter",
                        "description": f"Letter: {letter.get('subject', '')}"
                    })

        return evidence[:10]

    def _find_related_delays(self, issue_description: str, delay_events_df: pd.DataFrame) -> List[Dict]:
        """Find delay events related to the issue."""
        if delay_events_df.empty:
            return []

        related = []
        issue_lower = issue_description.lower()

        for _, event in delay_events_df.iterrows():
            desc = str(event.get("event_description", "")).lower()
            if any(kw in desc for kw in issue_lower.split() if len(kw) > 3):
                related.append({
                    "event_id": event.get("event_id", ""),
                    "description": event.get("event_description", "")[:200],
                    "duration_days": event.get("duration_days", 0),
                    "responsibility": event.get("responsibility", "")
                })

        return related

    def _find_related_payments(self, issue_description: str, payments_df: pd.DataFrame) -> List[Dict]:
        """Find payment records related to the issue."""
        if payments_df.empty:
            return []

        # For now, return recent payments as potentially related
        return payments_df.head(5).to_dict("records")

    def _determine_responsibility(self, related_delays: List[Dict], relevant_clauses: List[Dict]) -> str:
        """Determine responsibility indication."""
        if not related_delays:
            return "Undetermined"

        responsibilities = [d.get("responsibility", "") for d in related_delays]

        if all(r == "employer" for r in responsibilities if r):
            return "Likely Employer"
        elif all(r == "contractor" for r in responsibilities if r):
            return "Likely Contractor"
        elif any(r == "employer" for r in responsibilities if r) and any(r == "contractor" for r in responsibilities if r):
            return "Shared/Disputed"
        else:
            return "Requires Investigation"

    def _generate_recommendation(self, decision: str, missing_evidence: List[str]) -> str:
        """Generate recommended next action."""
        recommendations = {
            "YES_VALID": "Proceed with formal claim submission. Document is strong.",
            "YES_SUPPORTING": "Strengthen evidence base before submission.",
            "NO": "Do not pursue as formal claim. Consider commercial discussion.",
            "NOT_ENOUGH_DATA": f"Gather missing evidence: {', '.join(missing_evidence) if missing_evidence else 'Additional documentation'}",
            "COMMERCIAL_ONLY": "Pursue through commercial negotiation rather than contractual claim."
        }
        return recommendations.get(decision, "Review and reassess")

    def batch_evaluate(self, issues: List[Dict], data: Dict[str, pd.DataFrame]) -> List[Dict]:
        """Evaluate multiple issues."""
        clauses = self.load_contract_clauses()

        results = []
        for issue in issues:
            result = self.evaluate_issue(
                issue.get("title", ""),
                issue.get("description", ""),
                clauses,
                data.get("claim_evidence", pd.DataFrame()),
                data.get("delay_events", pd.DataFrame()),
                data.get("payments", pd.DataFrame()),
                data.get("letters", pd.DataFrame())
            )
            results.append(result)

        return results
