import PropTypes from 'prop-types';
import StatCard from './StatCard';

export default function DashboardStats({ totalFlagged, categoriesCount, activeModel }) {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
      <StatCard label="Flagged Messages" value={totalFlagged} />
      <StatCard label="Categories Seen" value={categoriesCount} />
      <StatCard
        label="Active Model"
        value={activeModel === 'distilbert' ? 'DistilBERT' : 'TF-IDF + LR'}
      />
    </div>
  );
}

DashboardStats.propTypes = {
  totalFlagged: PropTypes.number.isRequired,
  categoriesCount: PropTypes.number.isRequired,
  activeModel: PropTypes.string.isRequired,
};
