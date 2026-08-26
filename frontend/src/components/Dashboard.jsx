import React, { useEffect, useState } from 'react';
import { getDashboard, seedDatabaseCases, seedResponsibleAIExamples } from '../services/api';
import { 
  FileText, Cpu, UserCheck, CheckCircle2, Edit3, XCircle, 
  ShieldCheck, Percent, BookOpen, AlertOctagon, RefreshCw 
} from 'lucide-react';

export default function Dashboard({ onNavigateToCase }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [seeding, setSeeding] = useState(false);
  const [error, setError] = useState(null);

  const loadData = async () => {
    try {
      setLoading(true);
      const res = await getDashboard();
      setData(res);
      setError(null);
    } catch (err) {
      setError(err.message || 'Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleSeed = async () => {
    try {
      setSeeding(true);
      await seedDatabaseCases();
      await seedResponsibleAIExamples();
      await loadData();
    } catch (err) {
      alert('Error seeding: ' + err.message);
    } finally {
      setSeeding(false);
    }
  };

  if (loading) {
    return (
      <div className="p-8 text-center text-slate-400">
        <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-2 text-sky-400" />
        <p>Loading real-time database metrics...</p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="p-8 text-center text-rose-400 bg-rose-500/10 border border-rose-500/20 rounded-xl m-6">
        <AlertOctagon className="w-8 h-8 mx-auto mb-2" />
        <p>{error || 'Failed to load dashboard'}</p>
        <button 
          onClick={loadData}
          className="mt-4 px-4 py-1.5 bg-slate-800 hover:bg-slate-700 text-white text-xs rounded-lg"
        >
          Retry
        </button>
      </div>
    );
  }

  const { kpis, charts } = data;

  return (
    <div className="space-y-6 max-w-7xl mx-auto p-6">
      {/* Header with Quick Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight">Troubleshooting Intelligence Dashboard</h2>
          <p className="text-xs text-slate-400">Real-time metrics computed directly from SQLite database</p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={handleSeed}
            disabled={seeding}
            className="flex items-center space-x-1.5 px-3 py-1.5 bg-sky-600/20 hover:bg-sky-600/30 text-sky-300 border border-sky-500/30 rounded-lg text-xs font-medium transition"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${seeding ? 'animate-spin' : ''}`} />
            <span>Seed 30 Cases & 5+ AI Corrections</span>
          </button>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3">
        {/* Total Cases */}
        <div className="bg-slate-900/70 border border-slate-800 p-4 rounded-xl space-y-1">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-[11px] uppercase font-semibold">Total Cases</span>
            <FileText className="w-4 h-4 text-sky-400" />
          </div>
          <div className="text-2xl font-bold text-white">{kpis.total_cases}</div>
          <div className="text-[10px] text-slate-500">Packet Tracer</div>
        </div>

        {/* AI Diagnosed */}
        <div className="bg-slate-900/70 border border-slate-800 p-4 rounded-xl space-y-1">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-[11px] uppercase font-semibold">AI Diagnosed</span>
            <Cpu className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="text-2xl font-bold text-indigo-300">{kpis.ai_diagnosed}</div>
          <div className="text-[10px] text-slate-500">Analyzed</div>
        </div>

        {/* Human Reviewed */}
        <div className="bg-slate-900/70 border border-slate-800 p-4 rounded-xl space-y-1">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-[11px] uppercase font-semibold">Human Reviewed</span>
            <UserCheck className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-bold text-amber-300">{kpis.human_reviewed}</div>
          <div className="text-[10px] text-slate-500">HITL Gated</div>
        </div>

        {/* Accepted */}
        <div className="bg-slate-900/70 border border-slate-800 p-4 rounded-xl space-y-1">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-[11px] uppercase font-semibold">Accepted</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-emerald-300">{kpis.accepted}</div>
          <div className="text-[10px] text-slate-500">AI Approved</div>
        </div>

        {/* Edited */}
        <div className="bg-slate-900/70 border border-slate-800 p-4 rounded-xl space-y-1">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-[11px] uppercase font-semibold">Edited</span>
            <Edit3 className="w-4 h-4 text-blue-400" />
          </div>
          <div className="text-2xl font-bold text-blue-300">{kpis.edited}</div>
          <div className="text-[10px] text-slate-500">Corrected</div>
        </div>

        {/* Rejected */}
        <div className="bg-slate-900/70 border border-slate-800 p-4 rounded-xl space-y-1">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-[11px] uppercase font-semibold">Rejected</span>
            <XCircle className="w-4 h-4 text-rose-400" />
          </div>
          <div className="text-2xl font-bold text-rose-300">{kpis.rejected}</div>
          <div className="text-[10px] text-slate-500">Overruled</div>
        </div>

        {/* Verified */}
        <div className="bg-slate-900/70 border border-slate-800 p-4 rounded-xl space-y-1">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-[11px] uppercase font-semibold">Verified</span>
            <ShieldCheck className="w-4 h-4 text-teal-400" />
          </div>
          <div className="text-2xl font-bold text-teal-300">{kpis.verified_passed}</div>
          <div className="text-[10px] text-slate-500">Passed Tests</div>
        </div>

        {/* Agreement Rate */}
        <div className="bg-slate-900/70 border border-slate-800 p-4 rounded-xl space-y-1">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-[11px] uppercase font-semibold">Agreement</span>
            <Percent className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-2xl font-bold text-purple-300">{kpis.ai_human_agreement_rate}%</div>
          <div className="text-[10px] text-slate-500">AI vs Human</div>
        </div>
      </div>

      {/* Responsible AI Highlight Banner */}
      <div className="bg-gradient-to-r from-blue-950/40 via-indigo-950/40 to-slate-900/60 border border-indigo-500/30 rounded-xl p-5 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex items-center space-x-4">
          <div className="p-3 bg-indigo-500/20 text-indigo-300 rounded-xl border border-indigo-500/30">
            <BookOpen className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-bold text-white">Responsible AI Audit Governance</h3>
              <span className="px-2.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 text-xs font-semibold border border-emerald-500/30">
                {kpis.responsible_ai_corrections} Corrections Logged (Target: 5+)
              </span>
            </div>
            <p className="text-xs text-slate-300 mt-0.5">
              Enforcing Human-in-the-Loop oversight where human engineers correct, refine, or overrule AI diagnoses before network application.
            </p>
          </div>
        </div>
      </div>

      {/* Charts & Breakdown Section */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {/* 1. Cases by Category */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 space-y-4">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            1. Cases by Issue Category (30 Total)
          </h3>
          <div className="space-y-2.5">
            {Object.entries(charts.cases_by_category).map(([cat, count]) => {
              const pct = kpis.total_cases > 0 ? (count / kpis.total_cases) * 100 : 0;
              return (
                <div key={cat} className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span className="text-slate-300 font-medium">{cat}</span>
                    <span className="text-slate-400">{count} cases ({Math.round(pct)}%)</span>
                  </div>
                  <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
                    <div 
                      className="bg-sky-500 h-1.5 rounded-full transition-all duration-500" 
                      style={{ width: `${pct}%` }} 
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* 2. Human Review Outcomes */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 space-y-4">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            2. Human Review Outcomes (HITL Gate)
          </h3>
          <div className="space-y-3">
            {[
              { label: 'Accepted (AI Approved)', count: charts.review_outcomes['Accepted'], color: 'bg-emerald-500', text: 'text-emerald-400' },
              { label: 'Edited (Human Corrected)', count: charts.review_outcomes['Edited'], color: 'bg-blue-500', text: 'text-blue-400' },
              { label: 'Rejected (Human Overruled)', count: charts.review_outcomes['Rejected'], color: 'bg-rose-500', text: 'text-rose-400' },
              { label: 'Pending Human Review', count: charts.review_outcomes['Pending Review'], color: 'bg-slate-600', text: 'text-slate-400' },
            ].map((item) => {
              const total = kpis.total_cases || 1;
              const pct = Math.round((item.count / total) * 100);
              return (
                <div key={item.label} className="p-2.5 rounded-lg bg-slate-950/40 border border-slate-800/80 space-y-1.5">
                  <div className="flex justify-between text-xs">
                    <span className="text-slate-300">{item.label}</span>
                    <span className={`font-bold ${item.text}`}>{item.count} ({pct}%)</span>
                  </div>
                  <div className="w-full bg-slate-800 rounded-full h-1.5">
                    <div className={`${item.color} h-1.5 rounded-full`} style={{ width: `${pct}%` }} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* 3. Verification Results */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 space-y-4">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            3. Post-Fix Verification Status
          </h3>
          <div className="space-y-3">
            {[
              { label: 'Passed (Full Resolution)', count: charts.verification_results['Passed'], color: 'bg-teal-500', text: 'text-teal-400' },
              { label: 'Partial Resolution', count: charts.verification_results['Partial'], color: 'bg-amber-500', text: 'text-amber-400' },
              { label: 'Failed Verification', count: charts.verification_results['Failed'], color: 'bg-rose-500', text: 'text-rose-400' },
              { label: 'Pending Verification', count: charts.verification_results['Pending Verification'], color: 'bg-slate-600', text: 'text-slate-400' },
            ].map((item) => {
              return (
                <div key={item.label} className="p-2.5 rounded-lg bg-slate-950/40 border border-slate-800/80 space-y-1.5">
                  <div className="flex justify-between text-xs">
                    <span className="text-slate-300">{item.label}</span>
                    <span className={`font-bold ${item.text}`}>{item.count}</span>
                  </div>
                  <div className="w-full bg-slate-800 rounded-full h-1.5">
                    <div className={`${item.color} h-1.5 rounded-full`} style={{ width: `${Math.min(100, item.count * 15)}%` }} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
