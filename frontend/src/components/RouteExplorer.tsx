import React, { useState, useEffect } from 'react';
import {
  Search, ChevronLeft, ChevronRight, Eye,
  AlertTriangle, CheckCircle
} from 'lucide-react';
import {
  ResponsiveContainer, LineChart, Line, XAxis, YAxis,
  Tooltip, CartesianGrid
} from 'recharts';
import type { RouteWeekRecord } from '../types';
import { apiClient } from '../api/client';

interface RouteExplorerProps {
  initialRoute?: string;
  onOpenEvidence: (record: RouteWeekRecord) => void;
}

export const RouteExplorer: React.FC<RouteExplorerProps> = ({
  initialRoute,
  onOpenEvidence,
}) => {
  const [selectedRoute, setSelectedRoute] = useState<string>(initialRoute || 'All');
  const [selectedType, setSelectedType] = useState<string>('All');
  const [selectedVerdict, setSelectedVerdict] = useState<string>('All');
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [page, setPage] = useState<number>(1);
  const [pageSize] = useState<number>(25);

  const [records, setRecords] = useState<RouteWeekRecord[]>([]);
  const [totalRecords, setTotalRecords] = useState<number>(0);
  const [totalPages, setTotalPages] = useState<number>(1);
  const [loading, setLoading] = useState<boolean>(false);

  // Timeseries state for selected corridor
  const [timeseriesData, setTimeseriesData] = useState<RouteWeekRecord[]>([]);

  const availableRoutes = [
    'Ahmedabad-Mumbai',
    'Chennai-Bangalore',
    'Delhi-Chennai',
    'Delhi-Jaipur',
    'Kolkata-Bhubaneswar',
    'Mumbai-Delhi',
    'Mumbai-Pune'
  ];

  // Fetch paginated routes
  useEffect(() => {
    let isMounted = true;
    setLoading(true);

    const routeFilter = selectedRoute !== 'All' ? selectedRoute : searchTerm;

    apiClient.getRoutes({
      route: routeFilter || undefined,
      route_type: selectedType !== 'All' ? selectedType : undefined,
      flagged: selectedVerdict !== 'All' ? selectedVerdict : undefined,
      page,
      page_size: pageSize
    })
      .then((res) => {
        if (isMounted) {
          setRecords(res.items);
          setTotalRecords(res.total_records);
          setTotalPages(res.total_pages);
        }
      })
      .catch((err) => console.error("Error fetching routes:", err))
      .finally(() => {
        if (isMounted) setLoading(false);
      });

    return () => { isMounted = false; };
  }, [selectedRoute, selectedType, selectedVerdict, searchTerm, page, pageSize]);

  // Fetch timeseries when a specific corridor is chosen
  useEffect(() => {
    if (selectedRoute && selectedRoute !== 'All') {
      apiClient.getRouteTimeseries(selectedRoute)
        .then((res) => setTimeseriesData(res.data))
        .catch((err) => console.error("Error fetching timeseries:", err));
    } else {
      setTimeseriesData([]);
    }
  }, [selectedRoute]);

  const handleRouteSelect = (r: string) => {
    setSelectedRoute(r);
    setPage(1);
  };

  return (
    <div className="space-y-6">
      {/* Header & Controls Bar */}
      <div className="p-5 rounded-2xl border border-slate-800 bg-slate-900/60 backdrop-blur-sm space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-xl font-bold text-white tracking-tight">Corridor Anomaly Explorer</h1>
            <p className="text-xs text-slate-400">
              Query, filter, and inspect weekly costs, trailing 8-week baselines, and peer comparisons.
            </p>
          </div>
          <div className="flex items-center space-x-2">
            <span className="text-xs text-slate-400 font-medium">Corridor Preset:</span>
            <select
              value={selectedRoute}
              onChange={(e) => handleRouteSelect(e.target.value)}
              className="px-3 py-1.5 rounded-xl bg-slate-950 border border-slate-700 text-slate-200 text-xs font-semibold focus:outline-none focus:border-sky-500"
            >
              <option value="All">All Corridors (Network)</option>
              {availableRoutes.map((r) => (
                <option key={r} value={r}>{r}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Filter Pills */}
        <div className="flex flex-wrap items-center gap-3 pt-2 border-t border-slate-800/80">
          {/* Haul Type Filter */}
          <div className="flex items-center space-x-1.5">
            <span className="text-xs text-slate-500">Haul:</span>
            {['All', 'Short', 'Medium', 'Long'].map((type) => (
              <button
                key={type}
                onClick={() => { setSelectedType(type); setPage(1); }}
                className={`px-2.5 py-1 rounded-lg text-xs font-medium transition ${
                  selectedType === type
                    ? 'bg-sky-500/20 text-sky-400 border border-sky-500/40'
                    : 'bg-slate-950 text-slate-400 border border-slate-800 hover:text-slate-200'
                }`}
              >
                {type}
              </button>
            ))}
          </div>

          <div className="h-4 w-px bg-slate-800 mx-1 hidden sm:block" />

          {/* Verdict Filter */}
          <div className="flex items-center space-x-1.5">
            <span className="text-xs text-slate-500">Verdict:</span>
            {[
              { id: 'All', label: 'All' },
              { id: 'Yes', label: 'Unexplained (Yes)', color: 'rose' },
              { id: 'No (justified)', label: 'Justified', color: 'emerald' },
              { id: 'No', label: 'Normal (No)', color: 'slate' }
            ].map((v) => (
              <button
                key={v.id}
                onClick={() => { setSelectedVerdict(v.id); setPage(1); }}
                className={`px-2.5 py-1 rounded-lg text-xs font-medium transition ${
                  selectedVerdict === v.id
                    ? 'bg-sky-500/20 text-sky-400 border border-sky-500/40'
                    : 'bg-slate-950 text-slate-400 border border-slate-800 hover:text-slate-200'
                }`}
              >
                {v.label}
              </button>
            ))}
          </div>

          <div className="h-4 w-px bg-slate-800 mx-1 hidden sm:block" />

          {/* Search Box */}
          <div className="relative flex-1 min-w-[200px]">
            <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-slate-500" />
            <input
              type="text"
              placeholder="Search origin, destination, or note ID..."
              value={searchTerm}
              onChange={(e) => { setSearchTerm(e.target.value); setPage(1); }}
              className="w-full pl-8 pr-3 py-1.5 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-sky-500"
            />
          </div>
        </div>
      </div>

      {/* Corridor Timeseries Chart (Shown when single corridor is selected) */}
      {selectedRoute !== 'All' && timeseriesData.length > 0 && (
        <div className="p-5 rounded-2xl border border-slate-800 bg-slate-900/60 backdrop-blur-sm space-y-3">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div>
              <div className="flex items-center space-x-2">
                <h2 className="text-base font-bold text-white">{selectedRoute}</h2>
                <span className="px-2 py-0.5 rounded-md text-[10px] font-semibold bg-slate-800 text-slate-300 border border-slate-700">
                  {timeseriesData[0]?.route_type} Haul
                </span>
              </div>
              <p className="text-xs text-slate-400">
                Weekly actual cost per tonne-km vs trailing 8-week history baseline and peer route-type average.
              </p>
            </div>
            <div className="flex items-center space-x-4 text-xs">
              <span className="flex items-center text-sky-400 font-medium">
                <span className="w-3 h-0.5 bg-sky-400 mr-1.5" /> Actual Cost
              </span>
              <span className="flex items-center text-indigo-400 font-medium">
                <span className="w-3 h-0.5 border-t border-dashed border-indigo-400 mr-1.5" /> 8-Wk History Baseline
              </span>
              <span className="flex items-center text-amber-400 font-medium">
                <span className="w-3 h-0.5 border-t border-dotted border-amber-400 mr-1.5" /> Same-Type Peers
              </span>
            </div>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={timeseriesData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                <XAxis
                  dataKey="week_of"
                  tick={{ fill: '#64748b', fontSize: 11 }}
                  tickFormatter={(val) => {
                    const d = new Date(val);
                    return d.toLocaleDateString(undefined, { month: 'short', year: '2-digit' });
                  }}
                  interval={8}
                  stroke="#334155"
                />
                <YAxis
                  tick={{ fill: '#64748b', fontSize: 11 }}
                  tickFormatter={(val) => `₹${val.toFixed(1)}`}
                  domain={['auto', 'auto']}
                  stroke="#334155"
                />
                <Tooltip
                  content={({ active, payload, label }) => {
                    if (active && payload && payload.length) {
                      const d = payload[0].payload as RouteWeekRecord;
                      return (
                        <div className="bg-slate-900 border border-slate-700 rounded-xl p-3 shadow-xl text-xs space-y-1">
                          <p className="font-bold text-white">Week of {label}</p>
                          <p className="text-sky-400 font-semibold">Cost: ₹{d.cost_per_tonne_km.toFixed(2)} / t-km</p>
                          <p className="text-indigo-400">
                            History Baseline: {d.history_baseline ? `₹${d.history_baseline.toFixed(2)}` : 'N/A'} ({d.vs_own_history})
                          </p>
                          <p className="text-amber-400">
                            Peer Baseline: {d.peer_baseline ? `₹${d.peer_baseline.toFixed(2)}` : 'N/A'} ({d.vs_similar_routes})
                          </p>
                          <div className="pt-1 border-t border-slate-800">
                            <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                              d.flagged === 'No (justified)'
                                ? 'bg-emerald-500/20 text-emerald-400'
                                : d.flagged === 'Yes'
                                ? 'bg-rose-500/20 text-rose-400'
                                : 'bg-slate-800 text-slate-300'
                            }`}>
                              Verdict: {d.flagged}
                            </span>
                          </div>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="cost_per_tonne_km"
                  stroke="#38bdf8"
                  strokeWidth={2}
                  dot={(props: any) => {
                    const { cx, cy, payload } = props;
                    if (payload.flagged === 'No (justified)') {
                      return <circle cx={cx} cy={cy} r={5} fill="#10b981" stroke="#fff" strokeWidth={1.5} key={payload.week_of} />;
                    }
                    if (payload.flagged === 'Yes') {
                      return <circle cx={cx} cy={cy} r={5} fill="#f43f5e" stroke="#fff" strokeWidth={1.5} key={payload.week_of} />;
                    }
                    return <circle cx={cx} cy={cy} r={2} fill="#38bdf8" opacity={0.4} key={payload.week_of} />;
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="history_baseline"
                  stroke="#818cf8"
                  strokeWidth={1.5}
                  strokeDasharray="4 4"
                  dot={false}
                />
                <Line
                  type="monotone"
                  dataKey="peer_baseline"
                  stroke="#fbbf24"
                  strokeWidth={1.5}
                  strokeDasharray="2 2"
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Main Results Table */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/60 backdrop-blur-sm overflow-hidden">
        <div className="p-4 border-b border-slate-800 flex items-center justify-between">
          <div className="text-xs text-slate-400">
            Showing <span className="text-white font-bold">{records.length}</span> of{' '}
            <span className="text-white font-bold">{totalRecords}</span> matching route-weeks
          </div>
          {/* Pagination Controls */}
          <div className="flex items-center space-x-2">
            <button
              disabled={page <= 1}
              onClick={() => setPage(page - 1)}
              className="p-1 rounded-lg bg-slate-950 border border-slate-800 text-slate-400 hover:text-white disabled:opacity-40 transition"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="text-xs text-slate-400 font-mono">
              Page {page} / {totalPages || 1}
            </span>
            <button
              disabled={page >= totalPages}
              onClick={() => setPage(page + 1)}
              className="p-1 rounded-lg bg-slate-950 border border-slate-800 text-slate-400 hover:text-white disabled:opacity-40 transition"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/90 text-slate-400 uppercase tracking-wider border-b border-slate-800">
              <tr>
                <th className="py-3 px-4 font-semibold">Route</th>
                <th className="py-3 px-4 font-semibold">Week Of</th>
                <th className="py-3 px-4 font-semibold">Cost (INR/t-km)</th>
                <th className="py-3 px-4 font-semibold">vs Own History</th>
                <th className="py-3 px-4 font-semibold">vs Similar Hauls</th>
                <th className="py-3 px-4 font-semibold">Flagged Verdict</th>
                <th className="py-3 px-4 font-semibold">Matched Note</th>
                <th className="py-3 px-4 font-semibold">Plain-English Reason</th>
                <th className="py-3 px-4 font-semibold text-right">Audit</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-sans">
              {loading ? (
                <tr>
                  <td colSpan={9} className="py-12 text-center text-slate-400">
                    <div className="w-6 h-6 border-2 border-sky-400 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
                    Filtering freight records...
                  </td>
                </tr>
              ) : records.length === 0 ? (
                <tr>
                  <td colSpan={9} className="py-12 text-center text-slate-500">
                    No route-weeks match the active filters.
                  </td>
                </tr>
              ) : (
                records.map((r, idx) => (
                  <tr key={idx} className="hover:bg-slate-800/40 transition group">
                    <td className="py-3 px-4 font-bold text-white whitespace-nowrap">
                      {r.route}
                      <span className="block text-[10px] font-normal text-slate-400">{r.route_type} Haul</span>
                    </td>
                    <td className="py-3 px-4 text-slate-300 font-mono whitespace-nowrap">
                      {r.week_of}
                    </td>
                    <td className="py-3 px-4 font-bold text-sky-400 whitespace-nowrap">
                      ₹{r.cost_per_tonne_km.toFixed(2)}
                    </td>
                    <td className="py-3 px-4 whitespace-nowrap">
                      <span
                        className={`text-[11px] font-medium ${
                          r.vs_own_history.startsWith('+') && !r.vs_own_history.includes('+0.')
                            ? 'text-rose-400'
                            : 'text-slate-300'
                        }`}
                      >
                        {r.vs_own_history}
                      </span>
                    </td>
                    <td className="py-3 px-4 whitespace-nowrap">
                      <span
                        className={`text-[11px] font-medium ${
                          r.vs_similar_routes.startsWith('+') && !r.vs_similar_routes.includes('+0.')
                            ? 'text-rose-400'
                            : 'text-slate-300'
                        }`}
                      >
                        {r.vs_similar_routes}
                      </span>
                    </td>
                    <td className="py-3 px-4 whitespace-nowrap">
                      <span
                        className={`px-2.5 py-1 rounded-full text-[11px] font-bold inline-flex items-center space-x-1 ${
                          r.flagged === 'No (justified)'
                            ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                            : r.flagged === 'Yes'
                            ? 'bg-rose-500/15 text-rose-400 border border-rose-500/30 font-extrabold'
                            : 'bg-slate-800/80 text-slate-300 border border-slate-700/60'
                        }`}
                      >
                        {r.flagged === 'No (justified)' && <CheckCircle className="w-3 h-3 mr-1 inline" />}
                        {r.flagged === 'Yes' && <AlertTriangle className="w-3 h-3 mr-1 inline" />}
                        <span>{r.flagged}</span>
                      </span>
                    </td>
                    <td className="py-3 px-4 whitespace-nowrap">
                      {r.matched_note_id ? (
                        <span className="px-2 py-0.5 rounded-md font-mono text-[11px] font-bold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                          {r.matched_note_id}
                        </span>
                      ) : (
                        <span className="text-slate-600 font-mono">—</span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-slate-300 max-w-xs truncate" title={r.reason}>
                      {r.reason}
                    </td>
                    <td className="py-3 px-4 text-right whitespace-nowrap">
                      <button
                        onClick={() => onOpenEvidence(r)}
                        className="p-1.5 rounded-lg bg-slate-950 hover:bg-slate-800 text-sky-400 border border-slate-800 transition"
                        title="Audit 6 Evidence Gates"
                      >
                        <Eye className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
