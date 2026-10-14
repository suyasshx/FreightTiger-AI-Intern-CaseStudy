import React, { useState } from 'react';
import {
  Download, FileSpreadsheet, FileText, Settings, Play,
  CheckCircle, RefreshCw
} from 'lucide-react';
import { apiClient } from '../api/client';

interface ExportCenterProps {
  onRefreshData: () => void;
}

export const ExportCenter: React.FC<ExportCenterProps> = ({ onRefreshData }) => {
  const [historyThreshold, setHistoryThreshold] = useState<number>(15.0);
  const [peerThreshold, setPeerThreshold] = useState<number>(15.0);
  const [running, setRunning] = useState<boolean>(false);
  const [runResult, setRunResult] = useState<any>(null);

  const handleSimulate = async () => {
    setRunning(true);
    setRunResult(null);
    try {
      const res = await apiClient.triggerAnalysis(historyThreshold, peerThreshold);
      setRunResult(res);
      onRefreshData();
    } catch (err: any) {
      alert(`Pipeline execution error: ${err.message}`);
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div className="p-5 rounded-2xl border border-slate-800 bg-slate-900/60 backdrop-blur-sm">
        <h1 className="text-xl font-bold text-white tracking-tight">Submission Artifacts & Export Center</h1>
        <p className="text-xs text-slate-400 mt-1">
          Download the official graded CSV deliverables, cryptographic run reports, and simulate alternative anomaly thresholds.
        </p>
      </div>

      {/* Artifact Downloads Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Card 1: Official Output CSV */}
        <div className="p-5 rounded-2xl border border-sky-500/30 bg-slate-900/80 relative overflow-hidden space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2.5">
              <div className="p-2 rounded-xl bg-sky-500/10 text-sky-400">
                <FileSpreadsheet className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-white">Grading Contract Output CSV</h3>
                <span className="text-[11px] font-mono text-slate-400">outputs/flagged_routes.csv</span>
              </div>
            </div>
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-sky-500/10 text-sky-400 border border-sky-500/30">
              Contract Deliverable
            </span>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">
            Exact 8-column format required by the case study: <br />
            <code className="text-[10px] bg-slate-950 px-1.5 py-0.5 rounded text-sky-300 border border-slate-800">
              route,week_of,cost_per_tonne_km,vs_own_history,vs_similar_routes,flagged,matched_note_id,reason
            </code>
          </p>
          <div className="pt-2">
            <a
              href={apiClient.getExportCsvUrl()}
              download="flagged_routes.csv"
              className="w-full py-2.5 rounded-xl bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold flex items-center justify-center space-x-2 transition shadow-lg shadow-sky-600/20"
            >
              <Download className="w-4 h-4" />
              <span>Download Official Graded CSV</span>
            </a>
          </div>
        </div>

        {/* Card 2: Markdown Audit Report */}
        <div className="p-5 rounded-2xl border border-slate-800 bg-slate-900/80 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2.5">
              <div className="p-2 rounded-xl bg-indigo-500/10 text-indigo-400">
                <FileText className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-white">Logistics Executive Audit Report</h3>
                <span className="text-[11px] font-mono text-slate-400">audit_report.md</span>
              </div>
            </div>
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-500/10 text-indigo-400 border border-indigo-500/30">
              Markdown Report
            </span>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">
            Structured executive summary containing corridor performance matrices, justified anomaly evidence citations,
            and unexplained spikes for investigation.
          </p>
          <div className="pt-2">
            <a
              href={apiClient.getExportReportUrl()}
              download="RouteGuard_Audit_Report.md"
              className="w-full py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold flex items-center justify-center space-x-2 border border-slate-700 transition"
            >
              <Download className="w-4 h-4" />
              <span>Download Markdown Audit Report</span>
            </a>
          </div>
        </div>
      </div>

      {/* Threshold Tuning & Simulation Console */}
      <div className="p-6 rounded-2xl border border-slate-800 bg-slate-900/60 backdrop-blur-sm space-y-5">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2.5">
            <div className="p-2 rounded-xl bg-amber-500/10 text-amber-400">
              <Settings className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-white">Threshold Tuning & Pipeline Simulator</h2>
              <p className="text-xs text-slate-400">
                Adjust anomaly trigger percentages to re-run the pipeline and observe sensitivity in real time.
              </p>
            </div>
          </div>
          <span className="text-xs text-slate-500 font-mono">Real Backend Execution</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2">
          {/* History Threshold Slider */}
          <div className="space-y-2 p-4 rounded-xl bg-slate-950/60 border border-slate-800">
            <div className="flex justify-between items-center text-xs">
              <span className="font-semibold text-slate-300">Own History Threshold</span>
              <span className="font-bold text-sky-400 font-mono">+{historyThreshold.toFixed(1)}%</span>
            </div>
            <input
              type="range"
              min="5"
              max="35"
              step="1"
              value={historyThreshold}
              onChange={(e) => setHistoryThreshold(parseFloat(e.target.value))}
              className="w-full accent-sky-400 cursor-pointer"
            />
            <p className="text-[11px] text-slate-500">
              Triggers candidate if current cost exceeds trailing 8-week baseline by this percentage.
            </p>
          </div>

          {/* Peer Threshold Slider */}
          <div className="space-y-2 p-4 rounded-xl bg-slate-950/60 border border-slate-800">
            <div className="flex justify-between items-center text-xs">
              <span className="font-semibold text-slate-300">Peer Route Threshold</span>
              <span className="font-bold text-amber-400 font-mono">+{peerThreshold.toFixed(1)}%</span>
            </div>
            <input
              type="range"
              min="5"
              max="35"
              step="1"
              value={peerThreshold}
              onChange={(e) => setPeerThreshold(parseFloat(e.target.value))}
              className="w-full accent-amber-400 cursor-pointer"
            />
            <p className="text-[11px] text-slate-500">
              Triggers candidate if current cost exceeds same-week same-haul peer average by this percentage.
            </p>
          </div>
        </div>

        <div className="flex items-center justify-between pt-2">
          <button
            onClick={() => {
              setHistoryThreshold(15.0);
              setPeerThreshold(15.0);
            }}
            className="text-xs text-slate-400 hover:text-white transition"
          >
            Reset to Default (+15.0%)
          </button>

          <button
            onClick={handleSimulate}
            disabled={running}
            className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-sky-600 to-indigo-600 hover:from-sky-500 hover:to-indigo-500 text-white text-xs font-bold flex items-center space-x-2 transition shadow-lg shadow-sky-600/25 disabled:opacity-50"
          >
            {running ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                <span>Re-running Pipeline...</span>
              </>
            ) : (
              <>
                <Play className="w-4 h-4" />
                <span>Re-run Pipeline with Custom Thresholds</span>
              </>
            )}
          </button>
        </div>

        {/* Execution Result Banner */}
        {runResult && (
          <div className="p-4 rounded-xl bg-emerald-950/20 border border-emerald-500/40 text-xs space-y-2">
            <div className="flex items-center justify-between font-bold text-emerald-400">
              <div className="flex items-center space-x-2">
                <CheckCircle className="w-4 h-4" />
                <span>Pipeline Executed Successfully in {runResult.runtime_seconds}s</span>
              </div>
              <span className="font-mono text-[11px]">SHA-256: {runResult.sha256.substring(0, 16)}...</span>
            </div>
            <div className="grid grid-cols-3 gap-2 pt-1 font-mono text-[11px]">
              <div className="p-2 rounded bg-slate-900 border border-slate-800 text-slate-300">
                Normal Weeks: <span className="text-white font-bold">{runResult.normal_route_weeks}</span>
              </div>
              <div className="p-2 rounded bg-slate-900 border border-slate-800 text-slate-300">
                Unexplained: <span className="text-rose-400 font-bold">{runResult.unexplained_anomalies}</span>
              </div>
              <div className="p-2 rounded bg-slate-900 border border-slate-800 text-slate-300">
                Justified: <span className="text-emerald-400 font-bold">{runResult.justified_anomalies}</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
