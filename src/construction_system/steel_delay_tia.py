"""
Steel Delay Time Impact Analysis Engine.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

class SteelDelayTIA:
    """Calculate steel supply delay impacts on project schedule."""

    def __init__(self, project_context):
        self.ctx = project_context

    def load_baseline_data(self) -> pd.DataFrame:
        """Load baseline schedule data."""
        baseline_path = self.ctx.baseline_path
        if not baseline_path.exists():
            return pd.DataFrame()

        files = list(baseline_path.glob("*.csv"))
        if not files:
            return pd.DataFrame()

        return pd.read_csv(files[0])

    def load_impacted_data(self) -> pd.DataFrame:
        """Load impacted/updated schedule data."""
        tia_path = self.ctx.delay_tia_path / "steel_delay_tia_templates"
        if not tia_path.exists():
            return pd.DataFrame()

        files = list(tia_path.glob("*.csv"))
        if not files:
            return pd.DataFrame()

        return pd.read_csv(files[0])

    def calculate_steel_availability(self, 
                                     supply_df: pd.DataFrame,
                                     demand_df: pd.DataFrame) -> pd.DataFrame:
        """Calculate cumulative steel availability vs demand."""
        if supply_df.empty or demand_df.empty:
            return pd.DataFrame()

        # Aggregate supply by date and material type
        supply_agg = supply_df.groupby(["delivery_date", "material_type"]).agg({
            "quantity": "sum"
        }).reset_index()
        supply_agg.columns = ["date", "material_type", "supply_quantity"]

        # Aggregate demand by required date and material type
        demand_agg = demand_df.groupby(["required_date", "material_type"]).agg({
            "quantity_required": "sum"
        }).reset_index()
        demand_agg.columns = ["date", "material_type", "demand_quantity"]

        # Merge supply and demand
        merged = pd.merge(
            supply_agg, demand_agg,
            on=["date", "material_type"],
            how="outer"
        ).fillna(0)

        # Calculate cumulative
        merged = merged.sort_values(["material_type", "date"])
        merged["cumulative_supply"] = merged.groupby("material_type")["supply_quantity"].cumsum()
        merged["cumulative_demand"] = merged.groupby("material_type")["demand_quantity"].cumsum()
        merged["availability"] = merged["cumulative_supply"] - merged["cumulative_demand"]

        return merged

    def detect_first_negative_availability(self, availability_df: pd.DataFrame) -> Optional[Dict]:
        """Detect first date where steel availability goes negative."""
        if availability_df.empty:
            return None

        negative = availability_df[availability_df["availability"] < 0]
        if negative.empty:
            return None

        first = negative.iloc[0]
        return {
            "date": first["date"],
            "material_type": first["material_type"],
            "availability": first["availability"],
            "cumulative_supply": first["cumulative_supply"],
            "cumulative_demand": first["cumulative_demand"]
        }

    def identify_affected_activities(self,
                                   availability_df: pd.DataFrame,
                                   activities_df: pd.DataFrame,
                                   steel_relationships_df: pd.DataFrame) -> pd.DataFrame:
        """Identify activities affected by steel shortage."""
        if availability_df.empty or activities_df.empty or steel_relationships_df.empty:
            return pd.DataFrame()

        # Find negative availability periods
        negative_periods = availability_df[availability_df["availability"] < 0]
        if negative_periods.empty:
            return pd.DataFrame()

        # Get material types with shortage
        shortage_materials = negative_periods["material_type"].unique()

        # Find activities requiring these materials
        affected = steel_relationships_df[
            steel_relationships_df["material_type"].isin(shortage_materials)
        ]

        # Merge with activities
        if "activity_id" in activities_df.columns:
            result = pd.merge(
                affected,
                activities_df[["activity_id", "activity_name", "planned_start", "planned_finish"]],
                on="activity_id",
                how="left"
            )
        else:
            result = affected

        result["project_id"] = self.ctx.project_id
        return result

    def calculate_delay_windows(self,
                               affected_activities_df: pd.DataFrame,
                               availability_df: pd.DataFrame) -> pd.DataFrame:
        """Calculate delay windows for affected activities."""
        if affected_activities_df.empty or availability_df.empty:
            return pd.DataFrame()

        delays = []
        for _, activity in affected_activities_df.iterrows():
            material = activity.get("material_type", "")

            # Find negative availability for this material
            material_shortage = availability_df[
                (availability_df["material_type"] == material) &
                (availability_df["availability"] < 0)
            ]

            if material_shortage.empty:
                continue

            first_shortage = material_shortage.iloc[0]
            last_shortage = material_shortage.iloc[-1]

            delay_window = {
                "activity_id": activity.get("activity_id", ""),
                "activity_name": activity.get("activity_name", ""),
                "material_type": material,
                "delay_start_date": first_shortage["date"],
                "delay_end_date": last_shortage["date"],
                "impacted_duration_days": (pd.to_datetime(last_shortage["date"]) - 
                                            pd.to_datetime(first_shortage["date"])).days,
                "shortage_quantity": abs(first_shortage["availability"]),
                "project_id": self.ctx.project_id
            }
            delays.append(delay_window)

        return pd.DataFrame(delays)

    def analyze_concurrency(self,
                           delay_events_df: pd.DataFrame,
                           concurrency_matrix_df: pd.DataFrame) -> pd.DataFrame:
        """Analyze concurrent delay events."""
        if delay_events_df.empty or concurrency_matrix_df.empty:
            return pd.DataFrame()

        # Merge delay events with concurrency matrix
        merged = pd.merge(
            delay_events_df,
            concurrency_matrix_df,
            on="activity_id",
            how="inner"
        )

        merged["project_id"] = self.ctx.project_id
        return merged

    def generate_tia_summary(self,
                            availability_df: pd.DataFrame,
                            affected_activities_df: pd.DataFrame,
                            delay_windows_df: pd.DataFrame,
                            concurrency_df: pd.DataFrame) -> Dict:
        """Generate TIA summary report."""
        first_negative = self.detect_first_negative_availability(availability_df)

        missing_evidence = []
        if availability_df.empty:
            missing_evidence.append("Steel supply data")
        if affected_activities_df.empty:
            missing_evidence.append("Activity-steel relationship mapping")
        if delay_windows_df.empty:
            missing_evidence.append("Delay window calculations")

        total_impact_days = delay_windows_df["impacted_duration_days"].sum() if not delay_windows_df.empty else 0
        affected_count = len(affected_activities_df) if not affected_activities_df.empty else 0

        return {
            "project_id": self.ctx.project_id,
            "analysis_date": datetime.now().isoformat(),
            "first_shortage_detected": first_negative is not None,
            "first_shortage_details": first_negative,
            "total_affected_activities": affected_count,
            "total_impact_days": total_impact_days,
            "concurrent_events": len(concurrency_df) if not concurrency_df.empty else 0,
            "missing_evidence": missing_evidence,
            "status": "complete" if not missing_evidence else "incomplete",
            "entitlement_assessment": "Further analysis required" if missing_evidence else "Ready for review"
        }

    def run_full_analysis(self, data: Dict[str, pd.DataFrame]) -> Dict:
        """Run complete steel delay TIA analysis."""
        # Load data
        supply = pd.concat([
            data.get("employer_steel_supply", pd.DataFrame()),
            data.get("contractor_steel_supply", pd.DataFrame())
        ], ignore_index=True)

        demand = data.get("steel_demand", pd.DataFrame())
        activities = data.get("activities", pd.DataFrame())
        relationships = data.get("steel_relationships", pd.DataFrame())
        concurrency = data.get("concurrency_matrix", pd.DataFrame())

        # Check for sufficient data
        if supply.empty or demand.empty:
            return {
                "status": "insufficient_data",
                "message": "Not enough data: steel supply and demand data required",
                "missing_items": ["steel supply data", "steel demand data"] if supply.empty or demand.empty else [],
                "project_id": self.ctx.project_id
            }

        # Run analysis steps
        availability = self.calculate_steel_availability(supply, demand)
        affected = self.identify_affected_activities(availability, activities, relationships)
        delay_windows = self.calculate_delay_windows(affected, availability)
        concurrency_analysis = self.analyze_concurrency(
            data.get("delay_events", pd.DataFrame()), concurrency
        )

        summary = self.generate_tia_summary(availability, affected, delay_windows, concurrency_analysis)

        return {
            "status": summary["status"],
            "summary": summary,
            "availability_table": availability,
            "affected_activities": affected,
            "delay_windows": delay_windows,
            "concurrency_analysis": concurrency_analysis,
            "project_id": self.ctx.project_id
        }
