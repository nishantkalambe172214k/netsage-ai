import React, { useEffect, useState } from 'react';
import { getResponsibleAILog, seedResponsibleAIExamples } from '../services/api';
import { BookOpen, AlertCircle, ArrowDown, UserCheck, CheckCircle2, RefreshCw } from 'lucide-react';

export default function ResponsibleAILog() {
  const [logData, setLogData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [seeding, setSeeding] = useState(false);

  const loadData = async () => {
    try {
      setLoading(true);
      const res = await getResponsibleAILog();
      setLogData(res);
    } catch (err) {
      console.error(err);
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
      await seedResponsibleAIExamples();
      await loadData();
    } catch (err) {
      alert('Error seeding: ' + err.message);
    } finally {
      setSeeding(false);
    }
  };

  const records = logData?.records || [];
  const totalCount = logData?.total_corrections || 0;

  return (
    <div className="space-y-6 max-w-7xl mx-auto p-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-bold text-white tracking-tight">Responsible AI Governance & Correction Log</h2>
            <span className="px-2.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 text-xs font-semibold border border-emerald-500/30">
              AI Corrections: {totalCount} (Target: 5+)
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Auditable records where human engineers reviewed, identified flaws, and corrected AI network recommendations.
          </p>
        </div>

        <button
          onClick={handleSeed}
          disabled={seeding}
          className="flex items-center space-x-1.5 px-3 py-1.5 bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 border border-indigo-500/30 rounded-lg text-xs font-medium transition"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${seeding ? 'animate-spin' : ''}`} />
          <span>Reload Seeded Corrections</span>
        </button>
      </div>

      {/* Governance Banner */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 space-y-2">
        <h3 className="text-xs uppercase font-bold tracking-wider text-sky-400">
          The Human Oversight Principle in Network Engineering
        </h3>
        <p className="text-xs text-slate-300 leading-relaxed">
          In mission-critical enterprise infrastructure, automated AI generation must never apply unverified configuration changes autonomously.
          The NetSage AI framework enforces a four-stage audit lifecycle:
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-2 pt-2 text-center text-xs font-semibold">
          <div className="p-2.5 bg-slate-950 rounded-lg border border-slate-800 text-indigo-300">
            1. AI Recommends
          </div>
          <div className="p-2.5 bg-slate-950 rounded-lg border border-slate-800 text-amber-300">
            2. Human Identifies Problem
          </div>
          <div className="p-2.5 bg-slate-950 rounded-lg border border-slate-800 text-blue-300">
            3. Human Correction
          </div>
          <div className="p-2.5 bg-slate-950 rounded-lg border border-slate-800 text-emerald-300">
            4. Final Verified Diagnosis
          </div>
        </div>
      </div>

      {/* Records Feed */}
      {loading ? (
        <div className="p-8 text-center text-slate-400">Loading audit records...</div>
      ) : records.length === 0 ? (
        <div className="p-8 text-center text-slate-400 bg-slate-900/40 rounded-xl border border-slate-800 space-y-3">
          <p>No Responsible AI corrections logged yet.</p>
          <button
            onClick={handleSeed}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-semibold"
          >
            Seed 5 Authentic Case Corrections
          </button>
        </div>
      ) : (
        <div className="space-y-6">
          {records.map((rec, idx) => (
            <div 
              key={rec.review_id || idx}
              className="bg-slate-900/80 border border-slate-800 rounded-xl overflow-hidden shadow-xl"
            >
              {/* Record Header */}
              <div className="bg-slate-950/80 px-5 py-3 border-b border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div className="flex items-center space-x-3">
                  <span className="font-mono font-bold text-sky-400 text-xs">{rec.case_id}</span>
                  <h4 className="text-sm font-bold text-white">{rec.case_title}</h4>
                </div>
                <div className="flex items-center space-x-2 text-xs">
                  <span className="px-2.5 py-0.5 rounded bg-blue-500/20 text-blue-300 font-bold border border-blue-500/30">
                    {rec.decision}
                  </span>
                  <span className="text-slate-400 text-[11px]">By {rec.reviewer_name}</span>
                </div>
              </div>

              {/* Four-Stage Flow Card Body */}
              <div className="p-5 space-y-4 text-xs">
                {/* 1. AI Initial Recommendation */}
                <div className="p-3.5 bg-indigo-950/20 border border-indigo-500/30 rounded-lg space-y-1.5">
                  <div className="flex items-center justify-between text-indigo-400 font-bold">
                    <span>1. AI Initial Proposal:</span>
                    <span className="text-[11px] font-mono">Confidence: {Math.round(rec.ai_diagnosis.confidence * 100)}%</span>
                  </div>
                  <p className="text-slate-200 font-medium">{rec.ai_diagnosis.root_cause}</p>
                  {rec.ai_diagnosis.fix_steps?.length > 0 && (
                    <div className="font-mono text-[11px] text-slate-400 bg-slate-950 p-2 rounded">
                      {rec.ai_diagnosis.fix_steps.map((cmd, i) => <div key={i}>$ {cmd}</div>)}
                    </div>
                  )}
                </div>

                {/* Arrow indicator */}
                <div className="flex justify-center text-slate-600">
                  <ArrowDown className="w-4 h-4" />
                </div>

                {/* 2. Human Identifies Problem */}
                <div className="p-3.5 bg-amber-950/20 border border-amber-500/30 rounded-lg space-y-1">
                  <div className="flex items-center space-x-1.5 text-amber-400 font-bold">
                    <AlertCircle className="w-4 h-4" />
                    <span>2. Reviewer Identifies Problem in AI Diagnosis:</span>
                  </div>
                  <p className="text-amber-200/90 leading-relaxed font-medium">
                    {rec.why_ai_incorrect}
                  </p>
                </div>

                {/* Arrow indicator */}
                <div className="flex justify-center text-slate-600">
                  <ArrowDown className="w-4 h-4" />
                </div>

                {/* 3 & 4. Human Correction and Final Diagnosis */}
                <div className="p-3.5 bg-emerald-950/20 border border-emerald-500/30 rounded-lg space-y-2">
                  <div className="flex items-center justify-between text-emerald-400 font-bold">
                    <div className="flex items-center space-x-1.5">
                      <CheckCircle2 className="w-4 h-4" />
                      <span>3 & 4. Human-Corrected Final Remediation:</span>
                    </div>
                    <span className="text-[11px] text-emerald-300 font-mono">Validated by Engineer</span>
                  </div>
                  <p className="text-slate-100 font-semibold">{rec.human_correction.root_cause}</p>
                  
                  {rec.human_correction.fix_steps?.length > 0 && (
                    <div className="font-mono text-[11px] text-emerald-300 bg-slate-950 p-2 rounded border border-emerald-500/30">
                      {rec.human_correction.fix_steps.map((cmd, i) => <div key={i}>$ {cmd}</div>)}
                    </div>
                  )}

                  <div className="text-[11px] text-slate-400 pt-1 border-t border-slate-800">
                    <strong>Reviewer Justification:</strong> {rec.reviewer_notes}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
