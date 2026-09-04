import React from 'react';
import { ShieldCheck, LogOut, Upload, FileText, CheckCircle2, User } from 'lucide-react';

export const Dashboard = ({ user, onLogout }) => {
  return (
    <div className="max-w-3xl w-full mx-auto px-4 py-8">
      {/* Top Header Card */}
      <header className="flex items-center justify-between pb-6 mb-8 border-b border-slate-800">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 bg-gradient-to-br from-teal-500 to-emerald-600 rounded-xl shadow-lg shadow-teal-500/20">
            <ShieldCheck className="w-6 h-6 text-slate-950 font-bold" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-white">IntelliVault</h1>
            <p className="text-xs text-slate-400">Secure Cloud Storage with Document AI</p>
          </div>
        </div>

        <button
          onClick={onLogout}
          className="flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-semibold bg-slate-900 hover:bg-slate-800 text-slate-300 hover:text-white border border-slate-700/80 transition-all shadow-sm active:scale-95"
        >
          <LogOut className="w-3.5 h-3.5 text-red-400" />
          <span>Logout</span>
        </button>
      </header>

      {/* User Welcome Card */}
      <div className="p-6 rounded-2xl border border-slate-800 bg-slate-900/60 shadow-xl backdrop-blur-sm mb-8">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2 rounded-lg bg-teal-500/10 border border-teal-500/30 text-teal-400">
            <User className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-white">
              Welcome, {user?.name || 'User'}
            </h2>
            <span className="text-xs text-slate-400">Authenticated Session</span>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-4 border-t border-slate-800/80 text-sm">
          <div>
            <span className="block text-xs font-mono text-slate-400 uppercase tracking-wider mb-1">
              Email
            </span>
            <span className="font-mono text-slate-200">{user?.email}</span>
          </div>

          <div>
            <span className="block text-xs font-mono text-slate-400 uppercase tracking-wider mb-1">
              Account Status
            </span>
            <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
              <CheckCircle2 className="w-3 h-3" />
              {user?.status ? user.status.charAt(0).toUpperCase() + user.status.slice(1) : 'Active'}
            </span>
          </div>
        </div>
      </div>

      {/* My Files Section */}
      <div className="p-6 rounded-2xl border border-slate-800 bg-slate-900/40 shadow-xl">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-base font-bold text-white tracking-tight">My Files</h3>
          <button
            disabled
            title="File upload will be enabled in the next step"
            className="flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-semibold bg-teal-500/20 text-teal-300 border border-teal-500/40 cursor-not-allowed opacity-80"
          >
            <Upload className="w-3.5 h-3.5" />
            <span>Upload File</span>
          </button>
        </div>

        {/* Empty State */}
        <div className="py-12 border-2 border-dashed border-slate-800/90 rounded-xl flex flex-col items-center justify-center text-center p-6">
          <div className="p-3 bg-slate-800/50 rounded-2xl mb-3 text-slate-500">
            <FileText className="w-8 h-8" />
          </div>
          <p className="text-sm font-medium text-slate-300">No files yet.</p>
          <p className="text-xs text-slate-500 max-w-sm mt-1">
            File upload, client-transparent AES-256 GCM encryption, and MinIO object storage will be integrated in the upcoming steps.
          </p>
        </div>
      </div>
    </div>
  );
};
