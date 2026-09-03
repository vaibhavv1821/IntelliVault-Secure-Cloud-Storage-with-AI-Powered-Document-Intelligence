import React from 'react';
import { Database, HardDrive, CheckCircle2, XCircle, AlertTriangle, RefreshCw } from 'lucide-react';

export const StatusCard = ({ title, type, status, details, hint, loading }) => {
  const isConnected = status?.connected === true;
  const isPending = loading || status === undefined;

  const getIcon = () => {
    switch (type) {
      case 'database':
        return <Database className="w-5 h-5 text-emerald-400" />;
      case 'storage':
        return <HardDrive className="w-5 h-5 text-teal-400" />;
      default:
        return <Database className="w-5 h-5 text-slate-400" />;
    }
  };

  return (
    <div className="p-6 rounded-2xl border border-slate-800 bg-slate-900/60 shadow-xl backdrop-blur-sm transition-all hover:border-slate-700">
      <div className="flex items-start justify-between">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 rounded-xl bg-slate-800/80 border border-slate-700/50">
            {getIcon()}
          </div>
          <div>
            <h3 className="text-base font-semibold text-white">{title}</h3>
            <span className="text-xs font-mono text-slate-400">{status?.type || type}</span>
          </div>
        </div>

        {isPending ? (
          <span className="flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded-full bg-slate-800 text-slate-400">
            <RefreshCw className="w-3 h-3 animate-spin" /> Checking
          </span>
        ) : isConnected ? (
          <span className="flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
            <CheckCircle2 className="w-3.5 h-3.5" /> Connected
          </span>
        ) : (
          <span className="flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/30">
            <AlertTriangle className="w-3.5 h-3.5" /> Offline / Standby
          </span>
        )}
      </div>

      <div className="mt-5 space-y-2 border-t border-slate-800/80 pt-4 text-xs font-mono">
        <div className="flex justify-between text-slate-400">
          <span>Target Resource:</span>
          <span className="text-slate-200 truncate max-w-[200px]">
            {status?.database || status?.bucket || status?.endpoint || 'Configured via .env'}
          </span>
        </div>

        {status?.server_info && (
          <div className="flex justify-between text-slate-400">
            <span>Server Response:</span>
            <span className="text-emerald-400">{status.server_info}</span>
          </div>
        )}

        {status?.error && (
          <div className="p-3 mt-3 rounded-lg bg-red-950/30 border border-red-900/50 text-red-300">
            <p className="font-semibold mb-1">Status Diagnostic:</p>
            <p className="text-[11px] leading-relaxed opacity-90">{status.error}</p>
            {status.hint && (
              <p className="mt-2 text-[11px] text-amber-300/90 font-sans">{status.hint}</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
