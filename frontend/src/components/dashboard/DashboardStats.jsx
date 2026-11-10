import PropTypes from 'prop-types';
import { BarChart3, AlertCircle, AlertTriangle, ShieldCheck, Globe, TrendingUp } from 'lucide-react';
import StatCard from './StatCard';

export default function DashboardStats({ stats }) {
  if (!stats) return null;

  const totalReports = stats.total_reports || 0;
  const highRisk     = stats.high_risk || 0;
  const mediumRisk   = stats.medium_risk || 0;
  const safeMessages = stats.safe_messages || 0;
  const unsupported  = stats.unsupported || 0;
  const avgRisk      = Math.round(stats.avg_risk_score || 0);

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
      <StatCard
        label="Total Incidents"
        value={totalReports.toLocaleString()}
        icon={<BarChart3 size={16} />}
        accentColor="#00F2FE"
      />
      <StatCard
        label="High Risk"
        value={highRisk}
        icon={<AlertCircle size={16} />}
        accentColor="#F43F5E"
      />
      <StatCard
        label="Medium Risk"
        value={mediumRisk}
        icon={<AlertTriangle size={16} />}
        accentColor="#F59E0B"
      />
      <StatCard
        label="Safe / Low"
        value={safeMessages}
        icon={<ShieldCheck size={16} />}
        accentColor="#10B981"
      />
      <StatCard
        label="Unsupported"
        value={unsupported}
        icon={<Globe size={16} />}
        accentColor="#A855F7"
      />
      <StatCard
        label="Avg Risk Score"
        value={avgRisk}
        icon={<TrendingUp size={16} />}
        accentColor={avgRisk >= 70 ? '#F43F5E' : avgRisk >= 40 ? '#F59E0B' : '#10B981'}
      />
    </div>
  );
}

DashboardStats.propTypes = {
  stats: PropTypes.shape({
    total_reports:     PropTypes.number,
    high_risk:         PropTypes.number,
    medium_risk:       PropTypes.number,
    safe_messages:     PropTypes.number,
    unsupported:       PropTypes.number,
    avg_risk_score:    PropTypes.number,
    category_breakdown:PropTypes.object,
    conversation_stats:PropTypes.object,
  }).isRequired,
};
