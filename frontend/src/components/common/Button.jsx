import PropTypes from 'prop-types';

export default function Button({ 
  children, 
  onClick, 
  disabled = false, 
  loading = false, 
  loadingText = 'Loading...', 
  variant = 'primary', // 'primary' or 'ghost'
  className = '',
  ...props
}) {
  const baseClass = variant === 'primary' ? 'btn-primary' : 'btn-ghost';
  
  return (
    <button
      onClick={onClick}
      disabled={disabled || loading}
      className={`${baseClass} ${className}`}
      {...props}
    >
      {loading ? (
        <span className="flex items-center gap-2">
          <svg className="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none">
            <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" strokeDasharray="32" strokeLinecap="round" />
          </svg>
          {loadingText}
        </span>
      ) : (
        children
      )}
    </button>
  );
}

Button.propTypes = {
  children: PropTypes.node.isRequired,
  onClick: PropTypes.func,
  disabled: PropTypes.bool,
  loading: PropTypes.bool,
  loadingText: PropTypes.string,
  variant: PropTypes.oneOf(['primary', 'ghost']),
  className: PropTypes.string,
};
