import PropTypes from 'prop-types';

export default function ErrorAlert({ error }) {
  if (!error) return null;
  
  return (
    <div className="glass-card p-4 !border-red-300 !bg-red-50 animate-slide-up">
      <p className="text-sm text-red-700 flex items-center gap-2">
        <span>⚠️</span> {error}
      </p>
    </div>
  );
}

ErrorAlert.propTypes = {
  error: PropTypes.string,
};
