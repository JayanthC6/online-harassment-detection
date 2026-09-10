import { useState, useEffect } from 'react';
import { apiClient } from '../../api/client';
import { Clock, ShieldAlert, Trash2 } from 'lucide-react';
import RiskBadge from '../prediction/RiskBadge';
import ConfidenceBar from '../prediction/ConfidenceBar';

export default function MyHistory({ refreshKey }) {
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchTickets = async () => {
      try {
        setLoading(true);
        const data = await apiClient('/history/my');
        setTickets(data.complaints || []);
        setError(null);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    fetchTickets();
  }, [refreshKey]);

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this history entry?')) return;
    
    try {
      await apiClient(`/history/${id}`, { method: 'DELETE' });
      setTickets(tickets.filter(t => t._id !== id));
    } catch (err) {
      alert(`Failed to delete: ${err.message}`);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center p-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-critical-bg text-critical rounded border border-critical font-mono text-sm">
        Error loading history: {error}
      </div>
    );
  }

  if (tickets.length === 0) {
    return (
    <div className="text-center p-12 card bg-black/40 border border-blue/30 border-dashed backdrop-blur-xl rounded-xl">
      <ShieldAlert size={48} className="mx-auto text-blue mb-4 opacity-70 drop-shadow-[0_0_10px_rgba(0,242,254,0.5)]" />
      <h3 className="text-lg font-bold text-white tracking-widest uppercase">No Analysis History</h3>
      <p className="text-text-muted mt-2">You haven't run any instant analysis checks yet.</p>
    </div>
    );
  }

  return (
    <div className="space-y-4">
      {tickets.map((ticket, idx) => (
        <div key={ticket._id || idx} className="card p-5 animate-fade-in bg-black/40 backdrop-blur-xl border border-blue/20 hover:border-blue/70 hover:shadow-[0_0_20px_rgba(0,242,254,0.2)] transition-all relative overflow-hidden rounded-xl">
          <div className="absolute top-0 left-0 w-1 h-full bg-gradient-to-b from-blue to-purple shadow-[0_0_10px_rgba(0,242,254,0.5)]"></div>
          
          <button 
            onClick={() => handleDelete(ticket._id)}
            className="absolute top-4 right-4 text-text-muted hover:text-danger transition-colors p-1"
            title="Delete from history"
          >
            <Trash2 size={16} />
          </button>

          <div className="flex flex-col md:flex-row md:justify-between md:items-start gap-3 mb-3 pr-8">
            <div>
              <span className="text-xs text-text-muted font-mono flex items-center gap-1 mb-2">
                <Clock size={12} />
                {new Date(ticket.logged_at).toLocaleString()}
              </span>
              <RiskBadge 
                 safetyStatus={ticket.safety_status} 
                 severityTier={ticket.severity_tier} 
                 category={ticket.category || ticket.primary_label} 
                 threatScore={ticket.threat_score || ticket.risk_score} 
              />
            </div>
            
            <div className="w-full md:w-48 pt-1">
               <ConfidenceBar 
                  confidence={ticket.confidence} 
                  isHarassing={ticket.primary_label === 'harassing'} 
                  compact={true}
               />
            </div>
          </div>
          
          <div className="bg-black/60 p-4 rounded text-sm text-text-secondary border border-border/50 mt-3 shadow-inner">
            <p className="font-bold text-blue tracking-wide uppercase mb-1 text-xs">Payload Analyzed:</p>
            <p className="whitespace-pre-wrap italic font-mono text-xs opacity-80">"{ticket.text_preview}..."</p>
          </div>
          
        </div>
      ))}
    </div>
  );
}
