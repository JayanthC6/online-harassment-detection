import PropTypes from 'prop-types';
import { Loader2 } from 'lucide-react';

export default function Button({
  children,
  onClick,
  disabled = false,
  loading = false,
  loadingText = 'Loading...',
  variant = 'primary',
  className = '',
  ...props
}) {
  const variants = {
    primary:   'btn-primary',
    secondary: 'btn-secondary',
    ghost:     'btn-ghost',
  };

  return (
    <button
      onClick={onClick}
      disabled={disabled || loading}
      className={`${variants[variant] || 'btn-primary'} ${className}`}
      {...props}
    >
      {loading ? (
        <>
          <Loader2 size={14} className="animate-spin" />
          <span>{loadingText}</span>
        </>
      ) : (
        children
      )}
    </button>
  );
}

Button.propTypes = {
  children:    PropTypes.node.isRequired,
  onClick:     PropTypes.func,
  disabled:    PropTypes.bool,
  loading:     PropTypes.bool,
  loadingText: PropTypes.string,
  variant:     PropTypes.oneOf(['primary', 'secondary', 'ghost']),
  className:   PropTypes.string,
};
