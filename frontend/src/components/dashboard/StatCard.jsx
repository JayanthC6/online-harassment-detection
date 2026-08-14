import PropTypes from 'prop-types';

export default function StatCard({ label, value, icon }) {
  return (
    <div className="flex flex-col p-5 glass-panel border border-outline-variant clip-path-chamfer relative overflow-hidden transition-all hover:border-primary-fixed/50 hover:bg-surface-container/50">
      <div className="flex items-center justify-between mb-3 relative z-10">
        <p className="font-label-caps text-label-caps text-on-surface-variant uppercase tracking-wider">{label}</p>
        {icon && <div className="text-secondary-container">{icon}</div>}
      </div>
      <p className="font-display font-bold text-3xl text-on-surface tracking-tight relative z-10">{value}</p>
    </div>
  );
}

StatCard.propTypes = {
  label: PropTypes.string.isRequired,
  value: PropTypes.oneOfType([PropTypes.string, PropTypes.number]).isRequired,
  icon: PropTypes.node,
};
