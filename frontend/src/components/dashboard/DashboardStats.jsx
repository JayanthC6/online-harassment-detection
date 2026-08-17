import PropTypes from 'prop-types';
import { BarChart3, AlertCircle, AlertTriangle, ShieldAlert, Activity, Bug, TrendingUp } from 'lucide-react';
import StatCard from './StatCard';

export default function DashboardStats({ stats }) {
  if (!stats) return null;

  const categories   = stats.category_breakdown || {};
  const scamAlerts   = (categories['Scam']    || 0) + (categories['Fraud'] || 0);
  const phishing     = categories['Phishing'] || 0;
  const threats      = categories['Threat']   || 0;
  const behavioral   = stats.conversation_stats?.escalated || 0;
  const avgRisk      = Math.round(stats.avg_risk_score || 0);

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
      <StatCard
        label="Total Incidents"
        value={(stats.total_reports || 0).toLocaleString()}
        icon={<BarChart3 size={16} />}
        accentColor="#3B82F6"
      />
      <StatCard
        label="High Risk"
        value={stats.high_risk || 0}
        icon={<AlertCircle size={16} />}
        accentColor="#EF4444"
      />
      <StatCard
        label="Avg Risk Score"
        value={avgRisk}
        icon={<TrendingUp size={16} />}
        accentColor={avgRisk >= 70 ? '#EF4444' : avgRisk >= 40 ? '#F59E0B' : '#10B981'}
      />
      <StatCard
        label="Scams / Fraud"
        value={scamAlerts}
        icon={<AlertTriangle size={16} />}
        accentColor="#F97316"
      />
      <StatCard
        label="Phishing"
        value={phishing}
        icon={<Bug size={16} />}
        accentColor="#EF4444"
      />
      <StatCard
        label="Behavioral Alerts"
        value={behavioral}
        icon={<Activity size={16} />}
        accentColor="#94A3B8"
      />
    </div>
  );
}

DashboardStats.propTypes = {
  stats: PropTypes.shape({
    total_reports:     PropTypes.number,
    high_risk:         PropTypes.number,
    avg_risk_score:    PropTypes.number,
    category_breakdown:PropTypes.object,
    conversation_stats:PropTypes.object,
  }).isRequired,
};
