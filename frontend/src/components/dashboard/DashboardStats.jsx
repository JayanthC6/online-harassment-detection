import PropTypes from 'prop-types';
import { BarChart3, ShieldCheck, AlertCircle, AlertTriangle, Target, Activity, Cpu, MessageSquare } from 'lucide-react';
import StatCard from './StatCard';

export default function DashboardStats({ stats }) {
  if (!stats) return null;

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <StatCard label="Total Predictions" value={stats.total_reports || 0} icon={<BarChart3 size={18} className="text-slate-400" />} />
        <StatCard label="Safe Messages" value={stats.safe_messages || 0} icon={<ShieldCheck size={18} className="text-emerald-500" />} />
        <StatCard label="High Risk" value={stats.high_risk || 0} icon={<AlertCircle size={18} className="text-rose-500" />} />
        <StatCard label="Medium Risk" value={stats.medium_risk || 0} icon={<AlertTriangle size={18} className="text-amber-500" />} />
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <StatCard label="Total Conversations" value={stats.conversation_stats?.total || 0} icon={<MessageSquare size={18} className="text-indigo-400" />} />
        <StatCard label="Escalated Conversations" value={stats.conversation_stats?.escalated || 0} icon={<Activity size={18} className="text-rose-400" />} />
        <StatCard label="Avg Conv. Risk" value={stats.conversation_stats?.avg_risk || 0} icon={<Target size={18} className="text-orange-400" />} />
        <StatCard label="Active Model" value="DistilBERT" icon={<Cpu size={18} className="text-sky-400" />} />
      </div>
    </div>
  );
}

DashboardStats.propTypes = {
  stats: PropTypes.shape({
    total_reports: PropTypes.number,
    safe_messages: PropTypes.number,
    high_risk: PropTypes.number,
    medium_risk: PropTypes.number,
    avg_confidence: PropTypes.number,
    avg_risk_score: PropTypes.number,
    category_breakdown: PropTypes.object,
    model: PropTypes.string,
  }).isRequired,
};
