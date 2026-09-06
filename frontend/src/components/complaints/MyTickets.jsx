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
      <div className="text-center p-12 card border-dashed">
        <ShieldAlert size={48} className="mx-auto text-text-muted mb-4 opacity-50" />
        <h3 className="text-lg font-bold text-text-primary">No Analysis History</h3>
        <p className="text-text-muted mt-2">You haven't run any instant analysis checks yet.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {tickets.map((ticket, idx) => (
        <div key={ticket._id || idx} className="card p-5 animate-fade-in transition-all hover:border-primary/50 relative">
          
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
                 isHarassing={ticket.primary_label === 'harassing'} 
                 category={ticket.category || ticket.primary_label} 
                 riskScore={ticket.risk_score} 
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
          
          <div className="bg-surface-solid p-4 rounded text-sm text-text-secondary border border-border mt-3">
            <p className="font-medium text-text-primary mb-1">Text Analyzed:</p>
            <p className="whitespace-pre-wrap italic">"{ticket.text_preview}..."</p>
          </div>
          
        </div>
      ))}
    </div>
  );
}
