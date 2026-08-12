import PropTypes from 'prop-types';

export default function StatCard({ label, value, icon }) {
  return (
    <div className="flex flex-col p-5 bg-panel border border-slate-700 rounded-none shadow-sm transition-all hover:border-slate-500">
      <div className="flex items-center justify-between mb-3">
        <p className="text-[11px] text-slate-500 font-mono uppercase tracking-wider font-semibold">{label}</p>
        {icon && <div className="text-slate-400">{icon}</div>}
      </div>
      <p className="text-2xl font-bold text-off-white font-mono tracking-tight">{value}</p>
    </div>
  );
}

StatCard.propTypes = {
  label: PropTypes.string.isRequired,
  value: PropTypes.oneOfType([PropTypes.string, PropTypes.number]).isRequired,
  icon: PropTypes.node,
};
