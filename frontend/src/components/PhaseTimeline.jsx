import React from 'react';
import { Layers, CheckCircle2, Clock, Lock, Sparkles, Activity } from 'lucide-react';

export const PhaseTimeline = () => {
  const phases = [
    {
      id: 'phase-0',
      title: 'Phase 0: Foundation',
      subtitle: 'Architecture, DB & Storage Connectivity',
      status: 'IN PROGRESS',
      badgeClass: 'bg-teal-500/20 text-teal-300 border-teal-500/40',
      icon: <Clock className="w-4 h-4 text-teal-400" />,
      features: [
        'Flask REST App Factory',
        'React + Vite + Tailwind Scaffolding',
        'MongoDB Connection Adapter',
        'MinIO/S3 Storage Health Probe',
        'Structured Logger & JSON Error Envelope',
        '55-Section Master Technical Documentation'
      ]
    },
    {
      id: 'phase-1',
      title: 'Phase 1: Secure Cloud Storage',
      subtitle: 'Auth, Zero-Knowledge AES-256 Vault',
      status: 'PLANNED',
      badgeClass: 'bg-slate-800 text-slate-400 border-slate-700',
      icon: <Lock className="w-4 h-4 text-slate-400" />,
      features: [
        'JWT Authentication & bcrypt Security',
        'Client-Transparent AES-256 GCM Encryption',
        'File Upload, Streaming Download, Versioning',
        'Nested Materialized Path Folder Hierarchy',
        'Expiring Share Links & Revocation Tokens',
        'Tamper-Resistant Audit Logging'
      ]
    },
    {
      id: 'phase-2',
      title: 'Phase 2: Document Intelligence',
      subtitle: 'Computer Vision & NLP Pipelines',
      status: 'PLANNED',
      badgeClass: 'bg-slate-800 text-slate-400 border-slate-700',
      icon: <Sparkles className="w-4 h-4 text-slate-400" />,
      features: [
        'MobileNetV2 Image Auto-Tagging',
        'Grad-CAM Explainability Heatmaps',
        'TF-IDF & LinearSVC Document Classification',
        'Perceptual Hashing (pHash) Duplicate Detection',
        'spaCy NER & Regex Automated PII Redaction',
        'AI-Powered Metadata Search'
      ]
    },
    {
      id: 'phase-3',
      title: 'Phase 3: Security & Storage Optimization',
      subtitle: 'Anomaly Detection & Tiering',
      status: 'PLANNED',
      badgeClass: 'bg-slate-800 text-slate-400 border-slate-700',
      icon: <Activity className="w-4 h-4 text-slate-400" />,
      features: [
        'Access Log Feature Engineering',
        'Isolation Forest Anomaly & Risk Scoring',
        'Random Forest Hot/Cold Storage Tiering',
        'Automated Retention Lifecycle Jobs',
        'Executive Security & Cost Analytics Dashboard'
      ]
    }
  ];

  return (
    <div className="mt-12">
      <div className="flex items-center space-x-2 mb-6">
        <Layers className="w-5 h-5 text-teal-400" />
        <h2 className="text-xl font-bold text-white tracking-tight">System Development Roadmap</h2>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {phases.map((phase) => (
          <div
            key={phase.id}
            className={`p-5 rounded-2xl border transition-all ${
              phase.status === 'IN PROGRESS'
                ? 'border-teal-500/50 bg-gradient-to-b from-slate-900 via-slate-900/90 to-teal-950/20 shadow-lg shadow-teal-950/40 ring-1 ring-teal-500/20'
                : 'border-slate-800 bg-slate-900/40 opacity-75 hover:opacity-100 hover:border-slate-700'
            }`}
          >
            <div className="flex items-center justify-between mb-3">
              <span className={`px-2.5 py-0.5 text-xs font-semibold rounded-full border ${phase.badgeClass}`}>
                {phase.status}
              </span>
              {phase.icon}
            </div>

            <h3 className="text-base font-bold text-slate-100">{phase.title}</h3>
            <p className="text-xs text-slate-400 mt-1 mb-4">{phase.subtitle}</p>

            <ul className="space-y-2 border-t border-slate-800 pt-3">
              {phase.features.map((feat, idx) => (
                <li key={idx} className="flex items-start text-xs text-slate-300">
                  <span className="text-teal-400 mr-2 mt-0.5">•</span>
                  <span>{feat}</span>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </div>
  );
};
