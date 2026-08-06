import PropTypes from 'prop-types';

export default function StatCard({ label, value, icon }) {
  return (
    <div className="flex flex-col p-5 bg-white rounded-xl border border-slate-100 shadow-sm transition-all hover:border-slate-200">
      <div className="flex items-center justify-between mb-3">
        <p className="text-[11px] text-slate-500 uppercase tracking-wider font-semibold">{label}</p>
        {icon && <div className="text-slate-400">{icon}</div>}
      </div>
      <p className="text-2xl font-bold text-slate-900 tracking-tight">{value}</p>
    </div>
  );
}

StatCard.propTypes = {
  label: PropTypes.string.isRequired,
  value: PropTypes.oneOfType([PropTypes.string, PropTypes.number]).isRequired,
  icon: PropTypes.node,
};
