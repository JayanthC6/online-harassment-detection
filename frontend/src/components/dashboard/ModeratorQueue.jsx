import { useState } from 'react';
import PropTypes from 'prop-types';
import { ChevronUp, ChevronDown, ChevronsUpDown, Inbox, ChevronRight, Loader2 } from 'lucide-react';
import SearchFilters from './SearchFilters';
import IncidentIntelligencePanel from './IncidentIntelligencePanel';
import ConversationDetailsDrawer from './ConversationDetailsDrawer';
import RedactionBar from '../common/RedactionBar';

export default function ModeratorQueue({ reportsData, conversationsData, filters, loading }) {
  const [queueType, setQueueType] = useState('messages'); // 'messages' | 'conversations'
  
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
    <div className="space-y-4 relative pt-4">
      <div className="flex items-center justify-between mb-2">
        <h2 className="text-sm font-bold text-off-white font-display uppercase tracking-wider">Digital Safety Incidents</h2>
        <div className="flex bg-panel p-1 border border-slate-700 rounded-none">
          <button
            onClick={() => { setQueueType('messages'); filters.setPage(1); }}
            className={`px-3 py-1 text-xs font-bold font-mono uppercase rounded-none transition-colors ${queueType === 'messages' ? 'bg-slate-800 text-off-white' : 'text-slate-500 hover:text-slate-300'}`}
          >
            Messages
          </button>
          <button
            onClick={() => { setQueueType('conversations'); filters.setPage(1); }}
            className={`px-3 py-1 text-xs font-bold font-mono uppercase rounded-none transition-colors ${queueType === 'conversations' ? 'bg-slate-800 text-off-white' : 'text-slate-500 hover:text-slate-300'}`}
          >
            Conversations
          </button>
        </div>
      </div>
      
      <SearchFilters filters={filters} />

      <div className="glass-panel border border-outline-variant clip-path-chamfer overflow-hidden relative">
        {loading && (
          <div className="absolute inset-0 bg-surface/50 backdrop-blur-[2px] flex items-center justify-center z-10 transition-all">
            <Loader2 size={32} className="text-secondary-container animate-spin" />
          </div>
        )}
        
        {queueType === 'messages' ? (
          <div className="overflow-x-auto min-h-[300px] max-h-[600px]">
            <table className="w-full text-left text-sm whitespace-nowrap">
              <thead className="bg-surface-container text-on-surface-variant font-label-caps text-label-caps sticky top-0 border-b border-outline-variant/30 z-0">
                <tr className="uppercase tracking-wider">
                  <th className="px-5 py-4 cursor-pointer select-none hover:bg-slate-700 transition-colors group" onClick={() => handleSort('logged_at')}>
                    <div className="flex items-center">Timestamp {getSortIcon('logged_at')}</div>
                  </th>
                  <th className="px-5 py-4">Message Preview</th>
                  <th className="px-5 py-4">Category</th>
                  <th className="px-5 py-4 cursor-pointer select-none hover:bg-slate-700 transition-colors group" onClick={() => handleSort('risk')}>
                    <div className="flex items-center">Safety Score {getSortIcon('risk')}</div>
                  </th>
                  <th className="px-5 py-4 cursor-pointer select-none hover:bg-slate-700 transition-colors group" onClick={() => handleSort('confidence')}>
                    <div className="flex items-center">Confidence {getSortIcon('confidence')}</div>
                  </th>
                  <th className="px-5 py-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700">
                {!loading && reports.length === 0 ? (
                  <tr>
                    <td colSpan="6" className="px-5 py-24 text-center text-slate-500">
                      <div className="flex flex-col items-center justify-center space-y-3">
                        <div className="p-4 bg-slate-800 rounded-none border border-slate-700 text-slate-500">
                          <Inbox size={48} strokeWidth={1} />
                        </div>
                        <div>
                          <p className="font-bold text-off-white font-mono uppercase tracking-wider">Message queue is empty</p>
                          <p className="text-xs mt-1 text-slate-400 font-mono">No reports match your current filters.</p>
                        </div>
                      </div>
                    </td>
                  </tr>
                ) : (
                  reports.map((r, idx) => (
                    <tr 
                      key={idx} 
                      className="hover:bg-slate-800/50 transition-colors group cursor-pointer"
                      onClick={() => setSelectedReport(r)}
                    >
                      <td className="px-5 py-3.5 text-slate-400 text-xs tabular-nums font-mono">
                        {new Date(r.logged_at).toLocaleString(undefined, {
                          month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit'
                        })}
                      </td>
                      <td className="px-5 py-3.5">
                        <div className="max-w-[320px] truncate text-off-white" title={r.text_preview}>
                          {r.text_preview}
                        </div>
                      </td>
                      <td className="px-5 py-3.5">
                        <span className={`inline-flex items-center px-2 py-1 rounded-none text-[10px] uppercase font-bold tracking-wide font-mono ${
                          r.category === 'hate_speech' ? 'bg-slate-900 text-redaction-red border border-redaction-red' :
                          r.category === 'offensive_language' ? 'bg-panel text-alert-amber border border-alert-amber' :
                          'bg-panel text-verified-teal border border-verified-teal'
                        }`}>
                          {r.category.replace('_', ' ')}
                        </span>
                      </td>
                      <td className="px-5 py-3.5">
                        <div className="flex items-center gap-3">
                          <div className="w-16">
                            <RedactionBar score={r.risk_score / 100} tier={r.risk_score >= 75 ? 'red' : r.risk_score >= 40 ? 'amber' : 'teal'} />
                          </div>
                          <span className="font-bold text-off-white text-xs tabular-nums font-mono">{r.risk_score}</span>
                        </div>
                      </td>
                      <td className="px-5 py-3.5">
                        <span className="text-slate-400 text-xs tabular-nums font-mono">{(r.confidence * 100).toFixed(1)}%</span>
                      </td>
                      <td className="px-5 py-3.5 text-right">
                        <button 
                          className="text-slate-400 hover:text-off-white text-xs font-bold font-mono uppercase opacity-0 group-hover:opacity-100 transition-opacity focus:opacity-100 flex items-center justify-end w-full gap-1"
                          onClick={(e) => {
                            e.stopPropagation();
                            setSelectedReport(r);
                          }}
                        >
                          Details <ChevronRight size={14} />
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="overflow-x-auto min-h-[300px] max-h-[600px]">
            <table className="w-full text-left text-sm whitespace-nowrap">
              <thead className="bg-surface-container text-on-surface-variant font-label-caps text-label-caps sticky top-0 border-b border-outline-variant/30 z-0">
                <tr className="uppercase tracking-wider">
                  <th className="px-5 py-4 cursor-pointer select-none hover:bg-surface-variant transition-colors group" onClick={() => handleSort('logged_at')}>
                    <div className="flex items-center">Timestamp {getSortIcon('logged_at')}</div>
                  </th>
                  <th className="px-5 py-4">Messages</th>
                  <th className="px-5 py-4">Primary Category</th>
                  <th className="px-5 py-4 cursor-pointer select-none hover:bg-surface-variant transition-colors group" onClick={() => handleSort('risk')}>
                    <div className="flex items-center">Safety Score {getSortIcon('risk')}</div>
                  </th>
                  <th className="px-5 py-4">Escalation</th>
                  <th className="px-5 py-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-outline-variant/30">
                {!loading && conversations.length === 0 ? (
                  <tr>
                    <td colSpan="6" className="px-5 py-24 text-center text-slate-500">
                      <div className="flex flex-col items-center justify-center space-y-3">
                        <div className="p-4 bg-slate-800 border border-slate-700 rounded-none text-slate-500">
                          <Inbox size={48} strokeWidth={1} />
                        </div>
                        <div>
                          <p className="font-bold font-mono text-off-white uppercase tracking-wider">Conversation queue is empty</p>
                          <p className="text-xs mt-1 text-slate-400 font-mono">No conversations match your current filters.</p>
                        </div>
                      </div>
                    </td>
                  </tr>
                ) : (
                  conversations.map((c, idx) => (
                    <tr 
                      key={idx} 
                      className="hover:bg-slate-800/50 transition-colors group cursor-pointer"
                      onClick={() => setSelectedConversation(c)}
                    >
                      <td className="px-5 py-3.5 text-slate-400 text-xs tabular-nums font-mono">
                        {new Date(c.logged_at).toLocaleString(undefined, {
                          month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit'
                        })}
                      </td>
                      <td className="px-5 py-3.5">
                        <div className="max-w-[200px] truncate text-off-white font-mono">
                          {c.messages && c.messages.length} messages
                        </div>
                      </td>
                      <td className="px-5 py-3.5">
                        <span className={`inline-flex items-center px-2 py-1 rounded-none text-[10px] uppercase font-bold tracking-wide font-mono ${
                          c.primary_label === 'Clean' ? 'bg-panel text-verified-teal border border-verified-teal' :
                          'bg-panel text-alert-amber border border-alert-amber'
                        }`}>
                          {c.primary_label}
                        </span>
                      </td>
                      <td className="px-5 py-3.5">
                        <div className="flex items-center gap-3">
                          <div className="w-16">
                            <RedactionBar score={c.conversation_risk / 100} tier={c.conversation_risk >= 75 ? 'red' : c.conversation_risk >= 40 ? 'amber' : 'teal'} />
                          </div>
                          <span className="font-bold text-off-white text-xs tabular-nums font-mono">{c.conversation_risk}</span>
                        </div>
                      </td>
                      <td className="px-5 py-3.5">
                        <span className={`inline-flex items-center px-2 py-1 rounded-none text-[10px] uppercase font-bold tracking-wide font-mono ${
                          c.escalation_level === 'High' ? 'bg-slate-900 text-redaction-red border border-redaction-red' :
                          c.escalation_level === 'Medium' ? 'bg-panel text-alert-amber border border-alert-amber' :
                          'bg-panel text-slate-300 border border-slate-700'
                        }`}>
                          {c.escalation_level} (+{c.escalation_score})
                        </span>
                      </td>
                      <td className="px-5 py-3.5 text-right">
                        <button 
                          className="text-slate-400 hover:text-off-white text-xs font-bold font-mono uppercase opacity-0 group-hover:opacity-100 transition-opacity focus:opacity-100 flex items-center justify-end w-full gap-1"
                          onClick={(e) => {
                            e.stopPropagation();
                            setSelectedConversation(c);
                          }}
                        >
                          Details <ChevronRight size={14} />
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}
        
        {/* Pagination */}
        <div className="p-4 border-t border-slate-700 flex items-center justify-between bg-panel">
          <p className="text-xs text-slate-400 font-mono">
            Showing <span className="font-bold text-off-white">{(queueType === 'messages' ? reports.length : conversations.length) > 0 ? (filters.page - 1) * filters.pageSize + 1 : 0}</span> to <span className="font-bold text-off-white">{Math.min(filters.page * filters.pageSize, queueType === 'messages' ? messagesTotal : convTotal)}</span> of <span className="font-bold text-off-white">{queueType === 'messages' ? messagesTotal : convTotal}</span> results
          </p>
          <div className="flex gap-2">
            <button 
              disabled={filters.page === 1}
              onClick={() => filters.setPage(p => Math.max(1, p - 1))}
              className="px-3 py-1.5 text-xs font-bold font-mono uppercase bg-panel border border-slate-700 rounded-none text-slate-400 hover:bg-slate-800 hover:text-off-white disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Previous
            </button>
            <button 
              disabled={filters.page >= (queueType === 'messages' ? messagesPages : convPages)}
              onClick={() => filters.setPage(p => Math.min(queueType === 'messages' ? messagesPages : convPages, p + 1))}
              className="px-3 py-1.5 text-xs font-bold font-mono uppercase bg-panel border border-slate-700 rounded-none text-slate-400 hover:bg-slate-800 hover:text-off-white disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
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
  filters: PropTypes.object.isRequired,
  loading: PropTypes.bool,
};
