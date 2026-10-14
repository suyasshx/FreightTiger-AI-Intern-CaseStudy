import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { OperationsOverview } from './components/OperationsOverview';
import { RouteExplorer } from './components/RouteExplorer';
import { AIAssistant } from './components/AIAssistant';
import { EvaluationView } from './components/EvaluationView';
import { ExportCenter } from './components/ExportCenter';
import { EvidenceInspectorModal } from './components/EvidenceInspectorModal';
import type { RouteOverviewSummary, RouteWeekRecord } from './types';
import { apiClient } from './api/client';
import { Shield } from 'lucide-react';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string>('overview');
  const [overview, setOverview] = useState<RouteOverviewSummary | null>(null);
  const [selectedRouteForExplorer, setSelectedRouteForExplorer] = useState<string>('All');
  const [inspectingRecord, setInspectingRecord] = useState<RouteWeekRecord | null>(null);
  const [initialLoading, setInitialLoading] = useState<boolean>(true);

  const loadData = () => {
    apiClient.getOverview()
      .then((data) => setOverview(data))
      .catch((err) => console.error("Error loading overview data:", err))
      .finally(() => setInitialLoading(false));
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleSelectRouteFromOverview = (routeName: string) => {
    setSelectedRouteForExplorer(routeName);
    setActiveTab('explorer');
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-sky-500/30 selection:text-sky-200">
      {/* Top Fixed Header */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        unexplainedCount={overview?.unexplained_anomalies || 0}
      />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {initialLoading ? (
          <div className="flex items-center justify-center min-h-[60vh]">
            <div className="text-center space-y-4">
              <div className="w-12 h-12 border-3 border-sky-400 border-t-transparent rounded-full animate-spin mx-auto" />
              <div className="space-y-1">
                <h3 className="text-base font-bold text-white">RouteGuard AI Engine Starting...</h3>
                <p className="text-xs text-slate-400">Loading freight records, computing rolling baselines, and loading vector index</p>
              </div>
            </div>
          </div>
        ) : (
          <>
            {activeTab === 'overview' && (
              <OperationsOverview
                overview={overview}
                onSelectRoute={handleSelectRouteFromOverview}
                onOpenEvidence={(rec) => setInspectingRecord(rec)}
              />
            )}

            {activeTab === 'explorer' && (
              <RouteExplorer
                initialRoute={selectedRouteForExplorer}
                onOpenEvidence={(rec) => setInspectingRecord(rec)}
              />
            )}

            {activeTab === 'assistant' && (
              <AIAssistant />
            )}

            {activeTab === 'evaluation' && (
              <EvaluationView />
            )}

            {activeTab === 'export' && (
              <ExportCenter onRefreshData={loadData} />
            )}
          </>
        )}
      </main>

      {/* Evidence Gate Inspector Modal */}
      <EvidenceInspectorModal
        record={inspectingRecord}
        onClose={() => setInspectingRecord(null)}
      />

      {/* Footer */}
      <footer className="border-t border-slate-800/80 bg-slate-950/80 py-6 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-500 gap-4">
          <div className="flex items-center space-x-2">
            <Shield className="w-4 h-4 text-sky-400" />
            <span className="font-semibold text-slate-300">RouteGuard AI Platform</span>
            <span>•</span>
            <span>FreightTiger Software Engineering Intern (AI) Case Study</span>
          </div>
          <div className="flex items-center space-x-4">
            <span>Deterministic RAG Engine</span>
            <span>•</span>
            <span>Local Open-Source Embeddings (`all-MiniLM-L6-v2`)</span>
            <span>•</span>
            <span className="font-mono text-slate-400">v1.0.0</span>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default App;
