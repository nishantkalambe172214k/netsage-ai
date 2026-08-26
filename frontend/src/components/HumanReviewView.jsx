import React, { useEffect, useState } from 'react';
import { getCases, getCaseDetail, submitReview, getCaseReviews } from '../services/api';
import { 
  UserCheck, CheckCircle2, Edit3, XCircle, ShieldCheck, 
  Terminal, Layers, AlertTriangle, ArrowRight, Clock, HelpCircle 
} from 'lucide-react';
import VerificationModal from './VerificationModal';

export default function HumanReviewView({ selectedCaseId, onNavigateToVerification }) {
  const [cases, setCases] = useState([]);
  const [currentCaseId, setCurrentCaseId] = useState(selectedCaseId || 'CASE-VLAN-001');
  const [caseData, setCaseData] = useState(null);
  const [reviews, setReviews] = useState([]);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  // Review Form States
  const [decisionMode, setDecisionMode] = useState('ACCEPT'); // 'ACCEPT', 'EDIT', 'REJECT'
  const [reviewerName, setReviewerName] = useState('Senior Network Engineer');
  const [reviewNotes, setReviewNotes] = useState('');
  const [rejectionReason, setRejectionReason] = useState('');
  const [whyAiIncorrect, setWhyAiIncorrect] = useState('');

  // Editable fields for EDIT mode
  const [editRootCause, setEditRootCause] = useState('');
  const [editConfidence, setEditConfidence] = useState(0.98);
  const [editOsiLayer, setEditOsiLayer] = useState('Layer 3 - Network');
  const [editNextCommand, setEditNextCommand] = useState('show running-config');
  const [editFixSteps, setEditFixSteps] = useState('');

  // Verification modal state
  const [showVerifyModal, setShowVerifyModal] = useState(false);

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

  const loadCaseAndReviews = async (id) => {
    try {
      setLoading(true);
      const c = await getCaseDetail(id);
      setCaseData(c);
      const revs = await getCaseReviews(id);
      setReviews(revs);

      // Pre-fill editable fields with AI diagnosis
      const latestDiag = c.diagnoses?.[0];
      if (latestDiag) {
        setEditRootCause(latestDiag.root_cause || '');
        setEditConfidence(latestDiag.confidence_score || latestDiag.confidence || 0.95);
        setEditOsiLayer(latestDiag.osi_layer || 'Layer 3 - Network');
        setEditNextCommand(latestDiag.next_command || 'show running-config');
        setEditFixSteps(
          Array.isArray(latestDiag.fix_steps) ? latestDiag.fix_steps.join('\n') : latestDiag.fix_steps || ''
        );
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (currentCaseId) {
      loadCaseAndReviews(currentCaseId);
    }
  }, [currentCaseId]);

  const formatErrorMessage = (err) => {
    const detail = err.response?.data?.detail;
    if (!detail) return err.message || 'An unexpected error occurred';
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail)) {
      return detail.map((d) => d.msg || d.message || JSON.stringify(d)).join('; ');
    }
    if (typeof detail === 'object') {
      return detail.msg || detail.message || JSON.stringify(detail);
    }
    return String(detail);
  };

  const handleReviewSubmit = async () => {
    try {
      setSubmitting(true);
      const latestDiag = caseData?.diagnoses?.[0];

      if (decisionMode === 'EDIT' && !reviewNotes.trim()) {
        alert('Reviewer notes/explanation is required when submitting an EDITED diagnosis.');
        setSubmitting(false);
        return;
      }

      if (decisionMode === 'REJECT' && !rejectionReason.trim()) {
        alert('A rejection reason is required when REJECTING an AI diagnosis.');
        setSubmitting(false);
        return;
      }

      // Explicitly map decisionMode to canonical backend enum: ACCEPTED, EDITED, REJECTED
      let decisionEnum = 'ACCEPTED';
      if (decisionMode === 'EDIT') decisionEnum = 'EDITED';
      else if (decisionMode === 'REJECT') decisionEnum = 'REJECTED';

      const payload = {
        reviewer_name: reviewerName || 'Network Engineer',
        decision: decisionEnum,
        original_diagnosis: latestDiag ? {
          root_cause: latestDiag.root_cause,
          confidence: latestDiag.confidence_score || latestDiag.confidence || 0.95,
          osi_layer: latestDiag.osi_layer,
          evidence: latestDiag.evidence,
          next_command: latestDiag.next_command,
          fix_steps: latestDiag.fix_steps
        } : {},
        corrected_diagnosis: decisionEnum === 'EDITED' ? {
          root_cause: editRootCause || 'Human-corrected root cause',
          confidence: parseFloat(editConfidence) || 0.98,
          osi_layer: editOsiLayer || 'Layer 3 - Network',
          next_command: editNextCommand || 'show running-config',
          fix_steps: editFixSteps ? editFixSteps.split('\n').filter((s) => s.trim().length > 0) : []
        } : {},
        review_notes: decisionEnum === 'EDITED' ? reviewNotes : (reviewNotes || 'Human approved fix.'),
        rejection_reason: decisionEnum === 'REJECTED' ? rejectionReason : null,
        why_ai_incorrect: whyAiIncorrect || (decisionEnum === 'EDITED' ? reviewNotes : null),
        modified_commands: decisionEnum === 'EDITED' && editFixSteps ? [
          { device: 'R1', commands: editFixSteps.split('\n').filter((s) => s.trim().length > 0) }
        ] : []
      };

      await submitReview(currentCaseId, payload);
      await loadCaseAndReviews(currentCaseId);
      alert(`Human review submitted successfully: ${payload.decision}`);
    } catch (err) {
      alert('Error submitting review: ' + formatErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  };


  const latestDiag = caseData?.diagnoses?.[0];
  const ruleFindings = caseData?.rule_findings || [];
  const latestReview = reviews[0];

  return (
    <div className="space-y-6 max-w-7xl mx-auto p-6">
      {/* Case Header */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-lg flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="space-y-1.5 flex-1">
          <div className="flex items-center gap-2">
            <span className="text-xs uppercase font-bold text-amber-400 font-mono">Mandatory Human Review Gate</span>
            <select
              value={currentCaseId}
              onChange={(e) => setCurrentCaseId(e.target.value)}
              className="bg-slate-950 border border-slate-700 text-white text-xs font-semibold rounded-lg px-3 py-1.5 focus:outline-none focus:border-amber-500"
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

        {/* Verification Action */}
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setShowVerifyModal(true)}
            className="px-4 py-2 bg-teal-600 hover:bg-teal-500 text-white font-semibold rounded-lg text-xs flex items-center gap-2 shadow-md transition"
          >
            <ShieldCheck className="w-4 h-4" />
            <span>Record Verification</span>
          </button>
        </div>
      </div>

      {/* Side-by-Side Review Workspace */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Case Evidence, Rules & AI Diagnosis (5 cols) */}
        <div className="lg:col-span-5 space-y-4">
          {/* AI Recommendation Summary */}
          <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-5 space-y-3 shadow-md">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-indigo-400">AI Diagnostic Proposal</span>
              {latestDiag && (
                <span className="text-[11px] px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 font-semibold">
                  {Math.round((latestDiag.confidence_score || latestDiag.confidence || 0) * 100)}% Confidence
                </span>
              )}
            </div>

            {!latestDiag ? (
              <p className="text-xs text-slate-500">No AI diagnosis present. Run analysis in Troubleshoot tab first.</p>
            ) : (
              <div className="space-y-3 text-xs">
                <div>
                  <span className="text-slate-400 font-medium">Root Cause:</span>
                  <p className="text-white font-semibold mt-0.5">{latestDiag.root_cause}</p>
                </div>
                <div className="grid grid-cols-2 gap-2 text-[11px]">
                  <div className="p-2 bg-slate-950 rounded border border-slate-800">
                    <span className="text-slate-500 block">OSI Layer</span>
                    <span className="text-sky-300 font-semibold">{latestDiag.osi_layer || 'Layer 3'}</span>
                  </div>
                  <div className="p-2 bg-slate-950 rounded border border-slate-800">
                    <span className="text-slate-500 block">Next Command</span>
                    <span className="text-emerald-300 font-mono">{latestDiag.next_command || 'show run'}</span>
                  </div>
                </div>
                <div>
                  <span className="text-slate-400 font-medium">Proposed Fix Steps:</span>
                  <div className="bg-slate-950 p-2.5 rounded border border-slate-800 font-mono text-[11px] text-emerald-400 space-y-0.5 mt-1">
                    {latestDiag.fix_steps?.map((step, idx) => (
                      <div key={idx}>$ {step}</div>
                    )) || <div>$ {latestDiag.root_cause}</div>}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Python Rule Checker Evidence */}
          <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-5 space-y-3 shadow-md">
            <span className="text-xs font-bold uppercase tracking-wider text-amber-400">Deterministic Rule Evidence</span>
            {ruleFindings.length === 0 ? (
              <p className="text-xs text-slate-500">No rule violations flagged.</p>
            ) : (
              <div className="space-y-2">
                {ruleFindings.map((rf, i) => (
                  <div key={i} className="p-2.5 bg-slate-950/70 rounded border border-slate-800 text-xs space-y-1">
                    <div className="flex justify-between font-mono font-bold text-amber-300">
                      <span>{rf.rule_id}</span>
                      <span className="text-[10px] uppercase text-rose-400">{rf.severity}</span>
                    </div>
                    <p className="text-slate-300 text-[11px]">{rf.message}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Human Review Action Console (7 cols) */}
        <div className="lg:col-span-7 space-y-4">
          <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-6 space-y-5 shadow-xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center space-x-2 text-white font-bold text-sm">
                <UserCheck className="w-5 h-5 text-sky-400" />
                <h3>Reviewer Decision Console</h3>
              </div>
              <span className="text-xs text-slate-400">Reviewer: {reviewerName}</span>
            </div>

            {/* Decision Action Tabs: ACCEPT / EDIT / REJECT */}
            <div className="grid grid-cols-3 gap-2 bg-slate-950 p-1.5 rounded-xl border border-slate-800">
              <button
                type="button"
                onClick={() => setDecisionMode('ACCEPT')}
                className={`py-2 px-3 rounded-lg text-xs font-bold flex items-center justify-center gap-1.5 transition ${
                  decisionMode === 'ACCEPT'
                    ? 'bg-emerald-600 text-white shadow-md'
                    : 'text-slate-400 hover:text-emerald-300 hover:bg-slate-900'
                }`}
              >
                <CheckCircle2 className="w-4 h-4" />
                <span>ACCEPT</span>
              </button>

              <button
                type="button"
                onClick={() => setDecisionMode('EDIT')}
                className={`py-2 px-3 rounded-lg text-xs font-bold flex items-center justify-center gap-1.5 transition ${
                  decisionMode === 'EDIT'
                    ? 'bg-blue-600 text-white shadow-md'
                    : 'text-slate-400 hover:text-blue-300 hover:bg-slate-900'
                }`}
              >
                <Edit3 className="w-4 h-4" />
                <span>EDIT</span>
              </button>

              <button
                type="button"
                onClick={() => setDecisionMode('REJECT')}
                className={`py-2 px-3 rounded-lg text-xs font-bold flex items-center justify-center gap-1.5 transition ${
                  decisionMode === 'REJECT'
                    ? 'bg-rose-600 text-white shadow-md'
                    : 'text-slate-400 hover:text-rose-300 hover:bg-slate-900'
                }`}
              >
                <XCircle className="w-4 h-4" />
                <span>REJECT</span>
              </button>
            </div>

            {/* Decision Specific Form Inputs */}
            {decisionMode === 'ACCEPT' && (
              <div className="space-y-3 text-xs">
                <div className="p-3.5 bg-emerald-950/20 border border-emerald-500/30 rounded-lg text-emerald-300">
                  <strong>Accept AI Diagnosis:</strong> Confirms the proposed root cause and remediation commands without modification.
                </div>
                <div>
                  <label className="block text-slate-400 mb-1 font-semibold">Reviewer Notes (Optional):</label>
                  <textarea
                    rows={3}
                    value={reviewNotes}
                    onChange={(e) => setReviewNotes(e.target.value)}
                    placeholder="Enter validation notes or approval remarks..."
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-white focus:outline-none focus:border-emerald-500"
                  />
                </div>
              </div>
            )}

            {decisionMode === 'EDIT' && (
              <div className="space-y-4 text-xs">
                <div className="p-3.5 bg-blue-950/20 border border-blue-500/30 rounded-lg text-blue-300">
                  <strong>Human Correction Mode:</strong> Modify the root cause, OSI layer, or remediation commands. Requires explanation.
                </div>

                <div>
                  <label className="block text-slate-400 mb-1 font-semibold">Human-Corrected Root Cause:</label>
                  <input
                    type="text"
                    value={editRootCause}
                    onChange={(e) => setEditRootCause(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-white focus:outline-none focus:border-blue-500"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-slate-400 mb-1 font-semibold">Corrected OSI Layer:</label>
                    <select
                      value={editOsiLayer}
                      onChange={(e) => setEditOsiLayer(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-white focus:outline-none focus:border-blue-500"
                    >
                      <option>Layer 1 - Physical</option>
                      <option>Layer 2 - Data Link</option>
                      <option>Layer 3 - Network</option>
                      <option>Layer 4 - Transport</option>
                      <option>Layer 7 - Application</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-slate-400 mb-1 font-semibold">Next Command:</label>
                    <input
                      type="text"
                      value={editNextCommand}
                      onChange={(e) => setEditNextCommand(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-white font-mono focus:outline-none focus:border-blue-500"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-slate-400 mb-1 font-semibold">Corrected CLI Fix Steps (one per line):</label>
                  <textarea
                    rows={3}
                    value={editFixSteps}
                    onChange={(e) => setEditFixSteps(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-white font-mono text-[11px] focus:outline-none focus:border-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-slate-300 mb-1 font-semibold text-rose-300">
                    * Why AI Was Incorrect / Reviewer Explanation (Mandatory):
                  </label>
                  <textarea
                    rows={2}
                    value={reviewNotes}
                    onChange={(e) => {
                      setReviewNotes(e.target.value);
                      setWhyAiIncorrect(e.target.value);
                    }}
                    placeholder="Explain why the AI proposal was incomplete/inaccurate and how this correction resolves the fault..."
                    className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2.5 text-white focus:outline-none focus:border-blue-500"
                  />
                </div>
              </div>
            )}

            {decisionMode === 'REJECT' && (
              <div className="space-y-3 text-xs">
                <div className="p-3.5 bg-rose-950/20 border border-rose-500/30 rounded-lg text-rose-300">
                  <strong>Reject Diagnosis:</strong> Marks the AI diagnosis as invalid or hazardous. Overrules remediation.
                </div>
                <div>
                  <label className="block text-slate-300 mb-1 font-semibold text-rose-300">
                    * Rejection Reason (Mandatory):
                  </label>
                  <textarea
                    rows={3}
                    value={rejectionReason}
                    onChange={(e) => {
                      setRejectionReason(e.target.value);
                      setReviewNotes(e.target.value);
                    }}
                    placeholder="Provide specific technical justification for rejecting this diagnosis..."
                    className="w-full bg-slate-950 border border-slate-700 rounded-lg p-3 text-white focus:outline-none focus:border-rose-500"
                  />
                </div>
              </div>
            )}

            {/* Reviewer Signature & Submit */}
            <div className="pt-3 border-t border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div className="flex items-center space-x-2 text-xs">
                <span className="text-slate-400">Reviewer Name:</span>
                <input
                  type="text"
                  value={reviewerName}
                  onChange={(e) => setReviewerName(e.target.value)}
                  className="bg-slate-950 border border-slate-800 rounded px-2.5 py-1 text-white text-xs focus:outline-none focus:border-sky-500"
                />
              </div>
              <button
                type="button"
                onClick={handleReviewSubmit}
                disabled={submitting}
                className="px-5 py-2 bg-gradient-to-r from-sky-600 to-indigo-600 hover:from-sky-500 hover:to-indigo-500 text-white font-bold rounded-lg text-xs shadow-lg transition"
              >
                {submitting ? 'Submitting...' : `Submit Review: ${decisionMode}`}
              </button>
            </div>
          </div>

          {/* Review Audit History */}
          {reviews.length > 0 && (
            <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-5 space-y-3 shadow-md">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Human Review Audit History</span>
              <div className="space-y-2.5">
                {reviews.map((r) => (
                  <div key={r.id} className="p-3 bg-slate-950/70 rounded-lg border border-slate-800 text-xs space-y-1">
                    <div className="flex justify-between items-center">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        r.decision === 'ACCEPTED' ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' :
                        r.decision === 'EDITED' ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30' :
                        'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                      }`}>
                        {r.decision}
                      </span>
                      <span className="text-slate-500 text-[10px]">{new Date(r.reviewed_at).toLocaleString()}</span>
                    </div>
                    <p className="text-slate-200 font-medium">Reviewer: {r.reviewer_name}</p>
                    <p className="text-slate-400 text-[11px] italic">{r.review_notes || r.rejection_reason}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Verification Modal */}
      {showVerifyModal && (
        <VerificationModal
          caseId={currentCaseId}
          caseTitle={caseData?.title}
          latestReview={latestReview}
          onClose={() => setShowVerifyModal(false)}
          onSuccess={() => {
            setShowVerifyModal(false);
            loadCaseAndReviews(currentCaseId);
          }}
        />
      )}
    </div>
  );
}
