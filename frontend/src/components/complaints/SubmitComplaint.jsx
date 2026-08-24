import { useState } from 'react';
import { apiClient } from '../../../api/client';
import { UploadCloud, MessageSquare, AlertTriangle } from 'lucide-react';

export default function SubmitComplaint({ onNewResult }) {
  const [text, setText] = useState('');
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!text && !file) {
      setError('Please provide text or upload a file as evidence.');
      return;
    }
    setError('');
    setSuccess('');
    setLoading(true);

    try {
      let data;
      if (file) {
        const formData = new FormData();
        formData.append('file', file);
        if (text) formData.append('text', text); // optional context
        data = await apiClient('/complaints', {
          method: 'POST',
          body: formData,
        });
      } else {
        data = await apiClient('/complaints', {
          method: 'POST',
          body: JSON.stringify({ text }),
        });
      }
      
      setSuccess('Your complaint has been securely submitted for review.');
      setText('');
      setFile(null);
      if (onNewResult) setTimeout(onNewResult, 2000);
      
    } catch (err) {
      setError(err.message || 'An error occurred while submitting your complaint.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto card overflow-hidden shadow-neon animate-fade-in">
      <div className="px-6 py-5 border-b border-border bg-surface-solid">
        <h3 className="font-bold text-text-primary flex items-center gap-2">
          <AlertTriangle className="text-warning" size={20} />
          Report an Incident
        </h3>
        <p className="text-sm text-text-muted mt-1">
          Submit details of digital harassment or cyber threats. Our system will analyze the evidence and flag it for our security organization to review.
        </p>
      </div>
      
      <div className="p-6">
        <form onSubmit={handleSubmit} className="space-y-6">
          {error && (
            <div className="p-3 bg-critical-bg border-l-4 border-critical text-critical text-sm">
              {error}
            </div>
          )}
          {success && (
            <div className="p-3 bg-success/10 border-l-4 border-success text-success text-sm">
              {success}
            </div>
          )}
          
          <div>
            <label className="block text-sm font-bold text-text-primary mb-2 flex items-center gap-2">
              <MessageSquare size={16} className="text-text-muted" />
              Incident Description / Text Evidence
            </label>
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Paste the harassing message, threat, or describe the incident..."
              className="input w-full h-32 resize-none"
            />
          </div>
          
          <div>
            <label className="block text-sm font-bold text-text-primary mb-2 flex items-center gap-2">
              <UploadCloud size={16} className="text-text-muted" />
              Upload Evidence (Screenshot or Audio)
            </label>
            <input
              type="file"
              onChange={(e) => setFile(e.target.files[0])}
              className="block w-full text-sm text-text-muted
                file:mr-4 file:py-2 file:px-4
                file:rounded-md file:border-0
                file:text-sm file:font-semibold
                file:bg-surface-3 file:text-primary
                hover:file:bg-surface-hover cursor-pointer"
              accept="image/*,audio/*"
            />
            <p className="text-xs text-text-muted mt-2">
              Supported formats: PNG, JPG, MP3, WAV, M4A
            </p>
          </div>
          
          <div className="pt-4 border-t border-border flex justify-end">
            <button
              type="submit"
              disabled={loading || (!text && !file)}
              className="btn-primary"
            >
              {loading ? 'Submitting & Analyzing...' : 'Submit Complaint'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
