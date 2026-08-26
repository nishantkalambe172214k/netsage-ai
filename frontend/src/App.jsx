import React, { useEffect, useState } from 'react';
import { checkHealth, getCases } from './services/api';
import { Shield, CheckCircle, AlertTriangle, Network, Cpu, FileCheck } from 'lucide-react';

function App() {
  const [health, setHealth] = useState(null);
  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function loadInitialData() {
      try {
        setLoading(true);
        const healthData = await checkHealth();
        setHealth(healthData);
        const casesData = await getCases();
        setCases(casesData);
      } catch (err) {
        setError(err.message || 'Failed to connect to backend');
      } finally {
        setLoading(false);
      }
    }
    loadInitialData();
  }, []);

  return (
    <div className="min-h-screen w-screen bg-slate-950 text-slate-100 flex flex-col">
      {/* Header */}
      <header className="border-b border-slate-800 bg-slate-900/50 backdrop-blur px-6 py-4 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="bg-sky-500/10 border border-sky-500/30 p-2 rounded-lg text-sky-400">
            <Network className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
              NetSage AI
              <span className="text-xs px-2 py-0.5 rounded bg-sky-500/20 text-sky-300 font-medium border border-sky-500/30">
                v0.1.0 Core
              </span>
            </h1>
            <p className="text-xs text-slate-400">Cisco Packet Tracer Troubleshooting & Mandatory Human Review</p>
          </div>
        </div>

        {/* Health Status Indicator */}
        <div className="flex items-center space-x-2 text-xs">
          {loading ? (
            <span className="text-slate-400">Connecting to API...</span>
          ) : error ? (
            <div className="flex items-center space-x-1.5 px-3 py-1 rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/20">
              <AlertTriangle className="w-3.5 h-3.5" />
              <span>Backend Offline</span>
            </div>
          ) : (
            <div className="flex items-center space-x-1.5 px-3 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <CheckCircle className="w-3.5 h-3.5" />
              <span>System & Database Active ({health?.database})</span>
            </div>
          )}
        </div>
      </header>

      {/* Main Core View */}
      <main className="flex-1 max-w-6xl w-full mx-auto p-6 space-y-6">
        {/* Core Architecture Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 space-y-2">
            <div className="flex items-center space-x-2 text-sky-400 font-semibold">
              <Cpu className="w-5 h-5" />
              <h2>Deterministic Python Rules</h2>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">
              Enforces strict Cisco IOS / Packet Tracer rule checks across VLANs, IP subnets, routing protocols, and ACLs.
            </p>
          </div>

          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 space-y-2">
            <div className="flex items-center space-x-2 text-indigo-400 font-semibold">
              <Shield className="w-5 h-5" />
              <h2>AI Root Cause Analysis</h2>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">
              Synthesizes packet trace logs, CLI show outputs, and topologies to generate targeted remediation commands.
            </p>
          </div>

          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 space-y-2">
            <div className="flex items-center space-x-2 text-emerald-400 font-semibold">
              <FileCheck className="w-5 h-5" />
              <h2>Mandatory Human Review</h2>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">
              Mandatory Human-in-the-Loop review gate ensures no AI command is executed without engineer approval.
            </p>
          </div>
        </div>

        {/* Database Models Ready Summary */}
        <div className="bg-slate-900/40 border border-slate-800/80 rounded-xl p-6 space-y-4">
          <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
            Database Models Initialized
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            {[
              { name: 'cases', desc: 'Tickets & Topologies' },
              { name: 'rule_findings', desc: 'Rule Checks' },
              { name: 'diagnoses', desc: 'AI Hypotheses' },
              { name: 'reviews', desc: 'Mandatory HITL' },
              { name: 'verification_results', desc: 'Post-Fix Tests' },
            ].map((model) => (
              <div key={model.name} className="p-3 rounded-lg bg-slate-950/60 border border-slate-800 text-center">
                <div className="text-xs font-mono font-bold text-sky-300">{model.name}</div>
                <div className="text-[11px] text-slate-500 mt-1">{model.desc}</div>
              </div>
            ))}
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/60 py-3 text-center text-xs text-slate-500">
        NetSage AI &bull; Cisco Packet Tracer Troubleshooting Engine
      </footer>
    </div>
  );
}

export default App;
