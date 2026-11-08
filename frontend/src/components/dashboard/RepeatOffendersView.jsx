import React, { useState, useEffect, useCallback } from 'react';
import {
  Users,
  Link as LinkIcon,
  Phone,
  Mail,
  Search,
  Filter,
  ShieldAlert,
  AlertTriangle,
  Clock,
  ChevronRight,
  X,
  ExternalLink,
  ShieldCheck,
  Ban,
  Activity,
  Calendar,
  Layers
} from 'lucide-react';
import { apiClient } from '../../api/client';
import Card from '../common/Card';
import LoadingState from '../common/LoadingState';
import EmptyState from '../common/EmptyState';

export default function RepeatOffendersView() {
  const [offenders, setOffenders] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filters
  const [entityType, setEntityType] = useState('all');
  const [minRisk, setMinRisk] = useState(0);
  const [search, setSearch] = useState('');
  const [sortBy, setSortBy] = useState('hit_count');
  const [sortOrder, setSortOrder] = useState('desc');
  const [page, setPage] = useState(1);

  // Detail Drawer State
  const [selectedOffender, setSelectedOffender] = useState(null);
  const [updatingStatus, setUpdatingStatus] = useState(false);
  const [statusMessage, setStatusMessage] = useState('');

  const fetchOffenders = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams({
        entity_type: entityType,
        min_risk: minRisk,
        search,
        sort_by: sortBy,
        sort_order: sortOrder,
        page,
        page_size: 50
      });
      const data = await apiClient(`/admin/offenders?${params.toString()}`);
      setOffenders(data.offenders || []);
      setTotal(data.total || 0);
    } catch (err) {
      setError(err.message || 'Failed to load offenders');
    } finally {
      setLoading(false);
    }
  }, [entityType, minRisk, search, sortBy, sortOrder, page]);

  useEffect(() => {
    fetchOffenders();
  }, [fetchOffenders]);

  const handleStatusChange = async (entityValue, newStatus) => {
    setUpdatingStatus(true);
    setStatusMessage('');
    try {
      await apiClient(`/admin/offenders/${encodeURIComponent(entityValue)}/status`, {
        method: 'POST',
        body: JSON.stringify({ status: newStatus, notes: `Updated from ShieldAI Admin at ${new Date().toISOString()}` })
      });
      setStatusMessage(`Status updated to ${newStatus}`);
      // Update local state
      setOffenders(prev =>
        prev.map(o => (o.entity_value === entityValue ? { ...o, status: newStatus } : o))
      );
      if (selectedOffender && selectedOffender.entity_value === entityValue) {
        setSelectedOffender(prev => ({ ...prev, status: newStatus }));
      }
    } catch (err) {
      setStatusMessage(`Error: ${err.message}`);
    } finally {
      setUpdatingStatus(false);
    }
  };

  const getRiskColor = (score) => {
    if (score >= 80) return { text: 'text-red-400', bg: 'bg-red-500/20 border-red-500/40', label: 'Critical' };
    if (score >= 55) return { text: 'text-orange-400', bg: 'bg-orange-500/20 border-orange-500/40', label: 'High' };
    if (score >= 30) return { text: 'text-amber-400', bg: 'bg-amber-500/20 border-amber-500/40', label: 'Medium' };
    return { text: 'text-emerald-400', bg: 'bg-emerald-500/20 border-emerald-500/40', label: 'Low' };
  };

  const getEntityIcon = (type) => {
    switch (type) {
      case 'url':
        return <LinkIcon size={14} className="text-orange-400" />;
      case 'phone':
        return <Phone size={14} className="text-cyan-400" />;
      case 'email':
        return <Mail size={14} className="text-purple-400" />;
      default:
        return <Users size={14} className="text-blue" />;
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* ── Header ── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-border/50">
        <div>
          <h2 className="text-xl font-bold text-text-primary flex items-center gap-2">
            <ShieldAlert size={20} className="text-blue" />
            Repeat Offender Intelligence
          </h2>
          <p className="text-xs text-text-muted font-mono mt-1">
            Tracking cross-incident entity hits across Senders, Phone Numbers, Emails, and Phishing URLs
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs font-mono">
          <span className="px-3 py-1.5 rounded-lg bg-surface border border-border text-text-secondary">
            Total Entities: <strong className="text-text-primary">{total}</strong>
          </span>
        </div>
      </div>

      {/* ── Filters Bar ── */}
      <div className="p-4 rounded-xl bg-surface border border-border space-y-3">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
          {/* Search */}
          <div className="relative md:col-span-2">
            <Search size={14} className="absolute left-3 top-3 text-text-muted" />
            <input
              type="text"
              value={search}
              onChange={(e) => { setSearch(e.target.value); setPage(1); }}
              placeholder="Search sender handle, domain, phone, email..."
              className="input pl-9 text-xs"
            />
          </div>

          {/* Entity Type Filter */}
          <div>
            <select
              value={entityType}
              onChange={(e) => { setEntityType(e.target.value); setPage(1); }}
              className="input text-xs"
            >
              <option value="all">All Entity Types</option>
              <option value="sender">Senders / Accounts</option>
              <option value="url">URLs & Domains</option>
              <option value="phone">Phone Numbers</option>
              <option value="email">Email Addresses</option>
            </select>
          </div>

          {/* Min Risk Filter */}
          <div>
            <select
              value={minRisk}
              onChange={(e) => { setMinRisk(Number(e.target.value)); setPage(1); }}
              className="input text-xs"
            >
              <option value="0">All Risk Levels</option>
              <option value="30">Medium Risk+ (&ge; 30)</option>
              <option value="55">High Risk+ (&ge; 55)</option>
              <option value="80">Critical Risk Only (&ge; 80)</option>
            </select>
          </div>
        </div>

        {/* Secondary controls: Sort */}
        <div className="flex flex-wrap items-center justify-between text-xs text-text-muted gap-2 pt-2 border-t border-border/40">
          <div className="flex items-center gap-2">
            <span>Sort by:</span>
            {[
              { id: 'hit_count', label: 'Hit Count' },
              { id: 'peak_risk', label: 'Peak Risk' },
              { id: 'last_seen', label: 'Last Seen' }
            ].map((s) => (
              <button
                key={s.id}
                onClick={() => {
                  if (sortBy === s.id) {
                    setSortOrder(sortOrder === 'desc' ? 'asc' : 'desc');
                  } else {
                    setSortBy(s.id);
                    setSortOrder('desc');
                  }
                  setPage(1);
                }}
                className={`px-2.5 py-1 rounded font-mono uppercase tracking-wider text-[11px] transition-colors ${
                  sortBy === s.id
                    ? 'bg-blue/20 text-blue border border-blue/40 font-bold'
                    : 'bg-surface-solid hover:bg-surface-2 text-text-secondary border border-border'
                }`}
              >
                {s.label} {sortBy === s.id && (sortOrder === 'desc' ? '↓' : '↑')}
              </button>
            ))}
          </div>

          <button
            onClick={fetchOffenders}
            className="text-xs text-blue hover:underline font-mono"
          >
            Refresh List
          </button>
        </div>
      </div>

      {/* ── Table of Offenders ── */}
      {loading ? (
        <LoadingState message="Querying cross-incident offender records..." />
      ) : error ? (
        <div className="p-6 rounded-xl bg-red-950/40 border border-red-500/30 text-red-200 text-sm">
          {error}
        </div>
      ) : offenders.length === 0 ? (
        <EmptyState
          title="No Repeat Offenders Found"
          message="No entities match the current risk thresholds and filter parameters."
        />
      ) : (
        <div className="card overflow-hidden bg-surface/80 border border-border">
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th className="px-4 py-3">Entity</th>
                  <th className="px-4 py-3">Type</th>
                  <th className="px-4 py-3 text-center">Hits</th>
                  <th className="px-4 py-3 text-center">Peak Risk</th>
                  <th className="px-4 py-3">Categories</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Last Seen</th>
                  <th className="px-4 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {offenders.map((off, idx) => {
                  const risk = getRiskColor(off.peak_risk || 0);
                  return (
                    <tr
                      key={idx}
                      onClick={() => setSelectedOffender(off)}
                      className="cursor-pointer hover:bg-white/5 transition-colors group"
                    >
                      <td className="px-4 py-3 font-mono text-xs text-text-primary">
                        <div className="flex items-center gap-2 max-w-[240px] truncate" title={off.entity_value}>
                          {getEntityIcon(off.entity_type)}
                          <span className="truncate font-semibold">{off.entity_value}</span>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-xs uppercase font-mono text-text-muted">
                        {off.entity_type}
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span className="px-2 py-0.5 rounded-full font-mono text-xs font-bold bg-blue/15 text-blue border border-blue/30">
                          {off.hit_count}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span className={`px-2 py-0.5 rounded font-mono text-xs font-bold border ${risk.bg} ${risk.text}`}>
                          {Math.round(off.peak_risk || 0)}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex flex-wrap gap-1 max-w-[200px]">
                          {(off.categories || []).slice(0, 3).map((c, i) => (
                            <span key={i} className="text-[10px] px-1.5 py-0.5 rounded bg-surface border border-border text-text-secondary capitalize">
                              {c.replace(/_/g, ' ')}
                            </span>
                          ))}
                          {(off.categories || []).length > 3 && (
                            <span className="text-[10px] text-text-muted">
                              +{off.categories.length - 3}
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <span className={`text-[11px] font-mono uppercase px-2 py-0.5 rounded border ${
                          off.status === 'banned'
                            ? 'bg-red-500/20 text-red-400 border-red-500/40'
                            : off.status === 'flagged'
                            ? 'bg-orange-500/20 text-orange-400 border-orange-500/40'
                            : off.status === 'monitored'
                            ? 'bg-cyan-500/20 text-cyan-400 border-cyan-500/40'
                            : off.status === 'cleared'
                            ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40'
                            : 'bg-surface border-border text-text-muted'
                        }`}>
                          {off.status || 'active'}
                        </span>
                      </td>
                      <td className="px-4 py-3 font-mono text-xs text-text-muted whitespace-nowrap">
                        {off.last_seen ? new Date(off.last_seen).toLocaleDateString() : '—'}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setSelectedOffender(off);
                          }}
                          className="text-xs font-mono text-blue hover:text-white flex items-center gap-1 ml-auto"
                        >
                          Timeline <ChevronRight size={13} />
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ── Offender Timeline & Detail Drawer ── */}
      {selectedOffender && (
        <>
          <div
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 transition-opacity"
            onClick={() => setSelectedOffender(null)}
          />
          <div className="fixed inset-y-0 right-0 w-full md:w-[620px] bg-[#060913] border-l border-blue/30 shadow-2xl z-50 flex flex-col animate-slide-left overflow-hidden">
            {/* Drawer Header */}
            <div className="px-6 py-4 border-b border-border/50 bg-black/40 flex items-center justify-between shrink-0">
              <div className="flex items-center gap-2.5 overflow-hidden">
                <div className="p-2 rounded bg-blue/10 border border-blue/30 text-blue shrink-0">
                  {getEntityIcon(selectedOffender.entity_type)}
                </div>
                <div className="truncate">
                  <h3 className="text-base font-bold text-text-primary truncate font-mono">
                    {selectedOffender.entity_value}
                  </h3>
                  <p className="text-xs text-text-muted font-mono uppercase">
                    Type: {selectedOffender.entity_type} &bull; First seen: {new Date(selectedOffender.first_seen).toLocaleDateString()}
                  </p>
                </div>
              </div>
              <button
                onClick={() => setSelectedOffender(null)}
                className="p-1.5 text-text-muted hover:text-text-primary rounded-md"
              >
                <X size={18} />
              </button>
            </div>

            {/* Quick Metrics Bar */}
            <div className="grid grid-cols-3 gap-2 px-6 py-3 bg-black/60 border-b border-border/50 shrink-0 text-center font-mono text-xs">
              <div className="p-2 rounded bg-surface border border-border">
                <span className="text-text-muted block text-[10px]">TOTAL HITS</span>
                <span className="text-lg font-bold text-blue">{selectedOffender.hit_count}</span>
              </div>
              <div className="p-2 rounded bg-surface border border-border">
                <span className="text-text-muted block text-[10px]">PEAK RISK</span>
                <span className={`text-lg font-bold ${getRiskColor(selectedOffender.peak_risk || 0).text}`}>
                  {Math.round(selectedOffender.peak_risk || 0)}
                </span>
              </div>
              <div className="p-2 rounded bg-surface border border-border">
                <span className="text-text-muted block text-[10px]">AVG RISK</span>
                <span className="text-lg font-bold text-text-secondary">
                  {Math.round(selectedOffender.avg_risk || 0)}
                </span>
              </div>
            </div>

            {/* Status Workflow Action Buttons */}
            <div className="px-6 py-3 bg-surface/40 border-b border-border/50 flex flex-wrap items-center justify-between gap-2 shrink-0">
              <div className="text-xs font-mono text-text-muted">
                Status: <strong className="text-text-primary uppercase">{selectedOffender.status || 'active'}</strong>
              </div>
              <div className="flex items-center gap-1.5">
                {['active', 'flagged', 'monitored', 'banned', 'cleared'].map((st) => (
                  <button
                    key={st}
                    disabled={updatingStatus || selectedOffender.status === st}
                    onClick={() => handleStatusChange(selectedOffender.entity_value, st)}
                    className={`text-[10px] font-mono uppercase px-2 py-1 rounded transition-colors ${
                      selectedOffender.status === st
                        ? 'opacity-40 cursor-not-allowed bg-surface border border-border text-text-muted'
                        : 'bg-surface-3 hover:bg-surface border border-border text-text-secondary hover:text-white'
                    }`}
                  >
                    {st}
                  </button>
                ))}
              </div>
            </div>

            {statusMessage && (
              <div className="px-6 py-1.5 text-xs font-mono text-cyan-400 bg-cyan-950/40 border-b border-cyan-800/40">
                {statusMessage}
              </div>
            )}

            {/* Offender Timeline Content */}
            <div className="flex-1 overflow-y-auto p-6 space-y-6">
              <div>
                <h4 className="text-xs font-bold text-text-muted font-mono uppercase tracking-wider mb-3 flex items-center gap-2">
                  <Activity size={14} className="text-blue" />
                  Incident Timeline ({selectedOffender.timeline?.length || 0} Events)
                </h4>

                {(!selectedOffender.timeline || selectedOffender.timeline.length === 0) ? (
                  <p className="text-sm text-text-muted italic">No timeline entries recorded yet.</p>
                ) : (
                  <div className="relative pl-4 space-y-4 before:absolute before:inset-y-0 before:left-2 before:w-0.5 before:bg-border/60">
                    {selectedOffender.timeline.map((event, i) => {
                      const eventRisk = getRiskColor(event.risk_score || 0);
                      return (
                        <div key={i} className="relative flex items-start gap-3">
                          <div
                            className="absolute -left-[14px] mt-1.5 w-2.5 h-2.5 rounded-full border border-bg"
                            style={{
                              backgroundColor:
                                (event.risk_score || 0) >= 80 ? '#EF4444' :
                                (event.risk_score || 0) >= 55 ? '#F97316' :
                                (event.risk_score || 0) >= 30 ? '#F59E0B' : '#10B981'
                            }}
                          />
                          <div className="ml-2 flex-1 p-3.5 rounded-lg bg-surface border border-border/60 space-y-2">
                            <div className="flex items-center justify-between text-xs font-mono">
                              <span className="text-text-muted flex items-center gap-1">
                                <Calendar size={12} />
                                {new Date(event.timestamp).toLocaleString()}
                              </span>
                              <span className={`px-2 py-0.5 rounded font-bold border ${eventRisk.bg} ${eventRisk.text}`}>
                                Score: {Math.round(event.risk_score || 0)}
                              </span>
                            </div>

                            {event.category && (
                              <div className="text-xs">
                                <span className="text-text-muted font-mono">Category: </span>
                                <span className="font-semibold text-text-primary capitalize">
                                  {event.category.replace(/_/g, ' ')}
                                </span>
                              </div>
                            )}

                            {event.snippet && (
                              <div className="p-2.5 rounded bg-black/40 border border-border/40 font-mono text-xs text-text-secondary whitespace-pre-wrap break-words">
                                "{event.snippet}"
                              </div>
                            )}

                            {event.report_id && (
                              <div className="text-[11px] font-mono text-text-muted">
                                Linked Report ID: {event.report_id}
                              </div>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

