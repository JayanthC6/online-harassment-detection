import PropTypes from 'prop-types';

export default function StatCard({ label, value, icon, accentColor = '#3B82F6' }) {
  return (
    <div
      className="kpi-card relative overflow-hidden"
      style={{ borderLeftColor: accentColor, boxShadow: `inset 20px 0 30px -20px ${accentColor}30, 0 4px 12px rgba(0,0,0,0.4)` }}
    >
      <div className="flex items-center justify-between mb-2">
        <p className="text-2xs font-bold text-text-secondary uppercase tracking-widest">{label}</p>
        {icon && <div style={{ color: accentColor, filter: `drop-shadow(0 0 5px ${accentColor}80)` }}>{icon}</div>}
      </div>
      <p 
        className="text-3xl font-extrabold text-white tabular-nums font-mono tracking-tight"
        style={{ textShadow: `0 0 15px ${accentColor}60` }}
      >
        {value}
      </p>
    </div>
  );
}

StatCard.propTypes = {
  label:       PropTypes.string.isRequired,
  value:       PropTypes.oneOfType([PropTypes.string, PropTypes.number]).isRequired,
  icon:        PropTypes.node,
  accentColor: PropTypes.string,
};
