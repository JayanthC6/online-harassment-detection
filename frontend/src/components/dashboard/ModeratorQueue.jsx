import { useState } from 'react';
import PropTypes from 'prop-types';
import { ChevronUp, ChevronDown, ChevronsUpDown, Inbox, ChevronRight, Loader2 } from 'lucide-react';
import SearchFilters from './SearchFilters';
import IncidentIntelligencePanel from './IncidentIntelligencePanel';
import ConversationDetailsDrawer from './ConversationDetailsDrawer';
import RedactionBar from '../common/RedactionBar';

export default function ModeratorQueue({ reportsData, conversationsData, complaintsData, filters, loading }) {
  const [queueType, setQueueType] = useState('complaints'); // 'messages' | 'conversations' | 'complaints'

  const { reports, total: messagesTotal, total_pages: messagesPages } = reportsData;
  const { conversations, total: convTotal, total_pages: convPages } = conversationsData || { conversations: [], total: 0, total_pages: 0 };

  const [selectedReport, setSelectedReport] = useState(null);
  const [selectedConversation, setSelectedConversation] = useState(null);

  const handleSort = (field) => {
    if (filters.sortBy === field) {
      filters.setSortOrder(filters.sortOrder === 'desc' ? 'asc' : 'desc');
    } else {
      filters.setSortBy(field);
      filters.setSortOrder('desc');
    }
    filters.setPage(1);
  };

  const getSortIcon = (field) => {
    if (filters.sortBy !== field) return <ChevronsUpDown size={14} className="text-slate-500 ml-1" />;
    return filters.sortOrder === 'desc' ? <ChevronDown size={14} className="text-off-white ml-1" /> : <ChevronUp size={14} className="text-off-white ml-1" />;
  };

  return (
    <div className="space-y-4 relative">
      <div className="flex items-center justify-between">
        <h2 className="text-base font-semibold text-text-primary">Digital Safety Incidents</h2>
        <div className="flex bg-surface-2 p-1 border border-border rounded-md gap-1">
          <button
            onClick={() => { setQueueType('messages'); filters.setPage(1); }}
            className={`px-3 py-1.5 text-xs font-semibold rounded transition-colors ${queueType === 'messages' ? 'bg-surface-3 text-text-primary' : 'text-text-muted hover:text-text-secondary'}`}
          >
            Messages
          </button>
          <button
            onClick={() => { setQueueType('conversations'); filters.setPage(1); }}
            className={`px-3 py-1.5 text-xs font-semibold rounded transition-colors ${queueType === 'conversations' ? 'bg-surface-3 text-text-primary' : 'text-text-muted hover:text-text-secondary'}`}
          >
            Conversations
          </button>
          <button
            onClick={() => { setQueueType('complaints'); filters.setPage(1); }}
            className={`px-3 py-1.5 text-xs font-semibold rounded transition-colors ${queueType === 'complaints' ? 'bg-surface-3 text-text-primary' : 'text-text-muted hover:text-text-secondary'}`}
          >
            User Complaints
          </button>
        </div>
      </div>

      <SearchFilters filters={filters} />

      <div className="card overflow-hidden relative">
        {loading && (
          <div className="absolute inset-0 bg-surface/50 backdrop-blur-[2px] flex items-center justify-center z-10 transition-all">
            <Loader2 size={28} className="text-blue animate-spin" />
          </div>
        )}

        {queueType === 'messages' ? (
          <div className="overflow-x-auto min-h-[300px] max-h-[580px]">
            <table className="data-table">
              <thead>
                <tr>
                  <th className="px-5 py-3 cursor-pointer select-none hover:bg-surface-3 transition-colors" onClick={() => handleSort('logged_at')}>
                    <div className="flex items-center">Timestamp {getSortIcon('logged_at')}</div>
                  </th>
                  <th className="px-5 py-3">Message Preview</th>
                  <th className="px-5 py-3">Category</th>
                  <th className="px-5 py-3 cursor-pointer select-none hover:bg-surface-3 transition-colors" onClick={() => handleSort('risk')}>
                    <div className="flex items-center">Safety Score {getSortIcon('risk')}</div>
                  </th>
                  <th className="px-5 py-3 cursor-pointer select-none hover:bg-surface-3 transition-colors" onClick={() => handleSort('confidence')}>
                    <div className="flex items-center">Confidence {getSortIcon('confidence')}</div>
                  </th>
                  <th className="px-5 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {!loading && reports.length === 0 ? (
                  <tr>
                    <td colSpan="6" className="px-5 py-20 text-center">
                      <div className="flex flex-col items-center justify-center space-y-3">
                        <div className="p-4 bg-surface-2 rounded-lg border border-border text-text-muted">
                          <Inbox size={40} strokeWidth={1} />
                        </div>
                        <div>
                          <p className="font-semibold text-text-secondary">Queue is empty</p>
                          <p className="text-xs mt-1 text-text-muted">No reports match your current filters.</p>
                        </div>
                      </div>
                    </td>
                  </tr>
                ) : (
                  reports.map((r, idx) => (
                    <tr
                      key={idx}
                      className="hover:bg-surface-2 transition-colors group cursor-pointer"
                      onClick={() => setSelectedReport(r)}
                    >
                      <td className="px-5 py-3 text-text-muted text-xs tabular-nums font-mono">
                        {new Date(r.logged_at).toLocaleString(undefined, {
                          month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit'
                        })}
                      </td>
                      <td className="px-5 py-3">
                        <div className="max-w-[320px] truncate text-text-primary text-sm" title={r.text_preview}>
                          {r.text_preview}
                        </div>
                      </td>
                      <td className="px-5 py-3">
                        <span className={`badge ${r.category === 'hate_speech' || r.category === 'threat' ? 'badge-danger' :
                            r.category === 'scam' || r.category === 'phishing' ? 'badge-critical' :
                              r.category === 'offensive_language' ? 'badge-warning' :
                                r.category === 'none' || r.category === 'clean' ? 'badge-success' : 'badge-muted'
                          } capitalize`}>
                          {(r.category || 'unknown').replace(/_/g, ' ')}
                        </span>
                      </td>
                      <td className="px-5 py-3">
                        <span className={`${r.risk_score >= 80 ? 'score-critical' :
                            r.risk_score >= 55 ? 'score-high' :
                              r.risk_score >= 30 ? 'score-medium' : 'score-low'
                          }`}>{Math.round(r.risk_score)}</span>
                      </td>
                      <td className="px-5 py-3">
                        <span className="text-text-muted text-xs tabular-nums font-mono">{(r.confidence * 100).toFixed(1)}%</span>
                      </td>
                      <td className="px-5 py-3 text-right">
                        <button
                          className="text-text-muted hover:text-text-primary text-xs font-medium opacity-0 group-hover:opacity-100 transition-opacity focus:opacity-100 flex items-center justify-end w-full gap-1"
                          onClick={(e) => {
                            e.stopPropagation();
                            setSelectedReport(r);
                          }}
                        >
                          View <ChevronRight size={13} />
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        ) : queueType === 'conversations' ? (
          <div className="overflow-x-auto min-h-[300px] max-h-[580px]">
            <table className="data-table">
              <thead>
                <tr>
                  <th className="px-5 py-3 cursor-pointer select-none hover:bg-surface-3 transition-colors" onClick={() => handleSort('logged_at')}>
                    <div className="flex items-center">Timestamp {getSortIcon('logged_at')}</div>
                  </th>
                  <th className="px-5 py-3">Messages</th>
                  <th className="px-5 py-3">Primary Category</th>
                  <th className="px-5 py-3 cursor-pointer select-none hover:bg-surface-3 transition-colors" onClick={() => handleSort('risk')}>
                    <div className="flex items-center">Safety Score {getSortIcon('risk')}</div>
                  </th>
                  <th className="px-5 py-3">Escalation</th>
                  <th className="px-5 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {!loading && conversations.length === 0 ? (
                  <tr>
                    <td colSpan="6" className="px-5 py-20 text-center">
                      <div className="flex flex-col items-center justify-center space-y-3">
                        <div className="p-4 bg-surface-2 rounded-lg border border-border text-text-muted">
                          <Inbox size={40} strokeWidth={1} />
                        </div>
                        <div>
                          <p className="font-semibold text-text-secondary">Queue is empty</p>
                          <p className="text-xs mt-1 text-text-muted">No conversations match your current filters.</p>
                        </div>
                      </div>
                    </td>
                  </tr>
                ) : (
                  conversations.map((c, idx) => (
                    <tr
                      key={idx}
                      className="hover:bg-surface-2 transition-colors group cursor-pointer"
                      onClick={() => setSelectedConversation(c)}
                    >
                      <td className="px-5 py-3 text-text-muted text-xs tabular-nums font-mono">
                        {new Date(c.logged_at).toLocaleString(undefined, {
                          month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit'
                        })}
                      </td>
                      <td className="px-5 py-3">
                        <span className="text-text-secondary text-sm">{c.messages && c.messages.length} messages</span>
                      </td>
                      <td className="px-5 py-3">
                        <span className={`badge ${c.primary_label === 'Clean' ? 'badge-success' : 'badge-warning'
                          } capitalize`}>
                          {c.primary_label}
                        </span>
                      </td>
                      <td className="px-5 py-3">
                        <span className={`${c.conversation_risk >= 80 ? 'score-critical' :
                            c.conversation_risk >= 55 ? 'score-high' :
                              c.conversation_risk >= 30 ? 'score-medium' : 'score-low'
                          }`}>{Math.round(c.conversation_risk)}</span>
                      </td>
                      <td className="px-5 py-3">
                        <span className={`badge ${c.escalation_level === 'High' ? 'badge-danger' :
                            c.escalation_level === 'Medium' ? 'badge-warning' : 'badge-muted'
                          }`}>
                          {c.escalation_level} {c.escalation_score != null ? `(+${c.escalation_score})` : ''}
                        </span>
                      </td>
                      <td className="px-5 py-3 text-right">
                        <button
                          className="text-text-muted hover:text-text-primary text-xs font-medium opacity-0 group-hover:opacity-100 transition-opacity focus:opacity-100 flex items-center justify-end w-full gap-1"
                          onClick={(e) => {
                            e.stopPropagation();
                            setSelectedConversation(c);
                          }}
                        >
                          View <ChevronRight size={13} />
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        ) : queueType === 'complaints' ? (
        <div className="overflow-x-auto min-h-[300px] max-h-[580px]">
          <table className="data-table">
            <thead>
              <tr>
                <th className="px-5 py-3">Timestamp</th>
                <th className="px-5 py-3">User ID</th>
                <th className="px-5 py-3">Complaint Details</th>
                <th className="px-5 py-3">Status</th>
                <th className="px-5 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {!loading && (!complaintsData || complaintsData.length === 0) ? (
                <tr>
                  <td colSpan="5" className="px-5 py-20 text-center">
                    <div className="flex flex-col items-center justify-center space-y-3">
                      <div className="p-4 bg-surface-2 rounded-lg border border-border text-text-muted">
                        <Inbox size={40} strokeWidth={1} />
                      </div>
                      <div>
                        <p className="font-semibold text-text-secondary">No complaints</p>
                        <p className="text-xs mt-1 text-text-muted">Queue is empty.</p>
                      </div>
                    </div>
                  </td>
                </tr>
              ) : (
                (complaintsData || []).map((c, idx) => (
                  <tr key={idx} className="hover:bg-surface-2 transition-colors group">
                    <td className="px-5 py-3 text-text-muted text-xs font-mono">
                      {new Date(c.created_at).toLocaleString()}
                    </td>
                    <td className="px-5 py-3">
                      <span className="text-xs font-mono bg-surface-3 px-2 py-1 rounded text-text-muted">{c.user_id.substring(0, 8)}...</span>
                    </td>
                    <td className="px-5 py-3">
                      <div className="max-w-[320px] truncate text-text-primary text-sm">
                        {c.content || (c.ai_analysis && c.ai_analysis.incident_description) || 'Attached evidence'}
                      </div>
                    </td>
                    <td className="px-5 py-3">
                      <span className={`badge ${c.status === 'resolved' ? 'badge-success' : 'badge-warning'} capitalize`}>
                        {c.status || 'Pending'}
                      </span>
                    </td>
                    <td className="px-5 py-3 text-right">
                      <button className="text-primary hover:underline text-xs font-medium opacity-0 group-hover:opacity-100 transition-opacity focus:opacity-100">
                        Review
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        ) : null}

        {/* Pagination */}
        <div className="px-5 py-3 border-t border-border flex items-center justify-between bg-surface">
          <p className="text-xs text-text-muted">
            Showing <span className="font-semibold text-text-secondary">{(queueType === 'messages' ? reports.length : conversations.length) > 0 ? (filters.page - 1) * filters.pageSize + 1 : 0}</span> to <span className="font-semibold text-text-secondary">{Math.min(filters.page * filters.pageSize, queueType === 'messages' ? messagesTotal : convTotal)}</span> of <span className="font-semibold text-text-secondary">{queueType === 'messages' ? messagesTotal : convTotal}</span> results
          </p>
          <div className="flex gap-1.5">
            <button
              disabled={filters.page === 1}
              onClick={() => filters.setPage(p => Math.max(1, p - 1))}
              className="btn-secondary text-xs py-1.5 px-3 disabled:opacity-40 disabled:cursor-not-allowed"
            >
              Previous
            </button>
            <button
              disabled={filters.page >= (queueType === 'messages' ? messagesPages : convPages)}
              onClick={() => filters.setPage(p => Math.min(queueType === 'messages' ? messagesPages : convPages, p + 1))}
              className="btn-secondary text-xs py-1.5 px-3 disabled:opacity-40 disabled:cursor-not-allowed"
            >
              Next
            </button>
          </div>
        </div>
      </div>

      {/* Drawers */}
      <IncidentIntelligencePanel
        report={selectedReport}
        onClose={() => setSelectedReport(null)}
      />
      {selectedConversation && (
        <ConversationDetailsDrawer
          conversation={selectedConversation}
          onClose={() => setSelectedConversation(null)}
        />
      )}
    </div>
  );
}

ModeratorQueue.propTypes = {
  reportsData: PropTypes.shape({
    reports: PropTypes.array,
    total: PropTypes.number,
    total_pages: PropTypes.number,
  }),
  conversationsData: PropTypes.shape({
    conversations: PropTypes.array,
    total: PropTypes.number,
    total_pages: PropTypes.number,
  }),
  complaintsData: PropTypes.array,
  filters: PropTypes.object.isRequired,
  loading: PropTypes.bool,
};
