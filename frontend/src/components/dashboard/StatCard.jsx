import PropTypes from 'prop-types';

export default function StatCard({ label, value }) {
  return (
    <div className="stat-card">
      <p className="text-[11px] text-gray-400 uppercase tracking-wider mb-1">{label}</p>
      <p className="text-xl font-semibold text-gray-800">{value}</p>
    </div>
  );
}

StatCard.propTypes = {
  label: PropTypes.string.isRequired,
  value: PropTypes.oneOfType([PropTypes.string, PropTypes.number]).isRequired,
};
