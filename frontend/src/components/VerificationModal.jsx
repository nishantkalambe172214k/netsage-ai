import React, { useState } from 'react';
import { submitVerification } from '../services/api';
import { ShieldCheck, CheckCircle2, XCircle, AlertTriangle, X } from 'lucide-react';

export default function VerificationModal({ caseId, caseTitle, latestReview, onClose, onSuccess }) {
  const [status, setStatus] = useState('PASSED');
  const [testSummary, setTestSummary] = useState(
    'Simulated ICMP ping test and show command verification completed in Packet Tracer with 100% packet delivery.'
  );
  const [notes, setNotes] = useState('Verified end-to-end connectivity following approved remediation.');
  const [evidencePing, setEvidencePing] = useState('5/5 packets received, 0% packet loss.');
  const [submitting, setSubmitting] = useState(false);

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

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      setSubmitting(true);
      const payload = {
        status: status,
        test_summary: testSummary,
        notes: notes,
        verification_evidence: {
          ping_result: evidencePing,
          verified_by: latestReview?.reviewer_name || 'Network Engineer',
          review_decision: latestReview?.decision || 'ACCEPTED'
        }
      };

      await submitVerification(caseId, payload);
      alert(`Verification recorded as: ${status}`);
      onSuccess();
    } catch (err) {
      alert('Error recording verification: ' + formatErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  };


  const finalFixSteps = latestReview?.decision === 'EDITED' && latestReview?.corrected_diagnosis?.fix_steps?.length > 0
    ? latestReview.corrected_diagnosis.fix_steps
    : latestReview?.original_diagnosis?.fix_steps || [];

  return (
    <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-slate-700 rounded-xl w-full max-w-xl shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-3.5 border-b border-slate-800 bg-slate-950/60">
          <div className="flex items-center space-x-2">
            <ShieldCheck className="w-5 h-5 text-teal-400" />
            <h3 className="text-sm font-bold text-white">Post-Remediation Verification Recording</h3>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-white transition">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content */}
        <form onSubmit={handleSubmit} className="p-5 space-y-4 text-xs">
          <div>
            <span className="text-slate-400 font-mono text-[11px] block">{caseId}</span>
            <h4 className="text-sm font-bold text-slate-100">{caseTitle}</h4>
          </div>

          {/* Approved Fix Steps Display */}
          <div className="p-3 bg-slate-950 rounded-lg border border-slate-800 space-y-1">
            <span className="text-[10px] uppercase font-bold text-slate-400">Approved Remediation Commands Applied:</span>
            <div className="font-mono text-[11px] text-emerald-400 space-y-0.5">
              {finalFixSteps.length > 0 ? (
                finalFixSteps.map((step, i) => <div key={i}>$ {step}</div>)
              ) : (
                <div>$ Verified configuration applied</div>
              )}
            </div>
          </div>

          {/* Verification Status Selector */}
          <div>
            <label className="block text-slate-300 font-semibold mb-1.5">Verification Outcome:</label>
            <div className="grid grid-cols-3 gap-2">
              <button
                type="button"
                onClick={() => setStatus('PASSED')}
                className={`py-2 px-3 rounded-lg font-bold flex items-center justify-center gap-1.5 border transition ${
                  status === 'PASSED'
                    ? 'bg-teal-600/30 text-teal-300 border-teal-500'
                    : 'bg-slate-950 text-slate-400 border-slate-800 hover:bg-slate-800'
                }`}
              >
                <CheckCircle2 className="w-4 h-4 text-teal-400" />
                <span>PASSED</span>
              </button>

              <button
                type="button"
                onClick={() => setStatus('PARTIAL')}
                className={`py-2 px-3 rounded-lg font-bold flex items-center justify-center gap-1.5 border transition ${
                  status === 'PARTIAL'
                    ? 'bg-amber-600/30 text-amber-300 border-amber-500'
                    : 'bg-slate-950 text-slate-400 border-slate-800 hover:bg-slate-800'
                }`}
              >
                <AlertTriangle className="w-4 h-4 text-amber-400" />
                <span>PARTIAL</span>
              </button>

              <button
                type="button"
                onClick={() => setStatus('FAILED')}
                className={`py-2 px-3 rounded-lg font-bold flex items-center justify-center gap-1.5 border transition ${
                  status === 'FAILED'
                    ? 'bg-rose-600/30 text-rose-300 border-rose-500'
                    : 'bg-slate-950 text-slate-400 border-slate-800 hover:bg-slate-800'
                }`}
              >
                <XCircle className="w-4 h-4 text-rose-400" />
                <span>FAILED</span>
              </button>
            </div>
          </div>

          {/* Test Summary */}
          <div>
            <label className="block text-slate-300 font-semibold mb-1">Test Summary / Verification Method:</label>
            <input
              type="text"
              value={testSummary}
              onChange={(e) => setTestSummary(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-white focus:outline-none focus:border-teal-500"
              required
            />
          </div>

          {/* Verification Evidence */}
          <div>
            <label className="block text-slate-300 font-semibold mb-1">Verification Evidence / Test Output:</label>
            <input
              type="text"
              value={evidencePing}
              onChange={(e) => setEvidencePing(e.target.value)}
              placeholder="e.g. Ping 192.168.20.10: 5/5 success, OSPF state: FULL"
              className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-white font-mono text-[11px] focus:outline-none focus:border-teal-500"
            />
          </div>

          {/* Verification Notes */}
          <div>
            <label className="block text-slate-300 font-semibold mb-1">Engineer Notes:</label>
            <textarea
              rows={2}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-white focus:outline-none focus:border-teal-500"
            />
          </div>

          <p className="text-[11px] text-slate-500 italic">
            * Note: The case will only be marked as fully <strong>RESOLVED</strong> once verification is <strong>PASSED</strong>.
          </p>

          {/* Buttons */}
          <div className="flex justify-end space-x-2 pt-2 border-t border-slate-800">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="px-5 py-2 rounded-lg bg-teal-600 hover:bg-teal-500 text-white text-xs font-bold shadow-lg transition"
            >
              {submitting ? 'Recording...' : `Record Verification (${status})`}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
