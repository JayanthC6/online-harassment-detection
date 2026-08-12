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
    <div className="max-w-md mx-auto mt-12 bg-panel border border-slate-700 overflow-hidden">
      <div className="px-6 py-5 border-b border-slate-700 bg-ink flex items-center justify-between">
        <h3 className="font-bold text-off-white font-display uppercase tracking-wider flex items-center gap-2">
          <span>🔒</span> Admin Login
        </h3>
      </div>
      <div className="p-6">
        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="p-3 bg-slate-900 border-l-4 border-redaction-red text-redaction-red text-sm font-mono">
              {error}
            </div>
          )}
          
          <div>
            <label className="block text-xs font-bold text-slate-500 font-mono uppercase tracking-wider mb-1">
              Username
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="input-dark w-full px-3 py-2 text-sm"
              placeholder="Enter username"
              required
            />
          </div>
          
          <div>
            <label className="block text-xs font-bold text-slate-500 font-mono uppercase tracking-wider mb-1">
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="input-dark w-full px-3 py-2 text-sm"
              placeholder="Enter password"
              required
            />
          </div>
          
          <button
            type="submit"
            disabled={loading}
            className="btn-primary w-full justify-center"
          >
            {loading ? 'Logging in...' : 'Sign In'}
          </button>
        </form>
      </div>
    </div>
  );
}

LoginForm.propTypes = {
  onLogin: PropTypes.func.isRequired,
};
