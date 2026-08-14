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
  let baseClass = 'btn-cyber clip-path-chamfer font-label-caps text-label-caps transition-colors';
  if (variant === 'ghost') {
    baseClass += ' bg-surface/50 border border-outline-variant text-on-surface-variant hover:bg-surface-variant hover:text-on-surface';
  } else if (variant === 'secondary') {
    baseClass += ' bg-secondary-container/20 border border-secondary-container px-6 py-2 text-secondary-container hover:bg-secondary-container hover:text-on-secondary shadow-[0_0_10px_rgba(254,0,254,0.3)]';
  } else {
    // primary
    baseClass += ' bg-surface border border-primary-fixed/50 px-6 py-2 text-primary-fixed hover:bg-primary-fixed/10';
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
