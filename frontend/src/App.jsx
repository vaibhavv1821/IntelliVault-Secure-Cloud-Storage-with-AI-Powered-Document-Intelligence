import React, { useState, useEffect } from 'react';
import { AuthCard } from './components/AuthCard';
import { Dashboard } from './components/Dashboard';
import { Navbar } from './components/Navbar';
import { StatusCard } from './components/StatusCard';
import { PhaseTimeline } from './components/PhaseTimeline';
import { getMeApi, clearAuthToken, getHealth, getSystemStatus } from './services/api';
import { Activity, Shield, RefreshCw } from 'lucide-react';

export function App() {
  const [currentUser, setCurrentUser] = useState(null);
  const [authLoading, setAuthLoading] = useState(true);
  const [viewMode, setViewMode] = useState('app'); // 'app' | 'telemetry'

  // Diagnostic state for telemetry view
  const [healthData, setHealthData] = useState(null);
  const [statusData, setStatusData] = useState(null);
  const [telemetryLoading, setTelemetryLoading] = useState(false);

  // Restore authenticated session on initial mount
  useEffect(() => {
    const restoreSession = async () => {
      setAuthLoading(true);
      const res = await getMeApi();
      if (res.success && res.data?.user) {
        setCurrentUser(res.data.user);
      } else {
        clearAuthToken();
        setCurrentUser(null);
      }
      setAuthLoading(false);
    };

    restoreSession();
  }, []);

  const handleLogout = () => {
    clearAuthToken();
    setCurrentUser(null);
  };

  const handleAuthSuccess = (user) => {
    setCurrentUser(user);
  };

  const fetchTelemetry = async () => {
    setTelemetryLoading(true);
    const [hRes, sRes] = await Promise.all([getHealth(), getSystemStatus()]);
    setHealthData(hRes);
    setStatusData(sRes);
    setTelemetryLoading(false);
  };

  const toggleTelemetry = () => {
    if (viewMode === 'app') {
      setViewMode('telemetry');
      fetchTelemetry();
    } else {
      setViewMode('app');
    }
  };

  if (authLoading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center text-slate-400 font-mono text-xs">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-teal-400 animate-ping" />
          <span>Verifying secure session...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-teal-500 selection:text-white">
      {/* Top Bar Navigation */}
      <nav className="border-b border-slate-800 bg-slate-900/50 backdrop-blur-md px-4 sm:px-6 lg:px-8 h-14 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Shield className="w-4 h-4 text-teal-400" />
          <span className="text-sm font-bold tracking-tight text-white">IntelliVault</span>
          <span className="px-2 py-0.5 text-[10px] font-semibold bg-teal-500/10 text-teal-400 border border-teal-500/20 rounded-full">
            Core Vault
          </span>
        </div>

        <button
          onClick={toggleTelemetry}
          className="flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-medium bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-slate-200 border border-slate-800 transition-all"
        >
          <Activity className="w-3.5 h-3.5 text-teal-400" />
          <span>{viewMode === 'app' ? 'System Telemetry' : 'Back to Vault'}</span>
        </button>
      </nav>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col justify-center py-8">
        {viewMode === 'telemetry' ? (
          <div className="max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between mb-6 pb-4 border-b border-slate-800">
              <h2 className="text-xl font-bold text-white">System Diagnostics</h2>
              <button
                onClick={fetchTelemetry}
                disabled={telemetryLoading}
                className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs bg-slate-900 border border-slate-700 text-slate-300 disabled:opacity-50"
              >
                <RefreshCw className={`w-3 h-3 text-teal-400 ${telemetryLoading ? 'animate-spin' : ''}`} />
                Refresh Telemetry
              </button>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
              <StatusCard
                title="MongoDB Metadata Store"
                type="database"
                status={statusData?.data?.services?.database}
                loading={telemetryLoading}
              />
              <StatusCard
                title="MinIO Object Storage"
                type="storage"
                status={statusData?.data?.services?.storage}
                loading={telemetryLoading}
              />
            </div>
            <PhaseTimeline />
          </div>
        ) : currentUser ? (
          <Dashboard user={currentUser} onLogout={handleLogout} />
        ) : (
          <div className="px-4">
            <AuthCard onAuthSuccess={handleAuthSuccess} />
          </div>
        )}
      </main>

      {/* Minimal Footer */}
      <footer className="border-t border-slate-800/60 py-4 text-center text-[11px] text-slate-500 font-mono">
        IntelliVault ~ Secure Cloud Storage & AI Document Intelligence
      </footer>
    </div>
  );
}

export default App;
