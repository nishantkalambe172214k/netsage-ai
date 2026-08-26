import React from 'react';
import { LayoutDashboard, FileText, Wrench, UserCheck, ShieldAlert, BookOpen, Network } from 'lucide-react';

const NAV_ITEMS = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'cases', label: 'Cases', icon: FileText },
  { id: 'troubleshoot', label: 'Troubleshoot', icon: Wrench },
  { id: 'review', label: 'Human Review', icon: UserCheck },
  { id: 'rules', label: 'Rule Checker', icon: ShieldAlert },
  { id: 'responsible-ai', label: 'Responsible AI', icon: BookOpen },
];

export default function Navigation({ activeTab, setActiveTab, health }) {
  return (
    <header className="border-b border-slate-800 bg-slate-900/90 sticky top-0 z-50 backdrop-blur px-6 py-3 flex items-center justify-between">
      {/* Brand */}
      <div className="flex items-center space-x-3">
        <div className="bg-sky-500/10 border border-sky-500/30 p-2 rounded-lg text-sky-400">
          <Network className="w-6 h-6" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-lg font-bold tracking-tight text-white">NetSage AI</h1>
            <span className="text-[11px] px-2 py-0.5 rounded bg-sky-500/20 text-sky-300 font-medium border border-sky-500/30">
              Cisco Packet Tracer
            </span>
          </div>
          <p className="text-xs text-slate-400">Rule-Checked &bull; Human-Governed Network Assistant</p>
        </div>
      </div>

      {/* Tabs */}
      <nav className="flex items-center space-x-1 bg-slate-950/60 p-1 rounded-xl border border-slate-800">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                isActive
                  ? 'bg-sky-600 text-white shadow-md'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              <Icon className="w-4 h-4" />
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>

      {/* Health Badge */}
      <div className="flex items-center space-x-2 text-xs">
        <div className="flex items-center space-x-1.5 px-3 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
          <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span>System & SQLite Connected</span>
        </div>
      </div>
    </header>
  );
}
