import { useState, useEffect } from 'react';
import { apiClient } from '../../../api/client';
import { Clock, CheckCircle, AlertCircle, ShieldAlert } from 'lucide-react';
import RiskBadge from '../RiskBadge';

export default function MyTickets({ refreshKey }) {
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchTickets = async () => {
      try {
        setLoading(true);
        const data = await apiClient('/complaints/my');
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
        Error loading tickets: {error}
      </div>
    );
  }

  if (tickets.length === 0) {
    return (
      <div className="text-center p-12 card border-dashed">
        <ShieldAlert size={48} className="mx-auto text-text-muted mb-4 opacity-50" />
        <h3 className="text-lg font-bold text-text-primary">No Complaints Filed</h3>
        <p className="text-text-muted mt-2">You haven't submitted any complaints yet.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {tickets.map((ticket, idx) => (
        <div key={ticket._id || idx} className="card p-5 animate-fade-in transition-all hover:border-primary/50">
          <div className="flex justify-between items-start mb-3">
            <div className="flex items-center gap-3">
              <span className={`px-2 py-1 text-xs font-bold uppercase tracking-wider rounded ${
                ticket.status === 'resolved' ? 'bg-success/20 text-success' : 'bg-warning/20 text-warning'
              }`}>
                {ticket.status || 'Pending'}
              </span>
              <span className="text-xs text-text-muted font-mono flex items-center gap-1">
                <Clock size={12} />
                {new Date(ticket.created_at).toLocaleString()}
              </span>
            </div>
            {ticket.ai_analysis && (
              <RiskBadge score={ticket.ai_analysis.risk_score} category={ticket.ai_analysis.category} />
            )}
          </div>
          
          <div className="bg-surface-solid p-4 rounded text-sm text-text-secondary border border-border mt-3">
            <p className="font-medium text-text-primary mb-1">Your Submission:</p>
            <p className="whitespace-pre-wrap">{ticket.content || 'Attached file evidence.'}</p>
          </div>
          
          {ticket.status === 'resolved' && (
            <div className="mt-4 p-4 bg-success/5 border border-success/20 rounded flex gap-3">
              <CheckCircle className="text-success mt-0.5" size={18} />
              <div>
                <p className="text-sm font-bold text-success mb-1">Resolution Note from Organization</p>
                <p className="text-sm text-text-secondary">{ticket.resolution_note || 'This incident has been reviewed and resolved.'}</p>
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
