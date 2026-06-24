"""
Project Analytics Engine - EVM, Progress, and KPI Calculations.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

class ProjectAnalytics:
    """Calculate project control metrics and KPIs."""

    def __init__(self, project_context, database):
        self.ctx = project_context
        self.db = database

    def calculate_progress_metrics(self, activities_df: pd.DataFrame) -> Dict:
        """Calculate planned vs actual progress metrics."""
        if activities_df.empty:
            return {
                "planned_progress": 0.0,
                "actual_progress": 0.0,
                "variance": 0.0,
                "spi": 1.0,
                "total_activities": 0,
                "completed_activities": 0,
                "in_progress": 0,
                "not_started": 0
            }

        total = len(activities_df)
        completed = len(activities_df[activities_df["status"] == "completed"])
        in_progress = len(activities_df[activities_df["status"] == "in_progress"])
        not_started = len(activities_df[activities_df["status"] == "not_started"])

        # Weighted progress
        if "weight" in activities_df.columns and activities_df["weight"].notna().any():
            weights = activities_df["weight"].fillna(1/total)
            planned_progress = (activities_df["progress_percent"].fillna(0) * weights).sum() / weights.sum()
        else:
            planned_progress = activities_df["progress_percent"].mean() if "progress_percent" in activities_df.columns else 0

        actual_progress = activities_df["progress_percent"].mean() if "progress_percent" in activities_df.columns else 0
        variance = actual_progress - planned_progress if planned_progress else 0

        # SPI calculation
        spi = actual_progress / planned_progress if planned_progress > 0 else 1.0

        return {
            "planned_progress": round(planned_progress, 2),
            "actual_progress": round(actual_progress, 2),
            "variance": round(variance, 2),
            "spi": round(spi, 3),
            "total_activities": total,
            "completed_activities": completed,
            "in_progress": in_progress,
            "not_started": not_started
        }

    def calculate_cost_metrics(self, payments_df: pd.DataFrame, contracts_df: pd.DataFrame) -> Dict:
        """Calculate cost performance metrics."""
        if contracts_df.empty:
            total_contract_value = 0
        else:
            total_contract_value = contracts_df["contract_value"].sum()

        if payments_df.empty:
            total_paid = 0
            total_certified = 0
            total_retention = 0
        else:
            total_paid = payments_df["amount_paid"].sum()
            total_certified = payments_df["amount_certified"].sum()
            total_retention = payments_df["retention"].sum()

        cpi = total_certified / total_paid if total_paid > 0 else 1.0
        payment_ratio = total_paid / total_contract_value if total_contract_value > 0 else 0

        return {
            "total_contract_value": total_contract_value,
            "total_paid": total_paid,
            "total_certified": total_certified,
            "total_retention": total_retention,
            "cpi": round(cpi, 3),
            "payment_ratio": round(payment_ratio, 3),
            "remaining_value": total_contract_value - total_paid
        }

    def calculate_risk_metrics(self, risks_df: pd.DataFrame) -> Dict:
        """Calculate risk register metrics."""
        if risks_df.empty:
            return {
                "total_risks": 0,
                "high_risks": 0,
                "medium_risks": 0,
                "low_risks": 0,
                "avg_risk_score": 0,
                "open_risks": 0,
                "mitigated_risks": 0
            }

        total = len(risks_df)

        # Risk scoring
        if "risk_score" in risks_df.columns:
            high = len(risks_df[risks_df["risk_score"] >= 12])
            medium = len(risks_df[(risks_df["risk_score"] >= 6) & (risks_df["risk_score"] < 12)])
            low = len(risks_df[risks_df["risk_score"] < 6])
            avg_score = risks_df["risk_score"].mean()
        else:
            high = medium = low = 0
            avg_score = 0

        open_risks = len(risks_df[risks_df["status"] == "open"]) if "status" in risks_df.columns else 0
        mitigated = len(risks_df[risks_df["status"] == "mitigated"]) if "status" in risks_df.columns else 0

        return {
            "total_risks": total,
            "high_risks": high,
            "medium_risks": medium,
            "low_risks": low,
            "avg_risk_score": round(avg_score, 2),
            "open_risks": open_risks,
            "mitigated_risks": mitigated
        }

    def calculate_delay_metrics(self, delay_events_df: pd.DataFrame) -> Dict:
        """Calculate delay event metrics."""
        if delay_events_df.empty:
            return {
                "total_delay_events": 0,
                "total_delay_days": 0,
                "avg_delay_duration": 0,
                "employer_responsible": 0,
                "contractor_responsible": 0,
                "shared_responsibility": 0,
                "entitled_days": 0
            }

        total_events = len(delay_events_df)
        total_days = delay_events_df["duration_days"].sum() if "duration_days" in delay_events_df.columns else 0
        avg_duration = delay_events_df["duration_days"].mean() if "duration_days" in delay_events_df.columns else 0

        employer = len(delay_events_df[delay_events_df["responsibility"] == "employer"]) if "responsibility" in delay_events_df.columns else 0
        contractor = len(delay_events_df[delay_events_df["responsibility"] == "contractor"]) if "responsibility" in delay_events_df.columns else 0
        shared = len(delay_events_df[delay_events_df["responsibility"] == "shared"]) if "responsibility" in delay_events_df.columns else 0

        entitled = delay_events_df[delay_events_df["entitlement"] == "yes"]["duration_days"].sum() if "entitlement" in delay_events_df.columns else 0

        return {
            "total_delay_events": total_events,
            "total_delay_days": total_days,
            "avg_delay_duration": round(avg_duration, 2),
            "employer_responsible": employer,
            "contractor_responsible": contractor,
            "shared_responsibility": shared,
            "entitled_days": entitled
        }

    def calculate_s_curve_data(self, s_curve_df: pd.DataFrame) -> pd.DataFrame:
        """Prepare S-curve data for visualization."""
        if s_curve_df.empty:
            return pd.DataFrame()

        df = s_curve_df.copy()
        if "date" in df.columns:
            df = df.sort_values("date")
            df["planned_cumulative"] = df["planned_progress"].cumsum()
            df["actual_cumulative"] = df["actual_progress"].cumsum()
            df["variance"] = df["actual_cumulative"] - df["planned_cumulative"]

        return df

    def get_dashboard_summary(self, data: Dict[str, pd.DataFrame]) -> Dict:
        """Get complete dashboard summary."""
        return {
            "progress": self.calculate_progress_metrics(data.get("activities", pd.DataFrame())),
            "cost": self.calculate_cost_metrics(
                data.get("payments", pd.DataFrame()),
                data.get("contracts", pd.DataFrame())
            ),
            "risk": self.calculate_risk_metrics(data.get("risks", pd.DataFrame())),
            "delay": self.calculate_delay_metrics(data.get("delay_events", pd.DataFrame())),
            "s_curve": self.calculate_s_curve_data(data.get("s_curve", pd.DataFrame()))
        }

    def portfolio_summary(self, all_projects_data: List[Dict]) -> Dict:
        """Aggregate metrics across all projects."""
        total_projects = len(all_projects_data)
        total_contract_value = sum(p["cost"]["total_contract_value"] for p in all_projects_data)
        total_payments = sum(p["cost"]["total_paid"] for p in all_projects_data)
        avg_progress = sum(p["progress"]["actual_progress"] for p in all_projects_data) / total_projects if total_projects > 0 else 0
        delayed_projects = sum(1 for p in all_projects_data if p["delay"]["total_delay_days"] > 0)
        high_risk_projects = sum(1 for p in all_projects_data if p["risk"]["high_risks"] > 0)

        return {
            "total_projects": total_projects,
            "total_contract_value": total_contract_value,
            "total_payments": total_payments,
            "average_progress": round(avg_progress, 2),
            "delayed_projects_count": delayed_projects,
            "high_risk_projects_count": high_risk_projects,
            "payment_ratio": round(total_payments / total_contract_value, 3) if total_contract_value > 0 else 0
        }
