import React from 'react';
import { ShieldCheck, FileText, Cpu, Terminal } from 'lucide-react';

export const Navbar = ({ systemHealth }) => {
  const isHealthy = systemHealth?.success;

  return (
    <header className="border-b border-slate-800 bg-slate-900/70 backdrop-blur-md sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Logo & Brand */}
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-gradient-to-br from-teal-500 to-emerald-600 rounded-xl shadow-lg shadow-teal-500/20 text-slate-950 font-bold">
            <ShieldCheck className="w-5 h-5 text-slate-950" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-lg font-bold tracking-tight text-white">IntelliVault</span>
              <span className="px-2 py-0.5 text-xs font-semibold bg-teal-500/10 text-teal-400 border border-teal-500/30 rounded-full">
                Phase 0
              </span>
            </div>
            <p className="text-xs text-slate-400 hidden sm:block">Secure Cloud Storage with Document AI</p>
          </div>
        </div>

        {/* Live Status Badge */}
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2 px-3 py-1.5 rounded-lg border border-slate-800 bg-slate-950/60">
            <span className="relative flex h-2.5 w-2.5">
              <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${isHealthy ? 'bg-emerald-400' : 'bg-amber-400'}`}></span>
              <span className={`relative inline-flex rounded-full h-2.5 w-2.5 ${isHealthy ? 'bg-emerald-500' : 'bg-amber-500'}`}></span>
            </span>
            <span className="text-xs font-mono text-slate-300">
              API: {isHealthy ? 'ONLINE' : 'CONNECTING...'}
            </span>
          </div>

          <div className="hidden md:flex items-center space-x-2 text-xs text-slate-400">
            <span className="flex items-center gap-1 font-mono">
              <Terminal className="w-3.5 h-3.5 text-teal-400" />
              Flask REST
            </span>
          </div>
        </div>
      </div>
    </header>
  );
};
