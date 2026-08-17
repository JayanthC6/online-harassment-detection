import PropTypes from 'prop-types';

export default function StatCard({ label, value, icon, accentColor = '#3B82F6' }) {
  return (
    <div
      className="kpi-card"
      style={{ borderLeftColor: accentColor }}
    >
      <div className="flex items-center justify-between mb-2">
        <p className="text-2xs font-semibold text-text-muted uppercase tracking-widest">{label}</p>
        {icon && <div className="text-text-muted opacity-70">{icon}</div>}
      </div>
      <p className="text-3xl font-extrabold text-text-primary tabular-nums font-mono">{value}</p>
    </div>
  );
}

StatCard.propTypes = {
  label:       PropTypes.string.isRequired,
  value:       PropTypes.oneOfType([PropTypes.string, PropTypes.number]).isRequired,
  icon:        PropTypes.node,
  accentColor: PropTypes.string,
};
