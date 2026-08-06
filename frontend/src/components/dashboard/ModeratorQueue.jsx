import { useState } from 'react';
import PropTypes from 'prop-types';
import { ChevronUp, ChevronDown, ChevronsUpDown, Inbox, ChevronRight, Loader2 } from 'lucide-react';
import SearchFilters from './SearchFilters';
import ReportDetailsDrawer from './ReportDetailsDrawer';
import ConversationDetailsDrawer from './ConversationDetailsDrawer'; // will create this

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
    if (filters.sortBy !== field) return <ChevronsUpDown size={14} className="text-slate-300 ml-1" />;
    return filters.sortOrder === 'desc' ? <ChevronDown size={14} className="text-indigo-500 ml-1" /> : <ChevronUp size={14} className="text-indigo-500 ml-1" />;
  };

  return (
    <div className="space-y-4 relative pt-4">
      <div className="flex items-center justify-between mb-2">
        <h2 className="text-sm font-semibold text-slate-800 uppercase tracking-wider">Review Queue</h2>
        <div className="flex bg-slate-100 p-1 rounded-lg">
          <button
            onClick={() => { setQueueType('messages'); filters.setPage(1); }}
            className={`px-3 py-1 text-xs font-medium rounded-md transition-colors ${queueType === 'messages' ? 'bg-white shadow-sm text-indigo-700' : 'text-slate-500 hover:text-slate-700'}`}
          >
            Messages
          </button>
          <button
            onClick={() => { setQueueType('conversations'); filters.setPage(1); }}
            className={`px-3 py-1 text-xs font-medium rounded-md transition-colors ${queueType === 'conversations' ? 'bg-white shadow-sm text-indigo-700' : 'text-slate-500 hover:text-slate-700'}`}
          >
            Conversations
          </button>
        </div>
      </div>
      
      <SearchFilters filters={filters} />

      <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden relative">
        {loading && (
          <div className="absolute inset-0 bg-white/50 backdrop-blur-[2px] flex items-center justify-center z-10 transition-all">
            <Loader2 size={32} className="text-indigo-500 animate-spin" />
          </div>
        )}
        
        {queueType === 'messages' ? (
          <div className="overflow-x-auto min-h-[300px] max-h-[600px]">
            <table className="w-full text-left text-sm whitespace-nowrap">
              <thead className="bg-slate-50 text-slate-500 font-medium sticky top-0 border-b border-slate-200 z-0">
                <tr className="text-xs uppercase tracking-wider">
                  <th className="px-5 py-4 cursor-pointer select-none hover:bg-slate-100 transition-colors group" onClick={() => handleSort('logged_at')}>
                    <div className="flex items-center">Timestamp {getSortIcon('logged_at')}</div>
                  </th>
                  <th className="px-5 py-4">Message Preview</th>
                  <th className="px-5 py-4">Category</th>
                  <th className="px-5 py-4 cursor-pointer select-none hover:bg-slate-100 transition-colors group" onClick={() => handleSort('risk')}>
                    <div className="flex items-center">Risk Score {getSortIcon('risk')}</div>
                  </th>
                  <th className="px-5 py-4 cursor-pointer select-none hover:bg-slate-100 transition-colors group" onClick={() => handleSort('confidence')}>
                    <div className="flex items-center">Confidence {getSortIcon('confidence')}</div>
                  </th>
                  <th className="px-5 py-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {!loading && reports.length === 0 ? (
                  <tr>
                    <td colSpan="6" className="px-5 py-24 text-center text-slate-500">
                      <div className="flex flex-col items-center justify-center space-y-3">
                        <div className="p-4 bg-slate-50 rounded-full text-slate-300">
                          <Inbox size={48} strokeWidth={1} />
                        </div>
                        <div>
                          <p className="font-semibold text-slate-700">Message queue is empty</p>
                          <p className="text-xs mt-1 text-slate-400">No reports match your current filters.</p>
                        </div>
                      </div>
                    </td>
                  </tr>
                ) : (
                  reports.map((r, idx) => (
                    <tr 
                      key={idx} 
                      className="hover:bg-slate-50 transition-colors group cursor-pointer"
                      onClick={() => setSelectedReport(r)}
                    >
                      <td className="px-5 py-3.5 text-slate-500 text-xs tabular-nums">
                        {new Date(r.logged_at).toLocaleString(undefined, {
                          month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit'
                        })}
                      </td>
                      <td className="px-5 py-3.5">
                        <div className="max-w-[320px] truncate text-slate-700" title={r.text_preview}>
                          {r.text_preview}
                        </div>
                      </td>
                      <td className="px-5 py-3.5">
                        <span className={`inline-flex items-center px-2 py-1 rounded-md text-[10px] uppercase font-semibold tracking-wide ${
                          r.category === 'hate_speech' ? 'bg-rose-50 text-rose-700 border border-rose-200' :
                          r.category === 'offensive_language' ? 'bg-amber-50 text-amber-700 border border-amber-200' :
                          'bg-emerald-50 text-emerald-700 border border-emerald-200'
                        }`}>
                          {r.category.replace('_', ' ')}
                        </span>
                      </td>
                      <td className="px-5 py-3.5">
                        <div className="flex items-center gap-3">
                          <div className="w-16 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                            <div 
                              className={`h-full rounded-full ${r.risk_score >= 75 ? 'bg-rose-500' : r.risk_score >= 40 ? 'bg-amber-500' : 'bg-emerald-500'}`}
                              style={{ width: `${Math.max(0, Math.min(100, r.risk_score))}%` }}
                            />
                          </div>
                          <span className="font-semibold text-slate-700 text-xs tabular-nums">{r.risk_score}</span>
                        </div>
                      </td>
                      <td className="px-5 py-3.5">
                        <span className="text-slate-500 text-xs tabular-nums">{(r.confidence * 100).toFixed(1)}%</span>
                      </td>
                      <td className="px-5 py-3.5 text-right">
                        <button 
                          className="text-indigo-600 hover:text-indigo-800 text-xs font-semibold opacity-0 group-hover:opacity-100 transition-opacity focus:opacity-100 flex items-center justify-end w-full gap-1"
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
              <thead className="bg-slate-50 text-slate-500 font-medium sticky top-0 border-b border-slate-200 z-0">
                <tr className="text-xs uppercase tracking-wider">
                  <th className="px-5 py-4 cursor-pointer select-none hover:bg-slate-100 transition-colors group" onClick={() => handleSort('logged_at')}>
                    <div className="flex items-center">Timestamp {getSortIcon('logged_at')}</div>
                  </th>
                  <th className="px-5 py-4">Messages</th>
                  <th className="px-5 py-4">Primary Category</th>
                  <th className="px-5 py-4 cursor-pointer select-none hover:bg-slate-100 transition-colors group" onClick={() => handleSort('risk')}>
                    <div className="flex items-center">Risk Score {getSortIcon('risk')}</div>
                  </th>
                  <th className="px-5 py-4">Escalation</th>
                  <th className="px-5 py-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {!loading && conversations.length === 0 ? (
                  <tr>
                    <td colSpan="6" className="px-5 py-24 text-center text-slate-500">
                      <div className="flex flex-col items-center justify-center space-y-3">
                        <div className="p-4 bg-slate-50 rounded-full text-slate-300">
                          <Inbox size={48} strokeWidth={1} />
                        </div>
                        <div>
                          <p className="font-semibold text-slate-700">Conversation queue is empty</p>
                          <p className="text-xs mt-1 text-slate-400">No conversations match your current filters.</p>
                        </div>
                      </div>
                    </td>
                  </tr>
                ) : (
                  conversations.map((c, idx) => (
                    <tr 
                      key={idx} 
                      className="hover:bg-slate-50 transition-colors group cursor-pointer"
                      onClick={() => setSelectedConversation(c)}
                    >
                      <td className="px-5 py-3.5 text-slate-500 text-xs tabular-nums">
                        {new Date(c.logged_at).toLocaleString(undefined, {
                          month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit'
                        })}
                      </td>
                      <td className="px-5 py-3.5">
                        <div className="max-w-[200px] truncate text-slate-700">
                          {c.messages && c.messages.length} messages
                        </div>
                      </td>
                      <td className="px-5 py-3.5">
                        <span className={`inline-flex items-center px-2 py-1 rounded-md text-[10px] uppercase font-semibold tracking-wide ${
                          c.primary_label === 'Clean' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' :
                          'bg-amber-50 text-amber-700 border border-amber-200'
                        }`}>
                          {c.primary_label}
                        </span>
                      </td>
                      <td className="px-5 py-3.5">
                        <div className="flex items-center gap-3">
                          <div className="w-16 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                            <div 
                              className={`h-full rounded-full ${c.conversation_risk >= 75 ? 'bg-rose-500' : c.conversation_risk >= 40 ? 'bg-amber-500' : 'bg-emerald-500'}`}
                              style={{ width: `${Math.max(0, Math.min(100, c.conversation_risk))}%` }}
                            />
                          </div>
                          <span className="font-semibold text-slate-700 text-xs tabular-nums">{c.conversation_risk}</span>
                        </div>
                      </td>
                      <td className="px-5 py-3.5">
                        <span className={`inline-flex items-center px-2 py-1 rounded-md text-[10px] uppercase font-semibold tracking-wide ${
                          c.escalation_level === 'High' ? 'bg-rose-50 text-rose-700 border border-rose-200' :
                          c.escalation_level === 'Medium' ? 'bg-amber-50 text-amber-700 border border-amber-200' :
                          'bg-slate-50 text-slate-700 border border-slate-200'
                        }`}>
                          {c.escalation_level} (+{c.escalation_score})
                        </span>
                      </td>
                      <td className="px-5 py-3.5 text-right">
                        <button 
                          className="text-indigo-600 hover:text-indigo-800 text-xs font-semibold opacity-0 group-hover:opacity-100 transition-opacity focus:opacity-100 flex items-center justify-end w-full gap-1"
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
        <div className="p-4 border-t border-slate-200 flex items-center justify-between bg-white rounded-b-xl">
          <p className="text-xs text-slate-500">
            Showing <span className="font-medium text-slate-700">{(queueType === 'messages' ? reports.length : conversations.length) > 0 ? (filters.page - 1) * filters.pageSize + 1 : 0}</span> to <span className="font-medium text-slate-700">{Math.min(filters.page * filters.pageSize, queueType === 'messages' ? messagesTotal : convTotal)}</span> of <span className="font-medium text-slate-700">{queueType === 'messages' ? messagesTotal : convTotal}</span> results
          </p>
          <div className="flex gap-2">
            <button 
              disabled={filters.page === 1}
              onClick={() => filters.setPage(p => Math.max(1, p - 1))}
              className="px-3 py-1.5 text-xs font-medium bg-white border border-slate-200 rounded-md text-slate-600 hover:bg-slate-50 hover:text-slate-900 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Previous
            </button>
            <button 
              disabled={filters.page >= (queueType === 'messages' ? messagesPages : convPages)}
              onClick={() => filters.setPage(p => Math.min(queueType === 'messages' ? messagesPages : convPages, p + 1))}
              className="px-3 py-1.5 text-xs font-medium bg-white border border-slate-200 rounded-md text-slate-600 hover:bg-slate-50 hover:text-slate-900 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Next
            </button>
          </div>
        </div>
      </div>

      {/* Drawers */}
      <ReportDetailsDrawer 
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
