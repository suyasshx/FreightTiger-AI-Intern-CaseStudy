import type { RouteOverviewSummary, RouteWeekRecord, ContextNote, QAResponse, SensitivityCurveItem } from '../types';

const API_BASE = '/api';

export const apiClient = {
  async getOverview(): Promise<RouteOverviewSummary> {
    const res = await fetch(`${API_BASE}/overview`);
    if (!res.ok) throw new Error(`Failed to fetch overview: ${res.statusText}`);
    return res.json();
  },

  async getRoutes(params: {
    route?: string;
    route_type?: string;
    flagged?: string;
    start_date?: string;
    end_date?: string;
    page?: number;
    page_size?: number;
  }): Promise<{
    total_records: number;
    page: number;
    page_size: number;
    total_pages: number;
    items: RouteWeekRecord[];
  }> {
    const query = new URLSearchParams();
    if (params.route) query.append('route', params.route);
    if (params.route_type && params.route_type !== 'All') query.append('route_type', params.route_type);
    if (params.flagged && params.flagged !== 'All') query.append('flagged', params.flagged);
    if (params.start_date) query.append('start_date', params.start_date);
    if (params.end_date) query.append('end_date', params.end_date);
    query.append('page', String(params.page || 1));
    query.append('page_size', String(params.page_size || 50));

    const res = await fetch(`${API_BASE}/routes?${query.toString()}`);
    if (!res.ok) throw new Error(`Failed to fetch routes: ${res.statusText}`);
    return res.json();
  },

  async getRouteTimeseries(routeName: string): Promise<{
    route: string;
    route_type: string;
    total_weeks: number;
    data: RouteWeekRecord[];
  }> {
    const res = await fetch(`${API_BASE}/routes/timeseries/${encodeURIComponent(routeName)}`);
    if (!res.ok) throw new Error(`Failed to fetch corridor timeseries: ${res.statusText}`);
    return res.json();
  },

  async getNotes(): Promise<ContextNote[]> {
    const res = await fetch(`${API_BASE}/notes`);
    if (!res.ok) throw new Error(`Failed to fetch notes: ${res.statusText}`);
    return res.json();
  },

  async getEvidenceDetail(route: string, week_of: string): Promise<any> {
    const res = await fetch(`${API_BASE}/evidence/${encodeURIComponent(route)}/${encodeURIComponent(week_of)}`);
    if (!res.ok) throw new Error(`Failed to fetch evidence detail: ${res.statusText}`);
    return res.json();
  },

  async getSensitivity(): Promise<SensitivityCurveItem[]> {
    const res = await fetch(`${API_BASE}/evaluation/sensitivity`);
    if (!res.ok) throw new Error(`Failed to fetch sensitivity: ${res.statusText}`);
    return res.json();
  },

  async getCostLog(): Promise<any> {
    const res = await fetch(`${API_BASE}/cost-log`);
    if (!res.ok) throw new Error(`Failed to fetch cost log: ${res.statusText}`);
    return res.json();
  },

  async sendChatMessage(question: string, route?: string, week_of?: string): Promise<QAResponse> {
    const res = await fetch(`${API_BASE}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, route, week_of })
    });
    if (!res.ok) throw new Error(`Chat assistant request failed: ${res.statusText}`);
    return res.json();
  },

  async triggerAnalysis(historyThreshold: number, peerThreshold: number): Promise<any> {
    const res = await fetch(`${API_BASE}/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        history_threshold_pct: historyThreshold,
        peer_threshold_pct: peerThreshold,
        trailing_weeks: 8
      })
    });
    if (!res.ok) throw new Error(`Analysis execution failed: ${res.statusText}`);
    return res.json();
  },

  getExportCsvUrl(): string {
    return `${API_BASE}/export/csv`;
  },

  getExportReportUrl(): string {
    return `${API_BASE}/export/report`;
  }
};
