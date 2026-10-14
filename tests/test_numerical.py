"""
RouteGuard AI - Numerical Baseline and Aggregation Unit Tests
Verifies mathematical correctness, zero lookahead leakage, strict peer self-exclusion,
and Monday calendar week boundaries.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime

from backend.app.services.ingestion import compute_monday_week, format_route_name
from backend.app.services.weekly_analytics import compute_weekly_metrics
from backend.app.services.baselines import calculate_baselines, format_pct_comparison
from backend.app.services.anomaly_detection import detect_anomalies


def test_monday_week_boundaries():
    """Verify that any date is correctly mapped to its Monday start date."""
    # 2025-03-09 was a Sunday -> Monday is 2025-03-03
    d1 = pd.Series([pd.Timestamp("2025-03-09")])
    assert compute_monday_week(d1).iloc[0] == pd.Timestamp("2025-03-03")

    # 2025-03-03 is a Monday -> Monday is 2025-03-03
    d2 = pd.Series([pd.Timestamp("2025-03-03")])
    assert compute_monday_week(d2).iloc[0] == pd.Timestamp("2025-03-03")

    # 2025-03-05 is a Wednesday -> Monday is 2025-03-03
    d3 = pd.Series([pd.Timestamp("2025-03-05")])
    assert compute_monday_week(d3).iloc[0] == pd.Timestamp("2025-03-03")


def test_weighted_cost_formula():
    """
    Verify cost_per_tonne_km = sum(cost) / sum(quantity * distance).
    Must NOT be the unweighted arithmetic mean of individual shipment ratios.
    """
    shipments = pd.DataFrame([
        {
            "shipment_id": "S1",
            "route": "Mumbai-Pune",
            "route_type": "Short",
            "week_of": pd.Timestamp("2025-01-06"),
            "quantity_tonnes": 10.0,
            "distance_km": 100.0,    # 1000 t-km
            "freight_cost_inr": 2000.0,  # ratio = 2.0
            "tonne_km": 1000.0
        },
        {
            "shipment_id": "S2",
            "route": "Mumbai-Pune",
            "route_type": "Short",
            "week_of": pd.Timestamp("2025-01-06"),
            "quantity_tonnes": 50.0,
            "distance_km": 100.0,    # 5000 t-km
            "freight_cost_inr": 15000.0, # ratio = 3.0
            "tonne_km": 5000.0
        }
    ])
    weekly = compute_weekly_metrics(shipments)
    assert len(weekly) == 1
    # Total cost = 17,000, Total t-km = 6,000.
    # Weighted = 17000 / 6000 = 2.8333...
    # Unweighted mean of ratios would be (2.0 + 3.0) / 2 = 2.50 (WRONG)
    expected_weighted = 17000.0 / 6000.0
    actual = weekly["cost_per_tonne_km"].iloc[0]
    assert abs(actual - expected_weighted) < 1e-6
    assert abs(actual - 2.50) > 0.1  # Confirms unweighted mean was not used


def test_zero_lookahead_history_baseline():
    """Verify history baseline uses only strictly preceding weeks and excludes current week."""
    # 3 consecutive weeks for a route
    weekly = pd.DataFrame([
        {"route": "RouteA", "route_type": "Short", "week_of": pd.Timestamp("2025-01-06"), "cost_per_tonne_km": 3.0, "total_cost_inr": 300, "total_tonne_km": 100, "shipment_count": 1},
        {"route": "RouteA", "route_type": "Short", "week_of": pd.Timestamp("2025-01-13"), "cost_per_tonne_km": 4.0, "total_cost_inr": 400, "total_tonne_km": 100, "shipment_count": 1},
        {"route": "RouteA", "route_type": "Short", "week_of": pd.Timestamp("2025-01-20"), "cost_per_tonne_km": 5.0, "total_cost_inr": 500, "total_tonne_km": 100, "shipment_count": 1},
    ])
    result = calculate_baselines(weekly, window_weeks=8)

    # Week 1: 0 prior observations -> baseline is NaN
    assert pd.isna(result["history_baseline"].iloc[0])
    assert result["history_weeks_used"].iloc[0] == 0
    assert pd.isna(result["vs_own_history_pct"].iloc[0])

    # Week 2: exactly 1 prior week (Week 1 = 3.0) -> baseline is 3.0
    assert result["history_baseline"].iloc[1] == 3.0
    assert result["history_weeks_used"].iloc[1] == 1
    # ((4.0 - 3.0) / 3.0) * 100 = +33.33%
    assert abs(result["vs_own_history_pct"].iloc[1] - 33.3333) < 0.01

    # Week 3: exactly 2 prior weeks (3.0 and 4.0) -> baseline is 3.5. (Current week 5.0 must NOT be in baseline)
    assert result["history_baseline"].iloc[2] == 3.5
    assert result["history_weeks_used"].iloc[2] == 2
    # ((5.0 - 3.5) / 3.5) * 100 = +42.86%
    assert abs(result["vs_own_history_pct"].iloc[2] - 42.8571) < 0.01


def test_peer_baseline_excludes_self():
    """Verify peer average uses same week, same route_type, and strictly excludes the route itself."""
    weekly = pd.DataFrame([
        # Two Short routes in week 1
        {"route": "Short-1", "route_type": "Short", "week_of": pd.Timestamp("2025-01-06"), "cost_per_tonne_km": 2.0, "total_cost_inr": 200, "total_tonne_km": 100, "shipment_count": 1},
        {"route": "Short-2", "route_type": "Short", "week_of": pd.Timestamp("2025-01-06"), "cost_per_tonne_km": 4.0, "total_cost_inr": 400, "total_tonne_km": 100, "shipment_count": 1},
        # One Medium route in week 1
        {"route": "Medium-1", "route_type": "Medium", "week_of": pd.Timestamp("2025-01-06"), "cost_per_tonne_km": 6.0, "total_cost_inr": 600, "total_tonne_km": 100, "shipment_count": 1},
    ])
    result = calculate_baselines(weekly)

    s1 = result[result["route"] == "Short-1"].iloc[0]
    s2 = result[result["route"] == "Short-2"].iloc[0]
    m1 = result[result["route"] == "Medium-1"].iloc[0]

    # Short-1 peer baseline must be Short-2 cost (4.0)
    assert s1["peer_baseline"] == 4.0
    assert s1["peer_routes_count"] == 1
    # ((2.0 - 4.0) / 4.0) * 100 = -50.0%
    assert s1["vs_similar_routes_pct"] == -50.0

    # Short-2 peer baseline must be Short-1 cost (2.0)
    assert s2["peer_baseline"] == 2.0
    assert s2["peer_routes_count"] == 1
    # ((4.0 - 2.0) / 2.0) * 100 = +100.0%
    assert s2["vs_similar_routes_pct"] == 100.0

    # Medium-1 has no peers of same type in that week -> peer baseline must be NaN
    assert pd.isna(m1["peer_baseline"])
    assert m1["peer_routes_count"] == 0
    assert pd.isna(m1["vs_similar_routes_pct"])


def test_anomaly_threshold_boundaries():
    """Verify that anomaly triggers activate strictly at or above the threshold and ignore negative diffs."""
    df = pd.DataFrame([
        {"route": "R1", "route_type": "Short", "week_of": pd.Timestamp("2025-01-06"), "vs_own_history_pct": 15.0, "vs_similar_routes_pct": 0.0},
        {"route": "R2", "route_type": "Short", "week_of": pd.Timestamp("2025-01-06"), "vs_own_history_pct": 14.99, "vs_similar_routes_pct": 5.0},
        {"route": "R3", "route_type": "Short", "week_of": pd.Timestamp("2025-01-06"), "vs_own_history_pct": -30.0, "vs_similar_routes_pct": 15.1},
        {"route": "R4", "route_type": "Short", "week_of": pd.Timestamp("2025-01-06"), "vs_own_history_pct": np.nan, "vs_similar_routes_pct": np.nan},
    ])
    res = detect_anomalies(df, history_threshold_pct=15.0, peer_threshold_pct=15.0)

    # R1: exactly 15.0% on history -> Triggered
    assert res["is_anomaly_candidate"].iloc[0] == True
    # R2: 14.99% and 5.0% -> NOT triggered
    assert res["is_anomaly_candidate"].iloc[1] == False
    # R3: history is negative (-30%), but peers is +15.1% -> Triggered by peers
    assert res["is_anomaly_candidate"].iloc[2] == True
    # R4: NaNs -> NOT triggered
    assert res["is_anomaly_candidate"].iloc[3] == False
