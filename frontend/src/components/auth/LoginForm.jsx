import { useState } from 'react';
import PropTypes from 'prop-types';
import { apiClient } from '../../api/client';

export default function LoginForm({ onLogin }) {
  const [activeTab, setActiveTab] = useState('user'); // 'user' or 'org'
  const [isSignUp, setIsSignUp] = useState(false);
  
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      let endpoint = '/admin/login';
      if (activeTab === 'user' && isSignUp) {
        endpoint = '/admin/register';
      }
      
      const data = await apiClient(endpoint, {
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
      <div className="flex border-b border-border bg-surface-solid">
        <button
          className={`flex-1 py-4 text-sm font-bold uppercase tracking-wider ${activeTab === 'user' ? 'text-primary border-b-2 border-primary' : 'text-text-muted hover:bg-surface-hover'}`}
          onClick={() => { setActiveTab('user'); setError(''); }}
        >
          Victim / User
        </button>
        <button
          className={`flex-1 py-4 text-sm font-bold uppercase tracking-wider ${activeTab === 'org' ? 'text-primary border-b-2 border-primary' : 'text-text-muted hover:bg-surface-hover'}`}
          onClick={() => { setActiveTab('org'); setError(''); setIsSignUp(false); }}
        >
          Organization
        </button>
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
            {loading ? 'Authenticating...' : (activeTab === 'user' && isSignUp ? 'Sign Up' : 'Sign In')}
          </button>
          
          {activeTab === 'user' && (
            <div className="text-center mt-4">
              <button
                type="button"
                onClick={() => setIsSignUp(!isSignUp)}
                className="text-xs text-primary hover:underline"
              >
                {isSignUp ? 'Already have an account? Sign in' : 'Need an account? Sign up'}
              </button>
            </div>
          )}
        </form>
      </div>
    </div>
  );
}

LoginForm.propTypes = {
  onLogin: PropTypes.func.isRequired,
};
