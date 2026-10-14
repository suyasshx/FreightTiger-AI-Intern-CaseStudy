"""
RouteGuard AI - End-to-End Pipeline Orchestration Service
Coordinates data ingestion, weekly aggregation, baseline calculations,
anomaly candidate identification, contextual RAG retrieval, evidence gating,
verdict classification, and standards-compliant CSV export.
"""

import csv
import hashlib
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List
import pandas as pd

from backend.app.config import settings
from backend.app.schemas.models import RouteWeekRecord, RouteOverviewSummary
from backend.app.services.ingestion import load_and_validate_datasets
from backend.app.services.weekly_analytics import compute_weekly_metrics
from backend.app.services.baselines import calculate_baselines
from backend.app.services.anomaly_detection import detect_anomalies
from backend.app.services.note_index import note_index
from backend.app.services.verdicts import classify_route_weeks, OUTPUT_COLUMNS
from backend.app.services.cost_tracking import cost_tracker


def compute_sha256(filepath: str | Path) -> str:
    """Compute cryptographic SHA-256 digest of a generated file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


class PipelineState:
    """In-memory cache of latest analyzed pipeline run for rapid API queries."""
    shipments_df: Optional[pd.DataFrame] = None
    notes_df: Optional[pd.DataFrame] = None
    quality_report: Optional[Dict[str, Any]] = None
    output_df: Optional[pd.DataFrame] = None
    records: List[RouteWeekRecord] = []
    overview: Optional[RouteOverviewSummary] = None
    file_sha256: Optional[str] = None


pipeline_state = PipelineState()


def run_pipeline(
    shipments_path: Optional[Path] = None,
    notes_path: Optional[Path] = None,
    output_path: Optional[Path] = None,
    history_threshold_pct: float = 15.0,
    peer_threshold_pct: float = 15.0,
    trailing_weeks: int = 8
) -> Tuple[pd.DataFrame, List[RouteWeekRecord], Dict[str, Any]]:
    """
    Execute the complete RouteGuard AI pipeline end-to-end.
    """
    s_path = shipments_path or settings.shipments_path
    n_path = notes_path or settings.notes_path
    out_path = output_path or settings.output_csv_path

    # Step 1: Ingestion & Schema Sanitization
    shipments_clean, notes_clean, quality_report = load_and_validate_datasets(s_path, n_path)

    # Step 2: Index Context Notes into Vector Store
    note_index.initialize(notes_clean)
    cost_tracker.record_indexing(len(notes_clean))

    # Step 3: Compute Weekly Aggregates
    weekly_metrics = compute_weekly_metrics(shipments_clean)

    # Step 4: Baseline Calculations
    weekly_with_baselines = calculate_baselines(weekly_metrics, window_weeks=trailing_weeks)

    # Step 5: Anomaly Candidate Detection
    weekly_anomalies = detect_anomalies(
        weekly_with_baselines,
        history_threshold_pct=history_threshold_pct,
        peer_threshold_pct=peer_threshold_pct
    )

    cost_tracker.record_ingestion(
        shipment_count=len(shipments_clean),
        route_week_count=len(weekly_anomalies)
    )

    # Step 6: RAG Retrieval, Gate Validation, and Graded Verdict Assignment
    output_df, record_models = classify_route_weeks(weekly_anomalies, top_k_candidates=4)

    # Step 7: Export to Standards-Compliant CSV
    out_path.parent.mkdir(parents=True, exist_ok=True)
    # Using Pandas with csv.QUOTE_MINIMAL and explicit newline for cross-platform stability
    output_df.to_csv(
        out_path,
        index=False,
        columns=OUTPUT_COLUMNS,
        float_format="%.2f",
        quoting=csv.QUOTE_MINIMAL,
        lineterminator="\n"
    )

    file_hash = compute_sha256(out_path)

    # Step 8: Finalize Execution Cost Log
    cost_report = cost_tracker.finalize_report(settings.cost_log_path)

    # Step 9: Build Analytical Overview Metrics for Dashboard
    total_rw = len(output_df)
    unexplained = int((output_df["flagged"] == "Yes").sum())
    justified = int((output_df["flagged"] == "No (justified)").sum())
    normal = int((output_df["flagged"] == "No").sum())

    total_spend = float(shipments_clean["freight_cost_inr"].sum())
    total_tonne_km = float(shipments_clean["tonne_km"].sum())
    weighted_cost = total_spend / total_tonne_km if total_tonne_km > 0 else 0.0

    # Build weekly trend
    weekly_summary = output_df.groupby("week_of").agg(
        avg_cost=("cost_per_tonne_km", "mean"),
        anomaly_count=("flagged", lambda s: int((s != "No").sum())),
        unexplained_count=("flagged", lambda s: int((s == "Yes").sum())),
        justified_count=("flagged", lambda s: int((s == "No (justified)").sum()))
    ).reset_index().to_dict(orient="records")

    # Build route breakdown
    route_breakdown: Dict[str, Dict[str, Any]] = {}
    for r_name, group in output_df.groupby("route"):
        route_breakdown[r_name] = {
            "total_weeks": len(group),
            "unexplained_anomalies": int((group["flagged"] == "Yes").sum()),
            "justified_anomalies": int((group["flagged"] == "No (justified)").sum()),
            "avg_cost": round(float(group["cost_per_tonne_km"].mean()), 2),
            "min_cost": round(float(group["cost_per_tonne_km"].min()), 2),
            "max_cost": round(float(group["cost_per_tonne_km"].max()), 2),
        }

    # Extract notable recent anomalies
    recent_anomalies = [
        rec.model_dump() for rec in record_models if rec.flagged != "No"
    ]

    overview = RouteOverviewSummary(
        total_route_weeks=total_rw,
        unexplained_anomalies=unexplained,
        justified_anomalies=justified,
        normal_route_weeks=normal,
        total_shipments=len(shipments_clean),
        total_freight_spend_inr=round(total_spend, 2),
        total_tonne_km=round(total_tonne_km, 2),
        weighted_avg_cost_per_tonne_km=round(weighted_cost, 4),
        route_breakdown=route_breakdown,
        weekly_trend=weekly_summary,
        recent_anomalies=recent_anomalies
    )

    # Update in-memory state for API serving
    pipeline_state.shipments_df = shipments_clean
    pipeline_state.notes_df = notes_clean
    pipeline_state.quality_report = quality_report
    pipeline_state.output_df = output_df
    pipeline_state.records = record_models
    pipeline_state.overview = overview
    pipeline_state.file_sha256 = file_hash

    summary = {
        "status": "success",
        "output_path": str(out_path),
        "total_route_weeks": total_rw,
        "unexplained_anomalies": unexplained,
        "justified_anomalies": justified,
        "normal_route_weeks": normal,
        "sha256": file_hash,
        "runtime_seconds": cost_report.runtime_seconds,
        "quality_report": quality_report
    }

    return output_df, record_models, summary
