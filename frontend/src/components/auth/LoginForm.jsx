import { useState } from 'react';
import PropTypes from 'prop-types';
import { apiClient } from '../../api/client';

export default function LoginForm({ onLogin }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const data = await apiClient('/admin/login', {
        method: 'POST',
        body: JSON.stringify({ username, password })
      });
      onLogin(data.token);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto mt-12 card overflow-hidden animate-fade-in shadow-neon">
      <div className="px-6 py-5 border-b border-border bg-surface-solid flex items-center justify-between">
        <h3 className="font-bold text-text-primary uppercase tracking-wider flex items-center gap-2">
          <span>🔒</span> Admin Access
        </h3>
      </div>
      <div className="p-6">
        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="p-3 bg-critical-bg border-l-4 border-critical text-critical text-sm font-mono">
              {error}
            </div>
          )}
          
          <div>
            <label className="block text-xs font-bold text-text-muted font-mono uppercase tracking-wider mb-1">
              Username
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="input w-full"
              placeholder="Enter username"
              required
            />
          </div>
          
          <div>
            <label className="block text-xs font-bold text-text-muted font-mono uppercase tracking-wider mb-1">
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="input w-full"
              placeholder="Enter password"
              required
            />
          </div>
          
          <button
            type="submit"
            disabled={loading}
            className="btn-primary w-full justify-center mt-2"
          >
            {loading ? 'Authenticating...' : 'Sign In'}
          </button>
        </form>
      </div>
    </div>
  );
}

LoginForm.propTypes = {
  onLogin: PropTypes.func.isRequired,
};
