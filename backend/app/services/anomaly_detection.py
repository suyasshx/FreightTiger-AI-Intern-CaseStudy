"""
RouteGuard AI - Anomaly Detection Service
Detects abnormal positive freight cost increases against own-history or peer baselines.
Implements configurable thresholds and sensitivity evaluation.
"""

from typing import Dict, List, Any
import numpy as np
import pandas as pd


def detect_anomalies(
    df: pd.DataFrame,
    history_threshold_pct: float = 15.0,
    peer_threshold_pct: float = 15.0
) -> pd.DataFrame:
    """
    Flag route-weeks that exceed configured cost increase thresholds.
    A route-week is an anomaly candidate if EITHER:
      - vs_own_history_pct >= history_threshold_pct
      - vs_similar_routes_pct >= peer_threshold_pct
    Only positive cost increases qualify. Missing baselines never count as anomalies.
    """
    out = df.copy()

    history_trigger = (
        out["vs_own_history_pct"].notnull() &
        (out["vs_own_history_pct"] >= history_threshold_pct)
    )

    peer_trigger = (
        out["vs_similar_routes_pct"].notnull() &
        (out["vs_similar_routes_pct"] >= peer_threshold_pct)
    )

    out["history_anomaly_triggered"] = history_trigger
    out["peer_anomaly_triggered"] = peer_trigger
    out["is_anomaly_candidate"] = history_trigger | peer_trigger

    return out


def evaluate_threshold_sensitivity(
    df: pd.DataFrame,
    threshold_range: List[float] = [5.0, 10.0, 12.0, 15.0, 20.0, 25.0, 30.0]
) -> List[Dict[str, Any]]:
    """
    Sensitivity evaluation across alternative threshold levels.
    Enables audit of how anomaly candidates shift across policy thresholds.
    """
    sensitivity_results = []
    for th in threshold_range:
        temp = detect_anomalies(df, history_threshold_pct=th, peer_threshold_pct=th)
        cand_count = int(temp["is_anomaly_candidate"].sum())
        hist_only = int((temp["history_anomaly_triggered"] & ~temp["peer_anomaly_triggered"]).sum())
        peer_only = int((~temp["history_anomaly_triggered"] & temp["peer_anomaly_triggered"]).sum())
        both = int((temp["history_anomaly_triggered"] & temp["peer_anomaly_triggered"]).sum())

        sensitivity_results.append({
            "threshold_pct": th,
            "anomaly_candidate_count": cand_count,
            "history_triggered_only": hist_only,
            "peer_triggered_only": peer_only,
            "both_triggered": both,
            "pct_of_total_route_weeks": round(cand_count / len(df) * 100.0, 2)
        })

    return sensitivity_results
