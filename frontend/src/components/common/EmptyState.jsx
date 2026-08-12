import PropTypes from 'prop-types';

export default function EmptyState({ icon, title, subtitle, actionText }) {
  return (
    <div className="text-center py-8">
      <p className="text-2xl mb-2">{icon}</p>
      <p className="text-sm text-slate-400 font-mono">{title}</p>
      {subtitle && <p className="text-xs text-slate-500 font-mono mt-1">{subtitle}</p>}
      {actionText && <p className="text-xs text-slate-500 font-mono mt-1">{actionText}</p>}
    </div>
  );
}

EmptyState.propTypes = {
  icon: PropTypes.string.isRequired,
  title: PropTypes.string.isRequired,
  subtitle: PropTypes.string,
  actionText: PropTypes.string,
};
