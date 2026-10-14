"""
RouteGuard AI - RESTful API Router
Exposes clean, typed endpoints for operations dashboard, corridor exploration,
evidence inspector, AI chat assistant, evaluation reports, and CSV downloads.
"""

from pathlib import Path
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse, PlainTextResponse
from pydantic import BaseModel

from backend.app.config import settings
from backend.app.schemas.models import (
    RouteOverviewSummary, RouteWeekRecord, QARequest, QAResponse
)
from backend.app.services.pipeline import run_pipeline, pipeline_state
from backend.app.services.qa_assistant import qa_assistant
from backend.app.services.note_index import note_index
from backend.app.services.anomaly_detection import evaluate_threshold_sensitivity

router = APIRouter(prefix="/api", tags=["Freight Cost Intelligence"])


class AnalyzeRequest(BaseModel):
    history_threshold_pct: float = 15.0
    peer_threshold_pct: float = 15.0
    trailing_weeks: int = 8


@router.get("/health")
def health_check() -> Dict[str, Any]:
    """Health and status check verifying core paths and data availability."""
    return {
        "status": "healthy",
        "service": "RouteGuard AI - Evidence-Grounded Freight Cost Intelligence",
        "version": "1.0.0",
        "shipments_file_exists": settings.shipments_path.exists(),
        "notes_file_exists": settings.notes_path.exists(),
        "output_csv_exists": settings.output_csv_path.exists(),
        "pipeline_initialized": pipeline_state.overview is not None,
        "total_route_weeks": len(pipeline_state.records) if pipeline_state.records else 0
    }


@router.get("/overview", response_model=RouteOverviewSummary)
def get_overview():
    """Retrieve operational high-level metrics and network summary."""
    if not pipeline_state.overview:
        # Run pipeline if not already executed
        run_pipeline()
    return pipeline_state.overview


@router.get("/routes")
def get_routes(
    route: Optional[str] = None,
    route_type: Optional[str] = None,
    flagged: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500)
):
    """
    Search and filter route-week analytics.
    Filter by corridor, haul length category, verdict, and date range.
    """
    if not pipeline_state.records:
        run_pipeline()

    records = pipeline_state.records

    if route and route.strip():
        records = [r for r in records if route.strip().lower() in r.route.lower()]
    if route_type and route_type.strip() and route_type != "All":
        records = [r for r in records if r.route_type.lower() == route_type.strip().lower()]
    if flagged and flagged.strip() and flagged != "All":
        records = [r for r in records if r.flagged.lower() == flagged.strip().lower()]
    if start_date:
        records = [r for r in records if r.week_of >= start_date]
    if end_date:
        records = [r for r in records if r.week_of <= end_date]

    total_count = len(records)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_items = records[start_idx:end_idx]

    return {
        "total_records": total_count,
        "page": page,
        "page_size": page_size,
        "total_pages": (total_count + page_size - 1) // page_size if page_size > 0 else 1,
        "items": paginated_items
    }


@router.get("/routes/timeseries/{route_name}")
def get_route_timeseries(route_name: str):
    """
    Retrieve full weekly time series for a single corridor
    for interactive trend visualization (cost, history baseline, peer baseline).
    """
    if not pipeline_state.records:
        run_pipeline()

    corridor_records = [
        r for r in pipeline_state.records if r.route.lower() == route_name.lower()
    ]
    if not corridor_records:
        raise HTTPException(status_code=404, detail=f"Route '{route_name}' not found.")

    corridor_records.sort(key=lambda r: r.week_of)
    return {
        "route": route_name,
        "route_type": corridor_records[0].route_type,
        "total_weeks": len(corridor_records),
        "data": corridor_records
    }


@router.get("/notes")
def get_context_notes():
    """Retrieve all indexed contextual real-world notes."""
    if not note_index.initialized:
        run_pipeline()
    return note_index.get_all_notes()


@router.get("/evidence/{route_name}/{week_of}")
def get_evidence_detail(route_name: str, week_of: str):
    """
    Deep evidence audit for a specific route and week.
    Shows evaluated candidate notes, cosine similarity, and 6 hard evidence gates.
    """
    if not pipeline_state.records:
        run_pipeline()

    match = next(
        (r for r in pipeline_state.records if r.route.lower() == route_name.lower() and r.week_of == week_of),
        None
    )
    if not match:
        raise HTTPException(
            status_code=404,
            detail=f"No record found for route '{route_name}' on week '{week_of}'."
        )

    return {
        "route": match.route,
        "week_of": match.week_of,
        "cost_per_tonne_km": match.cost_per_tonne_km,
        "vs_own_history": match.vs_own_history,
        "vs_similar_routes": match.vs_similar_routes,
        "flagged": match.flagged,
        "matched_note_id": match.matched_note_id,
        "reason": match.reason,
        "candidates_evaluated": match.candidates
    }


@router.post("/analyze")
def trigger_analysis(req: AnalyzeRequest):
    """
    Re-run the analytical pipeline with customized thresholds.
    """
    output_df, records, summary = run_pipeline(
        history_threshold_pct=req.history_threshold_pct,
        peer_threshold_pct=req.peer_threshold_pct,
        trailing_weeks=req.trailing_weeks
    )
    return summary


@router.post("/chat", response_model=QAResponse)
def chat_assistant(req: QARequest):
    """
    Conversational QA assistant grounded in verified pipeline computation.
    """
    if not pipeline_state.records:
        run_pipeline()
    return qa_assistant.answer_question(req)


@router.get("/evaluation/sensitivity")
def get_sensitivity():
    """Threshold sensitivity evaluation across alternative thresholds."""
    if pipeline_state.output_df is None:
        run_pipeline()
    # Use in-memory weekly metrics
    from backend.app.services.baselines import calculate_baselines
    from backend.app.services.weekly_analytics import compute_weekly_metrics
    weekly = compute_weekly_metrics(pipeline_state.shipments_df)
    weekly_base = calculate_baselines(weekly, window_weeks=settings.trailing_history_weeks)
    return evaluate_threshold_sensitivity(weekly_base)


@router.get("/cost-log")
def get_cost_log():
    """Retrieve machine-readable token and execution cost log."""
    if not settings.cost_log_path.exists():
        run_pipeline()
    import json
    with open(settings.cost_log_path, "r", encoding="utf-8") as f:
        return json.load(f)


@router.get("/export/csv")
def export_csv():
    """Download the official grading contract CSV (flagged_routes.csv)."""
    if not settings.output_csv_path.exists():
        run_pipeline()
    return FileResponse(
        path=str(settings.output_csv_path),
        filename="flagged_routes.csv",
        media_type="text/csv"
    )


@router.get("/export/report")
def export_audit_report():
    """Download markdown logistics audit report."""
    if not pipeline_state.overview:
        run_pipeline()
    ov = pipeline_state.overview

    md_lines = [
        "# RouteGuard AI — Freight Cost Intelligence Audit Report",
        "",
        f"**Generated at**: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Output SHA-256 Digest**: `{pipeline_state.file_sha256}`",
        "",
        "## Executive Summary",
        f"- **Total Route-Weeks Analyzed**: {ov.total_route_weeks}",
        f"- **Unexplained Anomalies (Escalated for Human Review)**: {ov.unexplained_anomalies}",
        f"- **Evidence-Supported Anomalies (Justified)**: {ov.justified_anomalies}",
        f"- **Normal Operating Route-Weeks**: {ov.normal_route_weeks}",
        f"- **Weighted Network Freight Cost**: {ov.weighted_avg_cost_per_tonne_km:.4f} INR / tonne-km",
        "",
        "## Corridor Performance Breakdown",
        "| Route | Total Weeks | Unexplained | Justified | Avg Cost (INR/t-km) | Max Cost |",
        "|---|---|---|---|---|---|"
    ]
    for r_name, stats in ov.route_breakdown.items():
        md_lines.append(
            f"| {r_name} | {stats['total_weeks']} | {stats['unexplained_anomalies']} | {stats['justified_anomalies']} | {stats['avg_cost']:.2f} | {stats['max_cost']:.2f} |"
        )

    md_lines.extend([
        "",
        "## Evidence-Supported Anomalies",
        "| Route | Week Of | Cost (INR/t-km) | vs History | vs Peers | Note ID | Explanation |",
        "|---|---|---|---|---|---|---|"
    ])
    for rec in pipeline_state.records:
        if rec.flagged == "No (justified)":
            md_lines.append(
                f"| {rec.route} | {rec.week_of} | {rec.cost_per_tonne_km:.2f} | {rec.vs_own_history} | {rec.vs_similar_routes} | {rec.matched_note_id} | {rec.reason} |"
            )

    md_lines.extend([
        "",
        "## Unexplained Spikes Requiring Investigation",
        "| Route | Week Of | Cost (INR/t-km) | vs History | vs Peers | Status | Reason |",
        "|---|---|---|---|---|---|---|"
    ])
    for rec in pipeline_state.records:
        if rec.flagged == "Yes":
            md_lines.append(
                f"| {rec.route} | {rec.week_of} | {rec.cost_per_tonne_km:.2f} | {rec.vs_own_history} | {rec.vs_similar_routes} | {rec.flagged} | {rec.reason} |"
            )

    return PlainTextResponse(content="\n".join(md_lines), media_type="text/markdown")
