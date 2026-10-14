import React from 'react';
import {
  TrendingUp, AlertTriangle, CheckCircle, ShieldCheck,
  DollarSign, Truck, ArrowUpRight, ChevronRight, Zap
} from 'lucide-react';
import {
  ResponsiveContainer, LineChart, Line, XAxis, YAxis,
  Tooltip, CartesianGrid
} from 'recharts';
import type { RouteOverviewSummary, RouteWeekRecord } from '../types';

interface OperationsOverviewProps {
  overview: RouteOverviewSummary | null;
  onSelectRoute: (routeName: string) => void;
  onOpenEvidence: (record: RouteWeekRecord) => void;
}

export const OperationsOverview: React.FC<OperationsOverviewProps> = ({
  overview,
  onSelectRoute,
  onOpenEvidence,
}) => {
  if (!overview) {
    return (
      <div className="flex items-center justify-center min-h-[500px]">
        <div className="text-center space-y-3">
          <div className="w-10 h-10 border-2 border-sky-400 border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-sm text-slate-400">Loading freight intelligence metrics...</p>
        </div>
      </div>
    );
  }

  // Format INR currency readable
  const formatINR = (val: number) => {
    if (val >= 10000000) return `₹${(val / 10000000).toFixed(2)} Cr`;
    if (val >= 100000) return `₹${(val / 100000).toFixed(2)} Lakh`;
    return `₹${val.toLocaleString()}`;
  };

  const kpis = [
    {
      label: 'Route-Weeks Analyzed',
      value: overview.total_route_weeks.toLocaleString(),
      sub: `${overview.total_shipments.toLocaleString()} total shipments`,
      icon: Truck,
      color: 'text-sky-400',
      bg: 'bg-sky-500/10',
      border: 'border-sky-500/20',
    },
    {
      label: 'Unexplained Anomalies',
      value: overview.unexplained_anomalies,
      sub: 'Actionable review required',
      icon: AlertTriangle,
      color: 'text-rose-400',
      bg: 'bg-rose-500/10',
      border: 'border-rose-500/30 glow-rose',
      highlight: true,
    },
    {
      label: 'Evidence-Supported (Justified)',
      value: overview.justified_anomalies,
      sub: 'Grounded by contextual notes',
      icon: CheckCircle,
      color: 'text-emerald-400',
      bg: 'bg-emerald-500/10',
      border: 'border-emerald-500/30 glow-emerald',
    },
    {
      label: 'Normal Route-Weeks',
      value: overview.normal_route_weeks.toLocaleString(),
      sub: `${((overview.normal_route_weeks / overview.total_route_weeks) * 100).toFixed(1)}% network compliance`,
      icon: ShieldCheck,
      color: 'text-slate-300',
      bg: 'bg-slate-800/50',
      border: 'border-slate-700/50',
    },
    {
      label: 'Network Freight Spend',
      value: formatINR(overview.total_freight_spend_inr),
      sub: `${(overview.total_tonne_km / 1000000).toFixed(2)}M tonne-km carried`,
      icon: DollarSign,
      color: 'text-amber-400',
      bg: 'bg-amber-500/10',
      border: 'border-amber-500/20',
    },
    {
      label: 'Weighted Net Cost',
      value: `₹${overview.weighted_avg_cost_per_tonne_km.toFixed(2)}`,
      sub: 'per tonne-kilometre network-wide',
      icon: TrendingUp,
      color: 'text-indigo-400',
      bg: 'bg-indigo-500/10',
      border: 'border-indigo-500/20',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-slate-900 via-slate-900/90 to-sky-950/40 border border-slate-800 p-6 shadow-xl">
        <div className="absolute right-0 top-0 bottom-0 w-96 bg-gradient-to-l from-sky-500/10 to-transparent pointer-events-none" />
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 relative z-10">
          <div>
            <div className="inline-flex items-center space-x-2 px-2.5 py-1 rounded-full bg-sky-500/10 border border-sky-500/30 text-sky-400 text-xs font-semibold mb-2">
              <Zap className="w-3.5 h-3.5" />
              <span>Operational Intelligence Active</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
              Network Freight Transportation Control Tower
            </h1>
            <p className="text-sm text-slate-400 max-w-2xl mt-1">
              Tracking weekly cost per tonne-kilometre across commercial logistics corridors,
              flagging cost spikes against trailing 8-week history and same-week haul peers, and verifying
              real-world justifications using deterministic 6-gate RAG evidence retrieval.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => onSelectRoute('Ahmedabad-Mumbai')}
              className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm font-medium border border-slate-700 transition flex items-center space-x-2"
            >
              <span>Inspect Festival Surcharge (N002)</span>
              <ArrowUpRight className="w-4 h-4 text-slate-400" />
            </button>
            <button
              onClick={() => onSelectRoute('Chennai-Bangalore')}
              className="px-4 py-2 rounded-xl bg-sky-600 hover:bg-sky-500 text-white text-sm font-medium transition shadow-lg shadow-sky-600/25 flex items-center space-x-2"
            >
              <span>Inspect Flood Detour (N001)</span>
              <ArrowUpRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {kpis.map((kpi, idx) => {
          const Icon = kpi.icon;
          return (
            <div
              key={idx}
              className={`p-4 rounded-xl border ${kpi.border} bg-slate-900/60 backdrop-blur-sm relative transition hover:border-slate-600`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-medium text-slate-400">{kpi.label}</span>
                <div className={`p-1.5 rounded-lg ${kpi.bg}`}>
                  <Icon className={`w-4 h-4 ${kpi.color}`} />
                </div>
              </div>
              <div className="text-2xl font-bold text-white tracking-tight">{kpi.value}</div>
              <div className="text-[11px] text-slate-400 mt-1 truncate">{kpi.sub}</div>
            </div>
          );
        })}
      </div>

      {/* Main Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Weekly Trend Line Chart */}
        <div className="lg:col-span-2 p-5 rounded-2xl border border-slate-800 bg-slate-900/60 backdrop-blur-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-base font-bold text-white">Network Weekly Cost per Tonne-Km Trend</h2>
              <p className="text-xs text-slate-400">Weekly weighted average across 7 commercial corridors (2024–2025)</p>
            </div>
            <div className="flex items-center space-x-3 text-xs">
              <span className="flex items-center text-slate-300">
                <span className="w-2.5 h-2.5 rounded-full bg-sky-400 mr-1.5" />
                Avg Cost (INR/t-km)
              </span>
              <span className="flex items-center text-rose-400">
                <span className="w-2.5 h-2.5 rounded-full bg-rose-500 mr-1.5" />
                Anomalies
              </span>
            </div>
          </div>
          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={overview.weekly_trend} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                <XAxis
                  dataKey="week_of"
                  tick={{ fill: '#64748b', fontSize: 11 }}
                  tickFormatter={(val) => {
                    const d = new Date(val);
                    return d.toLocaleDateString(undefined, { month: 'short', year: '2-digit' });
                  }}
                  interval={12}
                  stroke="#334155"
                />
                <YAxis
                  tick={{ fill: '#64748b', fontSize: 11 }}
                  domain={['auto', 'auto']}
                  tickFormatter={(val) => `₹${val.toFixed(1)}`}
                  stroke="#334155"
                />
                <Tooltip
                  content={({ active, payload, label }) => {
                    if (active && payload && payload.length) {
                      const data = payload[0].payload;
                      return (
                        <div className="bg-slate-900 border border-slate-700 rounded-xl p-3 shadow-xl text-xs space-y-1">
                          <p className="font-semibold text-white">Week of {label}</p>
                          <p className="text-sky-400">Cost: ₹{Number(data.avg_cost).toFixed(2)} / t-km</p>
                          <p className="text-rose-400">Unexplained Spikes: {data.unexplained_count}</p>
                          <p className="text-emerald-400">Justified Events: {data.justified_count}</p>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="avg_cost"
                  stroke="#38bdf8"
                  strokeWidth={2.5}
                  dot={false}
                  activeDot={{ r: 5, fill: '#38bdf8' }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Anomaly Volume Stacked Bar Chart */}
        <div className="p-5 rounded-2xl border border-slate-800 bg-slate-900/60 backdrop-blur-sm flex flex-col justify-between">
          <div>
            <h2 className="text-base font-bold text-white mb-1">Anomaly Verification Ratio</h2>
            <p className="text-xs text-slate-400 mb-4">Justified vs Unexplained Candidates</p>
            <div className="space-y-4 pt-2">
              <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-2">
                <div className="flex justify-between text-xs">
                  <span className="text-rose-400 font-semibold">Unexplained Spikes (Review Required)</span>
                  <span className="text-white font-bold">{overview.unexplained_anomalies}</span>
                </div>
                <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                  <div
                    className="bg-rose-500 h-full rounded-full transition-all"
                    style={{
                      width: `${(overview.unexplained_anomalies / (overview.unexplained_anomalies + overview.justified_anomalies || 1)) * 100}%`,
                    }}
                  />
                </div>
                <p className="text-[11px] text-slate-400">
                  Failed route applicability, time windows, or lacked genuine increase mechanism.
                </p>
              </div>

              <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-2">
                <div className="flex justify-between text-xs">
                  <span className="text-emerald-400 font-semibold">Evidence-Grounded (Justified)</span>
                  <span className="text-white font-bold">{overview.justified_anomalies}</span>
                </div>
                <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                  <div
                    className="bg-emerald-500 h-full rounded-full transition-all"
                    style={{
                      width: `${(overview.justified_anomalies / (overview.unexplained_anomalies + overview.justified_anomalies || 1)) * 100}%`,
                    }}
                  />
                </div>
                <p className="text-[11px] text-slate-400">
                  Verified by N001 (flooding detours) and N002 (festival demand surcharge).
                </p>
              </div>
            </div>
          </div>

          <div className="p-3 rounded-xl bg-sky-500/10 border border-sky-500/20 text-xs text-sky-300 mt-4">
            <span className="font-bold">Zero-Hallucination Policy:</span> No LLM can override the 6 evidence gates.
            Verdicts are mathematically and chronologically bound to contextual notes.
          </div>
        </div>
      </div>

      {/* Corridor Breakdown Table */}
      <div className="p-5 rounded-2xl border border-slate-800 bg-slate-900/60 backdrop-blur-sm">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-base font-bold text-white">Commercial Transportation Corridors</h2>
            <p className="text-xs text-slate-400">Aggregated performance, baseline stability, and anomaly frequency</p>
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/80 text-slate-400 uppercase tracking-wider border-b border-slate-800">
              <tr>
                <th className="py-3 px-4 font-semibold">Corridor</th>
                <th className="py-3 px-4 font-semibold">Weeks</th>
                <th className="py-3 px-4 font-semibold">Avg Cost (INR/t-km)</th>
                <th className="py-3 px-4 font-semibold">Cost Range</th>
                <th className="py-3 px-4 font-semibold">Unexplained</th>
                <th className="py-3 px-4 font-semibold">Justified</th>
                <th className="py-3 px-4 font-semibold text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {Object.entries(overview.route_breakdown).map(([rName, stats]) => {
                return (
                  <tr key={rName} className="hover:bg-slate-800/40 transition">
                    <td className="py-3 px-4 font-bold text-white flex items-center space-x-2">
                      <span>{rName}</span>
                    </td>
                    <td className="py-3 px-4 text-slate-300">{stats.total_weeks} wks</td>
                    <td className="py-3 px-4 text-sky-400 font-medium">₹{stats.avg_cost.toFixed(2)}</td>
                    <td className="py-3 px-4 text-slate-400 font-mono">
                      ₹{stats.min_cost.toFixed(2)} – ₹{stats.max_cost.toFixed(2)}
                    </td>
                    <td className="py-3 px-4">
                      {stats.unexplained_anomalies > 0 ? (
                        <span className="px-2 py-0.5 rounded-full text-[11px] font-bold bg-rose-500/15 text-rose-400 border border-rose-500/30">
                          {stats.unexplained_anomalies} review needed
                        </span>
                      ) : (
                        <span className="text-slate-500 text-[11px]">0</span>
                      )}
                    </td>
                    <td className="py-3 px-4">
                      {stats.justified_anomalies > 0 ? (
                        <span className="px-2 py-0.5 rounded-full text-[11px] font-bold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
                          {stats.justified_anomalies} supported
                        </span>
                      ) : (
                        <span className="text-slate-500 text-[11px]">0</span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={() => onSelectRoute(rName)}
                        className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium border border-slate-700 transition"
                      >
                        Explore Timeseries
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Notable Anomalies Feed */}
      <div className="p-5 rounded-2xl border border-slate-800 bg-slate-900/60 backdrop-blur-sm">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-base font-bold text-white">Representative Ground Truth Benchmark Cases</h2>
            <p className="text-xs text-slate-400">Exact cases validated against sample_output_format_v2.csv</p>
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {overview.recent_anomalies
            .filter((a) =>
              (a.route === 'Delhi-Jaipur' && a.week_of === '2024-11-11') ||
              (a.route === 'Ahmedabad-Mumbai' && a.week_of === '2025-01-20') ||
              (a.route === 'Mumbai-Pune' && a.week_of === '2025-09-15')
            )
            .map((rec, i) => (
              <div
                key={i}
                className="p-4 rounded-xl border border-slate-800 bg-slate-950/60 hover:border-slate-700 transition space-y-2.5"
              >
                <div className="flex items-center justify-between">
                  <span className="font-bold text-white text-sm">{rec.route}</span>
                  <span
                    className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase ${
                      rec.flagged === 'No (justified)'
                        ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                        : 'bg-rose-500/15 text-rose-400 border border-rose-500/30'
                    }`}
                  >
                    {rec.flagged}
                  </span>
                </div>
                <div className="text-xs text-slate-400 font-mono">Week: {rec.week_of}</div>
                <div className="flex items-baseline space-x-2">
                  <span className="text-lg font-extrabold text-white">₹{rec.cost_per_tonne_km.toFixed(2)}</span>
                  <span className="text-xs text-slate-400">/ t-km</span>
                </div>
                <div className="text-[11px] space-y-1 bg-slate-900/80 p-2 rounded-lg border border-slate-800/80">
                  <div className="text-slate-300 font-medium">History: {rec.vs_own_history}</div>
                  <div className="text-slate-300 font-medium">Peers: {rec.vs_similar_routes}</div>
                </div>
                <p className="text-xs text-slate-300 line-clamp-3 italic">"{rec.reason}"</p>
                <button
                  onClick={() => onOpenEvidence(rec)}
                  className="w-full mt-2 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-sky-400 text-xs font-semibold flex items-center justify-center space-x-1 transition"
                >
                  <span>Inspect 6 Evidence Gates</span>
                  <ChevronRight className="w-3.5 h-3.5" />
                </button>
              </div>
            ))}
        </div>
      </div>
    </div>
  );
};
