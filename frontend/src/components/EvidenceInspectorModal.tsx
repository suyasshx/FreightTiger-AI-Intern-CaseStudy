import React, { useState, useEffect } from 'react';
import {
  X, ShieldCheck, CheckCircle2, XCircle
} from 'lucide-react';
import type { RouteWeekRecord } from '../types';
import { apiClient } from '../api/client';

interface EvidenceInspectorModalProps {
  record: RouteWeekRecord | null;
  onClose: () => void;
}

export const EvidenceInspectorModal: React.FC<EvidenceInspectorModalProps> = ({
  record,
  onClose,
}) => {
  const [loading, setLoading] = useState<boolean>(false);
  const [evidenceDetail, setEvidenceDetail] = useState<any>(null);

  useEffect(() => {
    if (record) {
      setLoading(true);
      apiClient.getEvidenceDetail(record.route, record.week_of)
        .then((data) => setEvidenceDetail(data))
        .catch((err) => console.error("Error loading evidence detail:", err))
        .finally(() => setLoading(false));
    } else {
      setEvidenceDetail(null);
    }
  }, [record]);

  if (!record) return null;

  const candidates = evidenceDetail?.candidates_evaluated || record.candidates || [];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md overflow-y-auto">
      <div className="relative w-full max-w-4xl max-h-[90vh] flex flex-col rounded-2xl border border-slate-700 bg-slate-900 shadow-2xl overflow-hidden">
        {/* Modal Header */}
        <div className="p-6 border-b border-slate-800 bg-slate-950/90 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-sky-500/10 border border-sky-500/30 flex items-center justify-center">
              <ShieldCheck className="w-5 h-5 text-sky-400" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h2 className="text-lg font-bold text-white tracking-tight">Evidence Gate Audit</h2>
                <span
                  className={`px-2.5 py-0.5 rounded-full text-xs font-bold ${
                    record.flagged === 'No (justified)'
                      ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40'
                      : record.flagged === 'Yes'
                      ? 'bg-rose-500/20 text-rose-400 border border-rose-500/40'
                      : 'bg-slate-800 text-slate-300'
                  }`}
                >
                  Verdict: {record.flagged}
                </span>
              </div>
              <p className="text-xs text-slate-400">
                Corridor: <span className="text-slate-200 font-semibold">{record.route}</span> | Week:{' '}
                <span className="font-mono text-slate-200">{record.week_of}</span>
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-400 hover:text-white transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 overflow-y-auto space-y-6">
          {/* Corridor Anomaly Overview */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 p-4 rounded-xl bg-slate-950/60 border border-slate-800 text-xs">
            <div>
              <span className="text-slate-400 block mb-0.5">Observed Rate:</span>
              <span className="text-base font-bold text-sky-400">₹{record.cost_per_tonne_km.toFixed(2)} / t-km</span>
            </div>
            <div>
              <span className="text-slate-400 block mb-0.5">vs 8-Wk History:</span>
              <span className="text-sm font-semibold text-white">{record.vs_own_history}</span>
            </div>
            <div>
              <span className="text-slate-400 block mb-0.5">vs Peer Hauls:</span>
              <span className="text-sm font-semibold text-white">{record.vs_similar_routes}</span>
            </div>
            <div>
              <span className="text-slate-400 block mb-0.5">Matched Note ID:</span>
              <span className="font-mono font-bold text-indigo-400">
                {record.matched_note_id || 'None (Unexplained)'}
              </span>
            </div>
          </div>

          {/* Official Reason */}
          <div className="p-4 rounded-xl bg-slate-800/40 border border-slate-700/60 space-y-1">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">
              Plain-English Verdict Reason
            </span>
            <p className="text-xs text-slate-200 leading-relaxed italic">"{record.reason}"</p>
          </div>

          {/* Candidate Notes & 6-Gate Audit */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-white">Contextual Notes Evaluated by RAG Engine</h3>
                <p className="text-xs text-slate-400">
                  Vector retrieval candidates verified against the 6 non-negotiable evidence gates.
                </p>
              </div>
              <span className="text-xs text-slate-500 font-mono">
                {candidates.length} candidate(s) evaluated
              </span>
            </div>

            {loading ? (
              <div className="py-8 text-center text-slate-400 text-xs">
                <div className="w-6 h-6 border-2 border-sky-400 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
                Loading candidate evidence audit...
              </div>
            ) : candidates.length === 0 ? (
              <div className="p-6 text-center text-slate-500 text-xs border border-dashed border-slate-800 rounded-xl">
                No contextual notes met the vector similarity threshold for this corridor and date range.
                The anomaly was classified as unexplained.
              </div>
            ) : (
              candidates.map((cand: any, idx: number) => {
                const gates = cand.gates;
                const passedAll = gates?.passed_all_gates;

                return (
                  <div
                    key={idx}
                    className={`rounded-xl border p-4 space-y-3 transition ${
                      passedAll
                        ? 'border-emerald-500/40 bg-emerald-950/15 glow-emerald'
                        : 'border-slate-800 bg-slate-950/60'
                    }`}
                  >
                    {/* Note Header */}
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                      <div className="flex items-center space-x-2">
                        <span className="px-2 py-0.5 rounded font-mono font-bold text-xs bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                          {cand.note_id}
                        </span>
                        <span className="text-xs text-slate-300 font-semibold">
                          Applies to: {cand.applies_to}
                        </span>
                        <span className="text-xs text-slate-400 font-mono">({cand.date})</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span className="text-[11px] text-slate-400 font-mono">
                          Cosine Sim: {(cand.similarity_score * 100).toFixed(1)}%
                        </span>
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                            passedAll
                              ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40'
                              : 'bg-rose-500/20 text-rose-400 border border-rose-500/40'
                          }`}
                        >
                          {passedAll ? 'Verified Justification' : 'Gate Rejected'}
                        </span>
                      </div>
                    </div>

                    {/* Original Note Text */}
                    <p className="text-xs text-slate-200 bg-slate-900/80 p-3 rounded-lg border border-slate-800/80 leading-relaxed font-sans">
                      "{cand.note_text || cand.note}"
                    </p>

                    {/* 6 Hard Evidence Gates Breakdown */}
                    {gates && (
                      <div className="space-y-1.5 pt-1">
                        <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                          Hard Evidence Gates Evaluation
                        </span>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-[11px]">
                          {/* Gate 1: Route */}
                          <div
                            className={`p-2 rounded-lg border flex items-start space-x-2 ${
                              gates.route_gate.passed
                                ? 'bg-emerald-950/20 border-emerald-500/30 text-emerald-300'
                                : 'bg-rose-950/20 border-rose-500/30 text-rose-300'
                            }`}
                          >
                            {gates.route_gate.passed ? (
                              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0 mt-0.5" />
                            ) : (
                              <XCircle className="w-3.5 h-3.5 text-rose-400 flex-shrink-0 mt-0.5" />
                            )}
                            <div>
                              <span className="font-bold">1. Route Scope: </span>
                              <span>{gates.route_gate.description}</span>
                            </div>
                          </div>

                          {/* Gate 2: Temporal */}
                          <div
                            className={`p-2 rounded-lg border flex items-start space-x-2 ${
                              gates.temporal_gate.passed
                                ? 'bg-emerald-950/20 border-emerald-500/30 text-emerald-300'
                                : 'bg-rose-950/20 border-rose-500/30 text-rose-300'
                            }`}
                          >
                            {gates.temporal_gate.passed ? (
                              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0 mt-0.5" />
                            ) : (
                              <XCircle className="w-3.5 h-3.5 text-rose-400 flex-shrink-0 mt-0.5" />
                            )}
                            <div>
                              <span className="font-bold">2. Temporal Window: </span>
                              <span>{gates.temporal_gate.description}</span>
                            </div>
                          </div>

                          {/* Gate 3: Causal */}
                          <div
                            className={`p-2 rounded-lg border flex items-start space-x-2 ${
                              gates.causal_gate.passed
                                ? 'bg-emerald-950/20 border-emerald-500/30 text-emerald-300'
                                : 'bg-rose-950/20 border-rose-500/30 text-rose-300'
                            }`}
                          >
                            {gates.causal_gate.passed ? (
                              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0 mt-0.5" />
                            ) : (
                              <XCircle className="w-3.5 h-3.5 text-rose-400 flex-shrink-0 mt-0.5" />
                            )}
                            <div>
                              <span className="font-bold">3. Causal Mechanism: </span>
                              <span>{gates.causal_gate.description}</span>
                            </div>
                          </div>

                          {/* Gate 4: Negative Filter */}
                          <div
                            className={`p-2 rounded-lg border flex items-start space-x-2 ${
                              gates.negative_filter_gate.passed
                                ? 'bg-emerald-950/20 border-emerald-500/30 text-emerald-300'
                                : 'bg-rose-950/20 border-rose-500/30 text-rose-300'
                            }`}
                          >
                            {gates.negative_filter_gate.passed ? (
                              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0 mt-0.5" />
                            ) : (
                              <XCircle className="w-3.5 h-3.5 text-rose-400 flex-shrink-0 mt-0.5" />
                            )}
                            <div>
                              <span className="font-bold">4. Negative Filter: </span>
                              <span>{gates.negative_filter_gate.description}</span>
                            </div>
                          </div>

                          {/* Gate 5: Magnitude */}
                          <div
                            className={`p-2 rounded-lg border flex items-start space-x-2 md:col-span-2 ${
                              gates.magnitude_gate.passed
                                ? 'bg-emerald-950/20 border-emerald-500/30 text-emerald-300'
                                : 'bg-rose-950/20 border-rose-500/30 text-rose-300'
                            }`}
                          >
                            {gates.magnitude_gate.passed ? (
                              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0 mt-0.5" />
                            ) : (
                              <XCircle className="w-3.5 h-3.5 text-rose-400 flex-shrink-0 mt-0.5" />
                            )}
                            <div>
                              <span className="font-bold">5. Magnitude Consistency: </span>
                              <span>{gates.magnitude_gate.description}</span>
                            </div>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Modal Footer */}
        <div className="p-4 border-t border-slate-800 bg-slate-950 flex items-center justify-between text-xs text-slate-400">
          <span>RouteGuard AI Evidence Verification Engine</span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-medium transition"
          >
            Close Audit
          </button>
        </div>
      </div>
    </div>
  );
};
