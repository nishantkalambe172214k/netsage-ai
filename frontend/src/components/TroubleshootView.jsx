import React, { useEffect, useState } from 'react';
import { 
  getCases, getCaseDetail, runRuleCheck, runAIDiagnosis, runCaseAnalysis 
} from '../services/api';
import { 
  Wrench, Cpu, ShieldAlert, CheckCircle2, AlertTriangle, ArrowRight, 
  Terminal, Layers, RefreshCw, UserCheck, Activity, HelpCircle 
} from 'lucide-react';

export default function TroubleshootView({ selectedCaseId, onNavigateToReview, onNavigateToVerification }) {
  const [cases, setCases] = useState([]);
  const [currentCaseId, setCurrentCaseId] = useState(selectedCaseId || 'CASE-VLAN-001');
  const [caseData, setCaseData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);

  useEffect(() => {
    async function init() {
      try {
        const allCases = await getCases();
        setCases(allCases);
        if (selectedCaseId) {
          setCurrentCaseId(selectedCaseId);
        } else if (allCases.length > 0) {
          setCurrentCaseId(allCases[0].case_id);
        }
      } catch (err) {
        console.error(err);
      }
    }
    init();
  }, [selectedCaseId]);

  const loadCaseDetail = async (id) => {
    try {
      setLoading(true);
      const data = await getCaseDetail(id);
      setCaseData(data);
      setAnalysisResult(null);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (currentCaseId) {
      loadCaseDetail(currentCaseId);
    }
  }, [currentCaseId]);

  const handleRunAnalysis = async () => {
    try {
      setActionLoading(true);
      const res = await runCaseAnalysis(currentCaseId);
      setAnalysisResult(res);
      await loadCaseDetail(currentCaseId);
    } catch (err) {
      alert('Error running analysis: ' + err.message);
    } finally {
      setActionLoading(false);
    }
  };

  const handleRunRules = async () => {
    try {
      setActionLoading(true);
      await runRuleCheck(currentCaseId);
      await loadCaseDetail(currentCaseId);
    } catch (err) {
      alert('Error running rule check: ' + err.message);
    } finally {
      setActionLoading(false);
    }
  };

  const handleRunAIDiagnosis = async () => {
    try {
      setActionLoading(true);
      await runAIDiagnosis(currentCaseId);
      await loadCaseDetail(currentCaseId);
    } catch (err) {
      alert('Error running AI diagnosis: ' + err.message);
    } finally {
      setActionLoading(false);
    }
  };

  const latestDiagnosis = caseData?.diagnoses?.[0];
  const latestReview = caseData?.reviews?.[0];
  const latestVerification = caseData?.verification_results?.[0];
  const ruleFindings = caseData?.rule_findings || [];

  return (
    <div className="space-y-6 max-w-7xl mx-auto p-6">
      {/* Case Selector and Status Header */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-lg flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="space-y-1.5 flex-1">
          <div className="flex items-center gap-2">
            <span className="text-xs uppercase font-bold text-sky-400 font-mono">Case Workbench</span>
            <select
              value={currentCaseId}
              onChange={(e) => setCurrentCaseId(e.target.value)}
              className="bg-slate-950 border border-slate-700 text-white text-xs font-semibold rounded-lg px-3 py-1.5 focus:outline-none focus:border-sky-500"
            >
              {cases.map((c) => (
                <option key={c.case_id} value={c.case_id}>
                  {c.case_id} — {c.title}
                </option>
              ))}
            </select>
          </div>
          <h2 className="text-lg font-bold text-white tracking-tight">{caseData?.title}</h2>
          <p className="text-xs text-slate-400 whitespace-pre-line">{caseData?.description}</p>
        </div>

        {/* Action Controls */}
        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={handleRunRules}
            disabled={actionLoading}
            className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-lg text-xs font-medium transition flex items-center gap-1.5"
          >
            <ShieldAlert className="w-3.5 h-3.5 text-amber-400" />
            <span>Check Python Rules</span>
          </button>
          <button
            onClick={handleRunAIDiagnosis}
            disabled={actionLoading}
            className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-lg text-xs font-medium transition flex items-center gap-1.5"
          >
            <Cpu className="w-3.5 h-3.5 text-indigo-400" />
            <span>AI Diagnosis</span>
          </button>
          <button
            onClick={handleRunAnalysis}
            disabled={actionLoading}
            className="px-4 py-1.5 bg-sky-600 hover:bg-sky-500 text-white rounded-lg text-xs font-semibold shadow-md transition flex items-center gap-1.5"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${actionLoading ? 'animate-spin' : ''}`} />
            <span>Run Complete Pipeline</span>
          </button>
        </div>
      </div>

      {/* Human Oversight Banner */}
      <div className="bg-amber-500/10 border border-amber-500/30 rounded-xl p-3.5 flex items-center justify-between text-xs text-amber-300">
        <div className="flex items-center space-x-2">
          <UserCheck className="w-4 h-4 text-amber-400 flex-shrink-0" />
          <span>
            <strong>Mandatory Human Review Gate:</strong> AI diagnoses and Python rule recommendations are advisory. A human engineer must review and approve before remediation can be applied or verified.
          </span>
        </div>
        <button
          onClick={() => onNavigateToReview(currentCaseId)}
          className="px-3 py-1 bg-amber-500/20 hover:bg-amber-500/30 text-amber-200 border border-amber-500/40 rounded-lg text-xs font-semibold flex items-center gap-1 transition ml-3 whitespace-nowrap"
        >
          <span>Review Console</span>
          <ArrowRight className="w-3 h-3" />
        </button>
      </div>

      {/* Main Analysis Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Python Rule Engine Findings (5 cols) */}
        <div className="lg:col-span-5 space-y-4">
          <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-5 space-y-4 shadow-md">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2 text-amber-400 font-bold text-sm">
                <ShieldAlert className="w-4 h-4" />
                <h3>Python Deterministic Rules</h3>
              </div>
              <span className="text-[11px] px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono">
                {ruleFindings.length} Finding(s)
              </span>
            </div>

            {ruleFindings.length === 0 ? (
              <div className="p-6 text-center text-slate-500 bg-slate-950/40 rounded-lg border border-slate-800 text-xs">
                No rule findings logged yet. Click "Check Python Rules" to scan Cisco configs.
              </div>
            ) : (
              <div className="space-y-3">
                {ruleFindings.map((rf) => (
                  <div 
                    key={rf.id || rf.rule_id} 
                    className="p-3.5 rounded-lg bg-slate-950/60 border border-slate-800 space-y-1.5"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-white font-mono">{rf.rule_id}</span>
                      <span className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded ${
                        rf.severity === 'CRITICAL' ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30' : 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                      }`}>
                        {rf.severity}
                      </span>
                    </div>
                    <p className="text-xs text-slate-200 font-medium">{rf.rule_name}</p>
                    <p className="text-[11px] text-slate-400 leading-relaxed">{rf.message}</p>
                    {(rf.affected_device || rf.affected_interface) && (
                      <div className="text-[10px] text-slate-500 font-mono pt-1">
                        Target: {rf.affected_device} &bull; {rf.affected_interface}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Raw Configuration Inspection */}
          <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-5 space-y-3 shadow-md">
            <div className="flex items-center space-x-2 text-slate-300 font-bold text-xs uppercase tracking-wider">
              <Terminal className="w-4 h-4 text-sky-400" />
              <h4>Cisco IOS Config / Show Command Dumps</h4>
            </div>
            <div className="space-y-2 max-h-64 overflow-y-auto font-mono text-[11px] bg-slate-950 p-3 rounded-lg border border-slate-800">
              {caseData?.raw_configs && Object.keys(caseData.raw_configs).length > 0 ? (
                Object.entries(caseData.raw_configs).map(([dev, conf]) => (
                  <div key={dev} className="space-y-1">
                    <span className="text-sky-400 font-bold"># {dev} Running Config:</span>
                    <pre className="text-slate-300 whitespace-pre-wrap">{conf}</pre>
                  </div>
                ))
              ) : (
                <div className="text-slate-500">No raw configs attached.</div>
              )}
            </div>
          </div>
        </div>

        {/* Right Column: AI Diagnosis & Synthesis (7 cols) */}
        <div className="lg:col-span-7 space-y-4">
          <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-5 space-y-5 shadow-md">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2 text-indigo-400 font-bold text-sm">
                <Cpu className="w-4 h-4" />
                <h3>AI Diagnostic Synthesis</h3>
              </div>
              {latestDiagnosis && (
                <div className="flex items-center space-x-2">
                  <span className="text-[11px] px-2.5 py-0.5 rounded bg-indigo-500/20 text-indigo-300 font-semibold border border-indigo-500/30">
                    Confidence: {Math.round((latestDiagnosis.confidence_score || latestDiagnosis.confidence || 0) * 100)}%
                  </span>
                  <span className="text-[11px] px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono">
                    {latestDiagnosis.model_name || 'mock-ai-engine'}
                  </span>
                </div>
              )}
            </div>

            {!latestDiagnosis ? (
              <div className="p-8 text-center text-slate-500 bg-slate-950/40 rounded-lg border border-slate-800 text-xs">
                No AI diagnosis generated yet. Click "Run Complete Pipeline" to analyze.
              </div>
            ) : (
              <div className="space-y-4 text-xs">
                {/* Root Cause */}
                <div className="p-3.5 rounded-lg bg-indigo-950/30 border border-indigo-500/30 space-y-1">
                  <span className="text-[10px] uppercase font-bold text-indigo-400 tracking-wider">Root Cause Analysis</span>
                  <p className="text-sm font-semibold text-white leading-snug">{latestDiagnosis.root_cause}</p>
                  <p className="text-slate-400 text-xs mt-1">{latestDiagnosis.explanation}</p>
                </div>

                {/* Metadata Grid: OSI Layer & Diagnostic Command */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div className="p-3 rounded-lg bg-slate-950/50 border border-slate-800 space-y-1">
                    <span className="text-[10px] uppercase text-slate-400 font-semibold">Identified OSI Layer</span>
                    <div className="text-xs font-bold text-sky-300 flex items-center gap-1.5">
                      <Layers className="w-3.5 h-3.5" />
                      <span>{latestDiagnosis.osi_layer || 'Layer 3 - Network'}</span>
                    </div>
                  </div>
                  <div className="p-3 rounded-lg bg-slate-950/50 border border-slate-800 space-y-1">
                    <span className="text-[10px] uppercase text-slate-400 font-semibold">Recommended CLI Command</span>
                    <div className="text-xs font-mono font-bold text-emerald-400 flex items-center gap-1.5">
                      <Terminal className="w-3.5 h-3.5" />
                      <span>{latestDiagnosis.next_command || 'show running-config'}</span>
                    </div>
                  </div>
                </div>

                {/* Evidence Observations */}
                {latestDiagnosis.evidence && latestDiagnosis.evidence.length > 0 && (
                  <div className="space-y-1.5">
                    <span className="text-[10px] uppercase text-slate-400 font-semibold">Diagnostic Evidence</span>
                    <ul className="list-disc list-inside space-y-1 text-slate-300 bg-slate-950/40 p-3 rounded-lg border border-slate-800">
                      {latestDiagnosis.evidence.map((ev, i) => (
                        <li key={i} className="text-[11px]">{ev}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Suggested Fix Steps */}
                <div className="space-y-1.5">
                  <span className="text-[10px] uppercase text-slate-400 font-semibold">Proposed Remediation CLI Commands</span>
                  <div className="bg-slate-950 p-3 rounded-lg border border-slate-800 font-mono text-[11px] text-emerald-300 space-y-1">
                    {latestDiagnosis.fix_steps && latestDiagnosis.fix_steps.length > 0 ? (
                      latestDiagnosis.fix_steps.map((step, idx) => (
                        <div key={idx}>$ {step}</div>
                      ))
                    ) : (
                      <div>$ {latestDiagnosis.root_cause}</div>
                    )}
                  </div>
                </div>

                {/* Comparison Consensus */}
                {analysisResult?.comparison && (
                  <div className="p-3.5 rounded-lg bg-slate-950 border border-purple-500/30 space-y-1.5">
                    <div className="flex items-center justify-between text-purple-400 font-semibold">
                      <span className="text-[11px] uppercase">AI vs Python Rule Alignment</span>
                      <span className="text-xs font-bold font-mono">
                        {analysisResult.comparison.status} ({Math.round(analysisResult.comparison.alignment_score * 100)}%)
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-300">{analysisResult.comparison.consensus_recommendation}</p>
                  </div>
                )}

                {/* Action to Human Review */}
                <div className="pt-2 flex justify-end">
                  <button
                    onClick={() => onNavigateToReview(currentCaseId)}
                    className="px-4 py-2 bg-gradient-to-r from-sky-600 to-indigo-600 hover:from-sky-500 hover:to-indigo-500 text-white font-semibold rounded-lg text-xs flex items-center gap-2 shadow-lg transition"
                  >
                    <UserCheck className="w-4 h-4" />
                    <span>Proceed to Mandatory Human Review</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
