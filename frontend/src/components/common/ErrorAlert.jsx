import PropTypes from 'prop-types';
import { AlertCircle } from 'lucide-react';

export default function ErrorAlert({ error }) {
  if (!error) return null;
  return (
    <div className="border border-danger bg-danger-bg rounded-lg p-4 flex items-start gap-3 animate-slide-up">
      <AlertCircle size={16} className="text-danger flex-shrink-0 mt-0.5" />
      <p className="text-sm text-danger leading-relaxed">{error}</p>
    </div>
  );
}

ErrorAlert.propTypes = {
  error: PropTypes.string,
};
