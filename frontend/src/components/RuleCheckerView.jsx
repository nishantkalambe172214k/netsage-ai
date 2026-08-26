import React, { useEffect, useState } from 'react';
import { getCases, runRuleCheck } from '../services/api';
import { ShieldAlert, Play, CheckCircle, AlertTriangle, XCircle, RefreshCw } from 'lucide-react';

const RULES_INFO = [
  { id: 'RULE_DUPLICATE_IP', name: 'Duplicate IP', desc: 'Detects duplicate IPv4 address assignments across interfaces & hosts.' },
  { id: 'RULE_WRONG_SUBNET_MASK', name: 'Wrong Subnet Mask', desc: 'Validates subnet mask correctness, parity on links, and ACL wildcard mask inversions.' },
  { id: 'RULE_GATEWAY_MISMATCH', name: 'Gateway Mismatch', desc: 'Verifies host client default gateways against local router IP & DHCP pool configurations.' },
  { id: 'RULE_INTERFACE_DOWN', name: 'Interface Down', desc: 'Identifies administratively disabled interfaces (shutdown) and disabled services.' },
  { id: 'RULE_MISSING_VLAN', name: 'Missing VLAN', desc: 'Detects uncreated VLANs, dot1Q sub-interface tag mismatches, and trunk allowed list pruning.' },
  { id: 'RULE_MISSING_ROUTE', name: 'Missing Route', desc: 'Validates default routes to ISP, OSPF passive-interface blocks, and DHCP helper-addresses.' },
];

export default function RuleCheckerView({ onSelectCase }) {
  const [cases, setCases] = useState([]);
  const [selectedCaseId, setSelectedCaseId] = useState('CASE-VLAN-001');
  const [findings, setFindings] = useState([]);
  const [loading, setLoading] = useState(false);
  const [runningAll, setRunningAll] = useState(false);

  useEffect(() => {
    async function init() {
      try {
        const all = await getCases();
        setCases(all);
        if (all.length > 0) setSelectedCaseId(all[0].case_id);
      } catch (err) {
        console.error(err);
      }
    }
    init();
  }, []);

  const handleRunRuleCheck = async () => {
    try {
      setLoading(true);
      const res = await runRuleCheck(selectedCaseId);
      setFindings(res);
    } catch (err) {
      alert('Error: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto p-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight">Python Deterministic Rule Engine</h2>
          <p className="text-xs text-slate-400">Pure-Python deterministic configuration validation for Cisco IOS</p>
        </div>
      </div>

      {/* 6 Rules Specification Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {RULES_INFO.map((rule) => (
          <div key={rule.id} className="p-4 rounded-xl bg-slate-900/70 border border-slate-800 space-y-1.5 shadow-md">
            <div className="flex items-center justify-between">
              <span className="font-bold text-xs text-sky-400 font-mono">{rule.id}</span>
              <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 font-bold border border-emerald-500/30">
                ACTIVE
              </span>
            </div>
            <h4 className="text-xs font-semibold text-white">{rule.name}</h4>
            <p className="text-[11px] text-slate-400 leading-relaxed">{rule.desc}</p>
          </div>
        ))}
      </div>

      {/* Interactive Case Runner */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 space-y-4 shadow-lg">
        <h3 className="text-xs font-bold uppercase tracking-wider text-amber-400">Execute Rule Check on Case</h3>
        
        <div className="flex flex-col sm:flex-row items-center gap-3">
          <select
            value={selectedCaseId}
            onChange={(e) => setSelectedCaseId(e.target.value)}
            className="flex-1 bg-slate-950 border border-slate-700 text-white text-xs font-semibold rounded-lg px-3 py-2 focus:outline-none focus:border-amber-500"
          >
            {cases.map((c) => (
              <option key={c.case_id} value={c.case_id}>
                {c.case_id} — {c.title}
              </option>
            ))}
          </select>

          <button
            onClick={handleRunRuleCheck}
            disabled={loading}
            className="px-5 py-2 bg-amber-600 hover:bg-amber-500 text-white text-xs font-bold rounded-lg shadow-md transition flex items-center gap-2"
          >
            <Play className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Scan Selected Case</span>
          </button>
        </div>

        {/* Results */}
        {findings.length > 0 ? (
          <div className="space-y-3 pt-3 border-t border-slate-800">
            <h4 className="text-xs font-bold text-slate-300">Rule Inspection Output ({findings.length} findings):</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {findings.map((f, i) => (
                <div key={i} className="p-3.5 bg-slate-950 rounded-lg border border-slate-800 space-y-1.5 text-xs">
                  <div className="flex justify-between items-center">
                    <span className="font-mono font-bold text-amber-400">{f.rule_id}</span>
                    <span className="text-[10px] uppercase font-bold text-rose-400 bg-rose-500/20 px-2 py-0.5 rounded">
                      {f.severity}
                    </span>
                  </div>
                  <p className="font-semibold text-white">{f.rule_name}</p>
                  <p className="text-slate-400 text-[11px]">{f.message}</p>
                  {f.affected_device && (
                    <div className="text-[10px] text-slate-500 font-mono">
                      Target: {f.affected_device} {f.affected_interface ? `(${f.affected_interface})` : ''}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="p-6 text-center text-slate-500 text-xs bg-slate-950/40 rounded-lg border border-slate-800">
            Select a case and click "Scan Selected Case" to execute deterministic rule inspection.
          </div>
        )}
      </div>
    </div>
  );
}
