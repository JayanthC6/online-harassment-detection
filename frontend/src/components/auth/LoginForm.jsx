import { useState } from 'react';
import PropTypes from 'prop-types';
import { apiClient } from '../../api/client';

export default function LoginForm({ onLogin }) {
  const [isRegistering, setIsRegistering] = useState(false);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const endpoint = isRegistering ? '/auth/register' : '/admin/login';
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
      <div className="bg-surface-solid border-b border-border p-4 text-center">
        <h2 className="text-lg font-bold text-primary font-mono tracking-wider uppercase">
          {isRegistering ? 'Create Account' : 'Sign In'}
        </h2>
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
              Email / Username
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="input w-full"
              placeholder="Enter email or username"
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

          {isRegistering && (
            <div className="p-3 bg-blue-muted/30 border-l-4 border-blue text-xs text-text-secondary">
              <strong>Disclaimer:</strong> This tool provides automated guidance only and is not a substitute for reporting to official resources. No human reviews or acts on what you paste here. 
              <br/><br/>
              Your email is used <em>solely</em> to let you view your personal analysis history. We do not sell or share your data.
            </div>
          )}
          
          <button
            type="submit"
            disabled={loading}
            className="btn-primary w-full justify-center mt-2"
          >
            {loading ? (isRegistering ? 'Creating...' : 'Authenticating...') : (isRegistering ? 'Register' : 'Sign In')}
          </button>
        </form>

        <div className="mt-4 text-center">
          <button 
            type="button" 
            onClick={() => setIsRegistering(!isRegistering)}
            className="text-xs text-text-muted hover:text-primary transition-colors"
          >
            {isRegistering ? 'Already have an account? Sign In' : 'Need an account? Register'}
          </button>
        </div>
      </div>
    </div>
  );
}

LoginForm.propTypes = {
  onLogin: PropTypes.func.isRequired,
};
