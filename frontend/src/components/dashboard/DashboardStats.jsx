import PropTypes from 'prop-types';
import { BarChart3, AlertCircle, AlertTriangle, ShieldAlert, Activity, Bug } from 'lucide-react';
import StatCard from './StatCard';

export default function DashboardStats({ stats }) {
  if (!stats) return null;

  const categories = stats.category_breakdown || {};
  const scamAlerts = (categories['Scam'] || 0) + (categories['Fraud'] || 0);
  const phishingAlerts = categories['Phishing'] || 0;
  const threatAlerts = categories['Threat'] || 0;
  const behavioralAlerts = stats.conversation_stats?.escalated || 0;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
        
        {/* Incident Overview */}
        <div className="col-span-1 md:col-span-4 space-y-3">
          <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Incident Overview</h3>
          <div className="grid grid-cols-2 gap-3">
            <StatCard label="Total Incidents" value={stats.total_reports || 0} icon={<BarChart3 size={18} className="text-slate-500" />} />
            <StatCard label="High Risk" value={stats.high_risk || 0} icon={<AlertCircle size={18} className="text-redaction-red" />} />
          </div>
        </div>

        {/* Threat Intelligence */}
        <div className="col-span-1 md:col-span-5 space-y-3">
          <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Threat Intelligence</h3>
          <div className="grid grid-cols-3 gap-3">
            <StatCard label="Scams" value={scamAlerts} icon={<AlertTriangle size={18} className="text-alert-amber" />} />
            <StatCard label="Phishing" value={phishingAlerts} icon={<Bug size={18} className="text-redaction-red" />} />
            <StatCard label="Threats" value={threatAlerts} icon={<ShieldAlert size={18} className="text-redaction-red" />} />
          </div>
        </div>

        {/* Actor Intelligence */}
        <div className="col-span-1 md:col-span-3 space-y-3">
          <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Actor Intelligence</h3>
          <div className="grid grid-cols-1 gap-3">
            <StatCard label="Behavioral Alerts" value={behavioralAlerts} icon={<Activity size={18} className="text-slate-400" />} />
          </div>
        </div>

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
