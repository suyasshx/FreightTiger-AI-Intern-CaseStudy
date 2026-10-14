"""
RouteGuard AI - Data Models and Schemas
Typed Pydantic models for domain entities, pipeline intermediate states, API responses, and eval reports.
"""

from datetime import date
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ContextNoteModel(BaseModel):
    note_id: str
    date: str
    applies_to: str
    note: str


class GateCheckDetail(BaseModel):
    passed: bool
    description: str


class EvidenceGateResult(BaseModel):
    note_id: str
    route_gate: GateCheckDetail
    temporal_gate: GateCheckDetail
    causal_gate: GateCheckDetail
    negative_filter_gate: GateCheckDetail
    magnitude_gate: GateCheckDetail
    passed_all_gates: bool
    summary: str


class RetrievedCandidate(BaseModel):
    note_id: str
    date: str
    applies_to: str
    note_text: str
    similarity_score: float
    distance: float
    gates: Optional[EvidenceGateResult] = None


class RouteWeekRecord(BaseModel):
    route: str
    week_of: str
    route_type: str
    cost_per_tonne_km: float
    vs_own_history: str
    vs_similar_routes: str
    flagged: str  # 'No', 'No (justified)', 'Yes'
    matched_note_id: Optional[str] = ""
    reason: str

    # Deep analytical attributes for UI inspector & auditing
    total_cost_inr: float
    total_tonne_km: float
    shipment_count: int
    history_baseline: Optional[float] = None
    history_weeks_used: int = 0
    vs_own_history_pct: Optional[float] = None
    peer_baseline: Optional[float] = None
    peer_routes_count: int = 0
    vs_similar_routes_pct: Optional[float] = None
    is_anomaly: bool = False
    candidates: List[RetrievedCandidate] = Field(default_factory=list)


class RouteOverviewSummary(BaseModel):
    total_route_weeks: int
    unexplained_anomalies: int
    justified_anomalies: int
    normal_route_weeks: int
    total_shipments: int
    total_freight_spend_inr: float
    total_tonne_km: float
    weighted_avg_cost_per_tonne_km: float
    route_breakdown: Dict[str, Dict[str, Any]]
    weekly_trend: List[Dict[str, Any]]
    recent_anomalies: List[Dict[str, Any]]


class ChatMessage(BaseModel):
    role: str  # 'user', 'assistant', 'system'
    content: str


class QARequest(BaseModel):
    question: str
    route: Optional[str] = None
    week_of: Optional[str] = None


class QAResponse(BaseModel):
    answer: str
    route: Optional[str] = None
    week_of: Optional[str] = None
    evidence_notes: List[str] = Field(default_factory=list)
    metrics_cited: Dict[str, Any] = Field(default_factory=dict)
    grounded_in_computation: bool = True
    provider_used: str = "local-deterministic-grounded"


class CostTrackingReport(BaseModel):
    run_id: str
    timestamp: str
    dataset_records_count: int
    total_route_weeks: int
    embedding_model: str
    notes_indexed_count: int
    queries_executed_count: int
    llm_calls_count: int
    llm_input_tokens: int
    llm_output_tokens: int
    token_accounting_method: str
    provider_currency: str
    estimated_api_cost: float
    runtime_seconds: float
    execution_mode: str
    notes: str
