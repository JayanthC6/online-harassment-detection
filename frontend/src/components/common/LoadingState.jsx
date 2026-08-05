import PropTypes from 'prop-types';

export default function LoadingState({ message = 'Loading...' }) {
  return (
    <div className="glass-card p-12 text-center animate-pulse-soft">
      <p className="text-sm text-gray-400">{message}</p>
    </div>
  );
}

LoadingState.propTypes = {
  message: PropTypes.string,
};
