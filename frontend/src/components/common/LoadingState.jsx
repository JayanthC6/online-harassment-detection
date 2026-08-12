import PropTypes from 'prop-types';
import { Loader2 } from 'lucide-react';

export default function LoadingState({ message = 'Loading...' }) {
  return (
    <div className="bg-panel border border-slate-700 p-16 text-center flex flex-col items-center justify-center animate-pulse-soft">
      <Loader2 className="w-8 h-8 text-slate-500 animate-spin mb-4" />
      <p className="text-sm font-bold text-slate-500 font-mono uppercase tracking-wider">{message}</p>
    </div>
  );
}

LoadingState.propTypes = {
  message: PropTypes.string,
};
