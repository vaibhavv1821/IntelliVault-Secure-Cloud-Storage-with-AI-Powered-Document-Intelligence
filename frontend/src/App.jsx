import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { StatusCard } from './components/StatusCard';
import { PhaseTimeline } from './components/PhaseTimeline';
import { getHealth, getSystemStatus } from './services/api';
import { RefreshCw, Server, Cpu, Shield, BookOpen, Terminal, CheckCircle2 } from 'lucide-react';

export function App() {
  const [healthData, setHealthData] = useState(null);
  const [statusData, setStatusData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [lastRefreshed, setLastRefreshed] = useState(null);

  const fetchSystemTelemetry = async () => {
    setLoading(true);
    const [healthRes, statusRes] = await Promise.all([
      getHealth(),
      getSystemStatus()
    ]);
    setHealthData(healthRes);
    setStatusData(statusRes);
    setLastRefreshed(new Date().toLocaleTimeString());
    setLoading(false);
  };

  useEffect(() => {
    fetchSystemTelemetry();
  }, []);

  const isOperational = statusData?.data?.status === 'operational';

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      <Navbar systemHealth={healthData} />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-10">
        {/* Hero Section */}
        <div className="mb-10 flex flex-col md:flex-row md:items-center justify-between gap-6 pb-8 border-b border-slate-800">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-teal-500/10 text-teal-300 border border-teal-500/30 mb-3">
              <Shield className="w-3.5 h-3.5 text-teal-400" />
              Zero-Trust Architecture & Interpretable Document AI
            </div>
            <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white">
              System Telemetry & Foundation Dashboard
            </h1>
            <p className="mt-2 text-sm sm:text-base text-slate-400 max-w-2xl">
              IntelliVault foundation active. Verifying backend REST APIs, MongoDB connection handles, and S3/MinIO encrypted storage adapters.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={fetchSystemTelemetry}
              disabled={loading}
              className="flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-200 transition-all shadow-md active:scale-95 disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 text-teal-400 ${loading ? 'animate-spin' : ''}`} />
              Refresh Diagnostic
            </button>
          </div>
        </div>

        {/* Telemetry Summary Strip */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/40">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono text-slate-400">Backend API</span>
              <Server className="w-4 h-4 text-teal-400" />
            </div>
            <p className="mt-2 text-xl font-bold text-white font-mono">
              {healthData?.success ? 'HTTP 200 OK' : 'OFFLINE'}
            </p>
            <span className="text-[11px] text-slate-500">Flask Factory on Port 5000</span>
          </div>

          <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/40">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono text-slate-400">Python Runtime</span>
              <Terminal className="w-4 h-4 text-emerald-400" />
            </div>
            <p className="mt-2 text-xl font-bold text-white font-mono">
              Python {statusData?.data?.platform?.python_version || '3.13'}
            </p>
            <span className="text-[11px] text-slate-500">
              OS: {statusData?.data?.platform?.os || 'Windows'}
            </span>
          </div>

          <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/40">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono text-slate-400">Documentation</span>
              <BookOpen className="w-4 h-4 text-cyan-400" />
            </div>
            <p className="mt-2 text-xl font-bold text-white font-mono">55 Sections</p>
            <span className="text-[11px] text-teal-400">PDF & Markdown Synchronized</span>
          </div>

          <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/40">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono text-slate-400">Diagnostic Time</span>
              <ClockIcon className="w-4 h-4 text-amber-400" />
            </div>
            <p className="mt-2 text-xl font-bold text-white font-mono">
              {lastRefreshed || 'Polling...'}
            </p>
            <span className="text-[11px] text-slate-500">Vite HMR Enabled</span>
          </div>
        </div>

        {/* Service Health Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-10">
          <StatusCard
            title="MongoDB Metadata Store"
            type="database"
            status={statusData?.data?.services?.database}
            loading={loading}
          />
          <StatusCard
            title="MinIO Object Storage"
            type="storage"
            status={statusData?.data?.services?.storage}
            loading={loading}
          />
        </div>

        {/* Phase Timeline Section */}
        <PhaseTimeline />
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/80 bg-slate-950 py-6 text-center text-xs text-slate-500">
        <p>IntelliVault ~ Secure Cloud Storage with AI-Powered Document Intelligence | Master Phase 0 Foundation</p>
      </footer>
    </div>
  );
}

function ClockIcon(props) {
  return (
    <svg {...props} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10"/>
      <polyline points="12 6 12 12 16 14"/>
    </svg>
  );
}

export default App;
