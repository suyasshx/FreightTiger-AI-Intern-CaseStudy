"""
RouteGuard AI - Verdict Classification Service
Combines mathematical baselines, anomaly triggers, contextual retrieval, and evidence gates
into final graded verdict assignments and plain-English reasons.
"""

from typing import List, Tuple, Dict, Any
import pandas as pd
import numpy as np

from backend.app.schemas.models import RouteWeekRecord, RetrievedCandidate
from backend.app.services.baselines import format_pct_comparison
from backend.app.services.retrieval import retrieve_and_validate_candidates
from backend.app.services.explanations import (
    generate_justified_explanation,
    generate_unexplained_explanation,
    generate_normal_explanation,
)

OUTPUT_COLUMNS = [
    "route",
    "week_of",
    "cost_per_tonne_km",
    "vs_own_history",
    "vs_similar_routes",
    "flagged",
    "matched_note_id",
    "reason",
]


def classify_route_weeks(
    df: pd.DataFrame,
    top_k_candidates: int = 4
) -> Tuple[pd.DataFrame, List[RouteWeekRecord]]:
    """
    Produce the exact 8-column graded output table along with rich typed models.
    Guarantees:
      - 'No (justified)' always has valid matched_note_id
      - 'Yes' and 'No' always have empty matched_note_id
      - cost_per_tonne_km rounded to 2 decimal places
      - week_of in ISO YYYY-MM-DD
    """
    rows = []
    record_models: List[RouteWeekRecord] = []

    for _, r in df.iterrows():
        route = str(r["route"])
        route_type = str(r["route_type"])
        week_ts = pd.Timestamp(r["week_of"])
        week_str = week_ts.strftime("%Y-%m-%d")
        cost = float(r["cost_per_tonne_km"])
        cost_rounded = round(cost, 2)

        hist_pct = float(r["vs_own_history_pct"]) if pd.notna(r["vs_own_history_pct"]) else None
        peer_pct = float(r["vs_similar_routes_pct"]) if pd.notna(r["vs_similar_routes_pct"]) else None
        hist_count = int(r["history_weeks_used"]) if "history_weeks_used" in r and pd.notna(r["history_weeks_used"]) else 0
        peer_count = int(r["peer_routes_count"]) if "peer_routes_count" in r and pd.notna(r["peer_routes_count"]) else 0

        vs_hist_str = format_pct_comparison(hist_pct, "this route's past average", hist_count)
        vs_peer_str = format_pct_comparison(peer_pct, "similar-length routes this week")

        is_cand = bool(r.get("is_anomaly_candidate", False))

        candidates_evaluated: List[RetrievedCandidate] = []
        if not is_cand:
            verdict = "No"
            matched_id = ""
            reason = generate_normal_explanation()
        else:
            best_note, candidates_evaluated, closest_rejected = retrieve_and_validate_candidates(
                route=route,
                route_type=route_type,
                week_of=week_ts,
                cost_per_tonne_km=cost,
                vs_history_pct=hist_pct,
                vs_peer_pct=peer_pct,
                top_k=top_k_candidates
            )

            if best_note is not None:
                verdict = "No (justified)"
                matched_id = str(best_note["note_id"])
                reason = generate_justified_explanation(best_note)
            else:
                verdict = "Yes"
                matched_id = ""
                reason = generate_unexplained_explanation(route, week_ts, closest_rejected)

        # Graded output table row
        rows.append({
            "route": route,
            "week_of": week_str,
            "cost_per_tonne_km": cost_rounded,
            "vs_own_history": vs_hist_str,
            "vs_similar_routes": vs_peer_str,
            "flagged": verdict,
            "matched_note_id": matched_id,
            "reason": reason,
        })

        # Structured record for frontend UI / analytical inspection
        record_models.append(RouteWeekRecord(
            route=route,
            week_of=week_str,
            route_type=route_type,
            cost_per_tonne_km=float(cost_rounded),
            vs_own_history=vs_hist_str,
            vs_similar_routes=vs_peer_str,
            flagged=verdict,
            matched_note_id=matched_id,
            reason=reason,
            total_cost_inr=float(r["total_cost_inr"]),
            total_tonne_km=float(r["total_tonne_km"]),
            shipment_count=int(r["shipment_count"]),
            history_baseline=round(float(r["history_baseline"]), 4) if pd.notna(r["history_baseline"]) else None,
            history_weeks_used=hist_count,
            vs_own_history_pct=round(hist_pct, 2) if hist_pct is not None else None,
            peer_baseline=round(float(r["peer_baseline"]), 4) if pd.notna(r["peer_baseline"]) else None,
            peer_routes_count=peer_count,
            vs_similar_routes_pct=round(peer_pct, 2) if peer_pct is not None else None,
            is_anomaly=is_cand,
            candidates=candidates_evaluated
        ))

    output_df = pd.DataFrame(rows, columns=OUTPUT_COLUMNS)
    return output_df, record_models
