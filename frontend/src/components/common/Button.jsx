import PropTypes from 'prop-types';
import { Loader2 } from 'lucide-react';

export default function Button({ 
  children, 
  onClick, 
  disabled = false, 
  loading = false, 
  loadingText = 'Loading...', 
  variant = 'primary', // 'primary', 'secondary', or 'ghost'
  className = '',
  ...props
}) {
  let baseClass = 'btn-primary';
  if (variant === 'ghost') {
    baseClass = 'btn-ghost';
  } else if (variant === 'secondary') {
    baseClass = 'bg-panel border border-slate-700 text-off-white hover:bg-slate-800 hover:text-white font-semibold rounded-none px-4 py-2 text-sm transition-all flex items-center justify-center gap-2';
  }
  
  return (
    <button
      onClick={onClick}
      disabled={disabled || loading}
      className={`${baseClass} ${className} flex items-center justify-center gap-2`}
      {...props}
    >
      {loading ? (
        <>
          <Loader2 className="w-4 h-4 animate-spin" />
          <span>{loadingText}</span>
        </>
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
  variant: PropTypes.oneOf(['primary', 'secondary', 'ghost']),
  className: PropTypes.string,
};
