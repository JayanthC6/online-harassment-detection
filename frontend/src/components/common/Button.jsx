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
    baseClass = 'bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 hover:text-slate-900 shadow-sm font-semibold rounded-lg px-4 py-2 text-sm transition-all flex items-center justify-center gap-2';
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
