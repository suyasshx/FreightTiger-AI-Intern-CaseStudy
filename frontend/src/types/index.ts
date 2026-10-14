export interface GateCheckDetail {
  passed: boolean;
  description: string;
}

export interface EvidenceGateResult {
  note_id: string;
  route_gate: GateCheckDetail;
  temporal_gate: GateCheckDetail;
  causal_gate: GateCheckDetail;
  negative_filter_gate: GateCheckDetail;
  magnitude_gate: GateCheckDetail;
  passed_all_gates: boolean;
  summary: string;
}

export interface RetrievedCandidate {
  note_id: string;
  date: string;
  applies_to: string;
  note_text: string;
  similarity_score: number;
  distance: number;
  gates?: EvidenceGateResult;
}

export interface RouteWeekRecord {
  route: string;
  week_of: string;
  route_type: string;
  cost_per_tonne_km: number;
  vs_own_history: string;
  vs_similar_routes: string;
  flagged: 'No' | 'No (justified)' | 'Yes';
  matched_note_id?: string;
  reason: string;
  total_cost_inr: number;
  total_tonne_km: number;
  shipment_count: number;
  history_baseline?: number;
  history_weeks_used: number;
  vs_own_history_pct?: number;
  peer_baseline?: number;
  peer_routes_count: number;
  vs_similar_routes_pct?: number;
  is_anomaly: boolean;
  candidates: RetrievedCandidate[];
}

export interface RouteOverviewSummary {
  total_route_weeks: number;
  unexplained_anomalies: number;
  justified_anomalies: number;
  normal_route_weeks: number;
  total_shipments: number;
  total_freight_spend_inr: number;
  total_tonne_km: number;
  weighted_avg_cost_per_tonne_km: number;
  route_breakdown: Record<string, {
    total_weeks: number;
    unexplained_anomalies: number;
    justified_anomalies: number;
    avg_cost: number;
    min_cost: number;
    max_cost: number;
  }>;
  weekly_trend: Array<{
    week_of: string;
    avg_cost: number;
    anomaly_count: number;
    unexplained_count: number;
    justified_count: number;
  }>;
  recent_anomalies: RouteWeekRecord[];
}

export interface ContextNote {
  note_id: string;
  date: string;
  applies_to: string;
  note: string;
}

export interface QAResponse {
  answer: string;
  route?: string;
  week_of?: string;
  evidence_notes: string[];
  metrics_cited: Record<string, any>;
  grounded_in_computation: boolean;
  provider_used: string;
}

export interface SensitivityCurveItem {
  threshold_pct: number;
  anomaly_candidate_count: number;
  history_triggered_only: number;
  peer_triggered_only: number;
  both_triggered: number;
  pct_of_total_route_weeks: number;
}
