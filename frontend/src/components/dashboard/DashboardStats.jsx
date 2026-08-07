import PropTypes from 'prop-types';
import { BarChart3, AlertCircle, AlertTriangle, ShieldAlert, Activity, Bug } from 'lucide-react';
import StatCard from './StatCard';

export default function DashboardStats({ stats }) {
  if (!stats) return null;

  // Extract counts for scams, phishing, threats if available, else 0
  const categories = stats.category_breakdown || {};
  const scamAlerts = (categories['Scam'] || 0) + (categories['Fraud'] || 0);
  const phishingAlerts = categories['Phishing'] || 0;
  const threatAlerts = categories['Threat'] || 0;
  const behavioralAlerts = stats.conversation_stats?.escalated || 0;

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-4">
        <StatCard label="Total Incidents" value={stats.total_reports || 0} icon={<BarChart3 size={18} className="text-slate-400" />} />
        <StatCard label="High Risk Incidents" value={stats.high_risk || 0} icon={<AlertCircle size={18} className="text-rose-500" />} />
        <StatCard label="Scam Alerts" value={scamAlerts} icon={<AlertTriangle size={18} className="text-amber-500" />} />
        <StatCard label="Phishing Alerts" value={phishingAlerts} icon={<Bug size={18} className="text-purple-500" />} />
        <StatCard label="Threat Alerts" value={threatAlerts} icon={<ShieldAlert size={18} className="text-rose-500" />} />
        <StatCard label="Behavioral Alerts" value={behavioralAlerts} icon={<Activity size={18} className="text-indigo-500" />} />
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
    conversation_stats: PropTypes.object,
  }).isRequired,
};
