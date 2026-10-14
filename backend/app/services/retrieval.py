"""
RouteGuard AI - Contextual Retrieval and Ranking Service
Coordinates vector search across contextual notes, constructs rich anomaly queries,
and executes deterministic ranking with full evidence gate evaluation.
"""

from typing import Dict, List, Optional, Tuple, Any
import pandas as pd

from backend.app.schemas.models import RetrievedCandidate
from backend.app.services.note_index import note_index
from backend.app.services.evidence_validation import evaluate_note_evidence


def build_retrieval_query(
    route: str,
    route_type: str,
    week_of: pd.Timestamp,
    cost_per_tonne_km: float,
    vs_history_pct: Optional[float],
    vs_peer_pct: Optional[float]
) -> str:
    """
    Construct rich contextual query incorporating corridor, week, and cost rise mechanics.
    """
    hist_text = f"+{vs_history_pct:.1f}% vs history" if vs_history_pct is not None else "no history baseline"
    peer_text = f"+{vs_peer_pct:.1f}% vs peers" if vs_peer_pct is not None else "no peer baseline"
    month_name = week_of.strftime("%B %Y")

    return (
        f"Freight cost rise on corridor {route} ({route_type} haul) during week {week_of.strftime('%Y-%m-%d')} ({month_name}). "
        f"Observed {cost_per_tonne_km:.2f} INR per tonne-km ({hist_text}, {peer_text}). "
        f"Highway disruptions, flooding, festival surcharges, diesel price hikes, or toll updates."
    )


def retrieve_and_validate_candidates(
    route: str,
    route_type: str,
    week_of: pd.Timestamp,
    cost_per_tonne_km: float,
    vs_history_pct: Optional[float],
    vs_peer_pct: Optional[float],
    top_k: int = 4
) -> Tuple[Optional[Dict[str, Any]], List[RetrievedCandidate], Optional[Dict[str, Any]]]:
    """
    Retrieve candidate notes for an anomaly, run evidence gates, and rank candidates deterministically.
    Returns:
        best_verified_note: Optional[Dict] - Note that passed all 6 gates, or None
        candidates_detail: List[RetrievedCandidate] - All evaluated candidate notes with gate results
        closest_rejected_note: Optional[Dict] - Top candidate that failed gates (for explanation citation)
    """
    query_str = build_retrieval_query(
        route=route,
        route_type=route_type,
        week_of=week_of,
        cost_per_tonne_km=cost_per_tonne_km,
        vs_history_pct=vs_history_pct,
        vs_peer_pct=vs_peer_pct
    )

    # 1. Vector Search Candidates
    vector_candidates = note_index.query(query_str, n_results=top_k)
    seen_ids = set()
    raw_candidates = []

    for vc in vector_candidates:
        seen_ids.add(vc["note_id"])
        raw_candidates.append(vc)

    # 2. Lexical & Exact Corridor Matching
    # Ensure corridor-specific notes or temporally proximate notes are included in evaluation
    all_notes = note_index.get_all_notes()
    for n in all_notes:
        nid = n["note_id"]
        if nid not in seen_ids:
            is_corridor_match = str(n.get("applies_to", "")).strip().lower() == route.strip().lower()
            note_date = pd.Timestamp(n.get("date")).normalize()
            is_date_proximate = abs((note_date - week_of).days) <= 21

            if is_corridor_match or is_date_proximate:
                seen_ids.add(nid)
                raw_candidates.append({
                    "note_id": nid,
                    "date": n["date"],
                    "applies_to": n["applies_to"],
                    "note": n["note"],
                    "note_text": n["note"],
                    "distance": 0.5,
                    "similarity_score": 0.5
                })

    passing_candidates: List[Tuple[Dict[str, Any], Any]] = []
    rejected_candidates: List[Tuple[Dict[str, Any], Any]] = []
    candidates_detail: List[RetrievedCandidate] = []

    for raw in raw_candidates:
        gate_res = evaluate_note_evidence(
            note=raw,
            route=route,
            week_start=week_of,
            observed_hist_pct=vs_history_pct
        )

        candidate_obj = RetrievedCandidate(
            note_id=raw["note_id"],
            date=raw["date"],
            applies_to=raw["applies_to"],
            note_text=raw["note_text"],
            similarity_score=raw["similarity_score"],
            distance=raw["distance"],
            gates=gate_res
        )
        candidates_detail.append(candidate_obj)

        if gate_res.passed_all_gates:
            passing_candidates.append((raw, gate_res))
        else:
            rejected_candidates.append((raw, gate_res))

    # Deterministic ranking of passing notes
    # 1. Exact route match prioritized over 'All Routes'
    # 2. Date proximity to week_of
    # 3. Stable alphabetical note_id
    if passing_candidates:
        passing_candidates.sort(key=lambda item: (
            0 if str(item[0]["applies_to"]).strip().lower() == route.lower() else 1,
            abs((pd.Timestamp(item[0]["date"]).normalize() - week_of).days),
            str(item[0]["note_id"])
        ))
        best_verified_note = passing_candidates[0][0]
        return best_verified_note, candidates_detail, None

    # If no candidate passed all gates, identify the closest candidate to explain rejection
    if rejected_candidates:
        # Prioritize: 1) route relevance (exact route > All Routes > others)
        #             2) date proximity (days difference to week_of)
        #             3) vector distance
        rejected_candidates.sort(key=lambda item: (
            0 if str(item[0]["applies_to"]).strip().lower() == route.lower() else (1 if str(item[0]["applies_to"]).strip().lower() == "all routes" else 2),
            abs((pd.Timestamp(item[0]["date"]).normalize() - week_of).days),
            item[0].get("distance", 1.0)
        ))
        closest_rejected = rejected_candidates[0][0]
    else:
        closest_rejected = None

    return None, candidates_detail, closest_rejected
