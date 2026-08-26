import React, { useEffect, useState } from 'react';
import { getCases } from '../services/api';
import { Search, Filter, Wrench, CheckCircle, Clock, AlertTriangle, XCircle, ArrowRight } from 'lucide-react';

const CATEGORIES = ['All', 'VLAN', 'Gateway', 'DHCP', 'DNS', 'Routing', 'ACL', 'NAT', 'Wireless'];

export default function CasesList({ onSelectCase }) {
  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('All');

  const loadCases = async () => {
    try {
      setLoading(true);
      const data = await getCases();
      setCases(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCases();
  }, []);

  const filteredCases = cases.filter((c) => {
    const desc = c.description || '';
    const title = c.title || '';
    const caseId = c.case_id || '';
    
    // Category match
    let matchCat = true;
    if (selectedCategory !== 'All') {
      matchCat = desc.includes(`Category: ${selectedCategory}`) || title.includes(selectedCategory);
    }

    // Status match
    let matchStatus = true;
    if (statusFilter !== 'All') {
      matchStatus = c.status === statusFilter;
    }

    // Search match
    const matchSearch =
      title.toLowerCase().includes(search.toLowerCase()) ||
      caseId.toLowerCase().includes(search.toLowerCase()) ||
      desc.toLowerCase().includes(search.toLowerCase());

    return matchCat && matchStatus && matchSearch;
  });

  const getStatusBadge = (status) => {
    switch (status) {
      case 'RESOLVED':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-teal-500/10 text-teal-400 border border-teal-500/20">
            <CheckCircle className="w-3 h-3" /> Resolved
          </span>
        );
      case 'APPROVED':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <CheckCircle className="w-3 h-3" /> Approved
          </span>
        );
      case 'IN_REVIEW':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">
            <Clock className="w-3 h-3" /> In Review
          </span>
        );
      case 'REJECTED':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20">
            <XCircle className="w-3 h-3" /> Rejected
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-slate-700/50 text-slate-300 border border-slate-700">
            Open
          </span>
        );
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto p-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight">Cisco Packet Tracer Troubleshooting Cases</h2>
          <p className="text-xs text-slate-400">30 authentic networking scenarios across 8 core domains</p>
        </div>
        <div className="text-xs text-slate-400 font-mono">
          Showing {filteredCases.length} of {cases.length} cases
        </div>
      </div>

      {/* Category Pills */}
      <div className="flex flex-wrap gap-1.5 bg-slate-950/60 p-1.5 rounded-xl border border-slate-800">
        {CATEGORIES.map((cat) => (
          <button
            key={cat}
            onClick={() => setSelectedCategory(cat)}
            className={`px-3 py-1 rounded-lg text-xs font-medium transition ${
              selectedCategory === cat
                ? 'bg-sky-600 text-white'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
            }`}
          >
            {cat}
          </button>
        ))}
      </div>

      {/* Search & Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search cases by ID, title, symptom..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-slate-900 border border-slate-800 rounded-lg pl-9 pr-4 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-sky-500"
          />
        </div>
        <div className="flex items-center space-x-2">
          <Filter className="w-4 h-4 text-slate-400" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-300 focus:outline-none focus:border-sky-500"
          >
            <option value="All">All Statuses</option>
            <option value="OPEN">OPEN</option>
            <option value="IN_REVIEW">IN_REVIEW</option>
            <option value="APPROVED">APPROVED</option>
            <option value="REJECTED">REJECTED</option>
            <option value="RESOLVED">RESOLVED</option>
          </select>
        </div>
      </div>

      {/* Cases Table */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/80 text-slate-400 font-semibold border-b border-slate-800 uppercase tracking-wider text-[10px]">
              <tr>
                <th className="py-3 px-4">Case ID</th>
                <th className="py-3 px-4">Title</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4">Description & Symptoms</th>
                <th className="py-3 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {loading ? (
                <tr>
                  <td colSpan={5} className="py-8 text-center text-slate-500">
                    Loading cases...
                  </td>
                </tr>
              ) : filteredCases.length === 0 ? (
                <tr>
                  <td colSpan={5} className="py-8 text-center text-slate-500">
                    No cases match the selected filters.
                  </td>
                </tr>
              ) : (
                filteredCases.map((c) => (
                  <tr key={c.id} className="hover:bg-slate-800/30 transition group">
                    <td className="py-3.5 px-4 font-mono font-bold text-sky-400">
                      {c.case_id}
                    </td>
                    <td className="py-3.5 px-4 font-medium text-slate-100 max-w-xs">
                      {c.title}
                    </td>
                    <td className="py-3.5 px-4 whitespace-nowrap">
                      {getStatusBadge(c.status)}
                    </td>
                    <td className="py-3.5 px-4 text-slate-400 text-[11px] max-w-md line-clamp-2">
                      {c.description}
                    </td>
                    <td className="py-3.5 px-4 text-right whitespace-nowrap">
                      <button
                        onClick={() => onSelectCase(c.case_id)}
                        className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-sky-600/20 hover:bg-sky-600 text-sky-300 hover:text-white border border-sky-500/30 transition text-xs font-medium"
                      >
                        <Wrench className="w-3.5 h-3.5" />
                        <span>Triage</span>
                        <ArrowRight className="w-3 h-3" />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
