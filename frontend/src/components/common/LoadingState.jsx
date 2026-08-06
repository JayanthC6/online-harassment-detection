import PropTypes from 'prop-types';
import { Loader2 } from 'lucide-react';

export default function LoadingState({ message = 'Loading...' }) {
  return (
    <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-16 text-center flex flex-col items-center justify-center animate-pulse-soft">
      <Loader2 className="w-8 h-8 text-indigo-500 animate-spin mb-4" />
      <p className="text-sm font-medium text-slate-500 uppercase tracking-wider">{message}</p>
    </div>
  );
}

LoadingState.propTypes = {
  message: PropTypes.string,
};
