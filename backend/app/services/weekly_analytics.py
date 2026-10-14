"""
RouteGuard AI - Weekly Analytics Service
Aggregates shipments into weekly route metrics:
weekly_cost_per_tonne_km = sum(freight_cost_inr) / sum(quantity_tonnes * distance_km)
Strictly adheres to Monday-Sunday week bounds and weighted tonne-km formulation.
"""

import pandas as pd
import numpy as np


def compute_weekly_metrics(shipments: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate shipments by route, route_type, and Monday week_of.
    The denominator must be the sum of tonne-kilometres across shipments,
    not the unweighted mean of individual shipment ratios.
    """
    required_cols = {"route", "route_type", "week_of", "freight_cost_inr", "tonne_km"}
    if not required_cols.issubset(shipments.columns):
        raise ValueError(f"Shipments dataframe missing required columns for aggregation: {required_cols - set(shipments.columns)}")

    # Aggregate by route, route_type, week_of
    weekly = shipments.groupby(["route", "route_type", "week_of"], as_index=False).agg(
        total_cost_inr=("freight_cost_inr", "sum"),
        total_tonne_km=("tonne_km", "sum"),
        shipment_count=("shipment_id", "count") if "shipment_id" in shipments.columns else ("freight_cost_inr", "size"),
    )

    # Division with zero-protection
    weekly["cost_per_tonne_km"] = np.where(
        weekly["total_tonne_km"] > 0,
        weekly["total_cost_inr"] / weekly["total_tonne_km"],
        np.nan
    )

    # Deterministic sorting
    weekly = weekly.sort_values(["route", "week_of"]).reset_index(drop=True)
    return weekly
