"""
RouteGuard AI - Comparison Baselines Service
Calculates exact mathematical baselines:
1. vs. own history: Trailing 8-week rolling average cost per tonne-km, strictly preceding
   the current week (no lookahead, no extrapolation).
2. vs. similar routes: Same-week average cost per tonne-km across all other routes
   sharing the same route_type (Short / Medium / Long), excluding the route itself.
"""

from typing import Optional
import numpy as np
import pandas as pd


def calculate_baselines(weekly_df: pd.DataFrame, window_weeks: int = 8) -> pd.DataFrame:
    """
    Compute own-history and peer-route comparison baselines for each route-week.
    Guarantees no look-ahead leakage and strict self-exclusion for peer averages.
    """
    df = weekly_df.copy()
    df = df.sort_values(["route", "week_of"]).reset_index(drop=True)

    # 1. Own History Baseline
    # Strictly before the current week via shift(1), rolling window of up to window_weeks
    df["history_baseline"] = df.groupby("route", sort=False)["cost_per_tonne_km"].transform(
        lambda s: s.shift(1).rolling(window=window_weeks, min_periods=1).mean()
    )
    df["history_weeks_used"] = df.groupby("route", sort=False)["cost_per_tonne_km"].transform(
        lambda s: s.shift(1).rolling(window=window_weeks, min_periods=1).count()
    ).fillna(0).astype(int)

    # Calculate percentage change vs own history
    # vs_own_history_pct = ((current - baseline) / baseline) * 100
    df["vs_own_history_pct"] = np.where(
        (df["history_baseline"].notnull()) & (df["history_baseline"] > 0),
        ((df["cost_per_tonne_km"] - df["history_baseline"]) / df["history_baseline"]) * 100.0,
        np.nan
    )

    # 2. Similar Routes (Peer) Baseline
    # Group by week_of and route_type, sum the costs and count the routes
    peer_stats = df.groupby(["week_of", "route_type"])["cost_per_tonne_km"].agg(
        peer_sum="sum",
        peer_total_routes="count"
    ).reset_index()

    df = df.merge(peer_stats, on=["week_of", "route_type"], how="left")

    # Exclude current route: peer_count = total_routes - 1, peer_sum = total_sum - current_cost
    peer_count = df["peer_total_routes"] - 1
    df["peer_routes_count"] = np.maximum(0, peer_count)
    df["peer_baseline"] = np.where(
        peer_count > 0,
        (df["peer_sum"] - df["cost_per_tonne_km"]) / peer_count,
        np.nan
    )

    # Calculate percentage change vs peers
    df["vs_similar_routes_pct"] = np.where(
        (df["peer_baseline"].notnull()) & (df["peer_baseline"] > 0),
        ((df["cost_per_tonne_km"] - df["peer_baseline"]) / df["peer_baseline"]) * 100.0,
        np.nan
    )

    # Clean intermediate columns
    df = df.drop(columns=["peer_sum", "peer_total_routes"])
    return df


def format_pct_comparison(
    pct: Optional[float],
    baseline_label: str,
    history_count: Optional[int] = None
) -> str:
    """
    Format percentage string matching sample_output_format_v2.csv contract.
    Examples:
        +35.5% vs this route's past average
        +21.0% vs similar-length routes this week
        -4.2% vs similar-length routes this week
        N/A (no prior history)
        N/A (no similar routes)
    """
    if pct is None or pd.isna(pct):
        if "past average" in baseline_label:
            return "N/A (no prior history)"
        return "N/A (no similar routes)"

    sign = "+" if pct >= 0 else ""
    return f"{sign}{pct:.1f}% vs {baseline_label}"
