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

  const handleGuestSession = async () => {
    setError('');
    setLoading(true);
    try {
      // First attempt authenticating with dev demo admin credentials
      const data = await apiClient('/admin/login', {
        method: 'POST',
        body: JSON.stringify({ username: 'admin', password: 'password123' })
      });
      if (data?.token) {
        onLogin(data.token);
        return;
      }
    } catch (err) {
      // Fallback to GUEST token if login endpoint fails or in offline demo
    } finally {
      setLoading(false);
    }
    onLogin('GUEST');
  };

  return (
    <div className="max-w-md w-full mx-auto mt-12 bg-black/40 backdrop-blur-xl border border-blue/30 rounded-xl overflow-hidden animate-fade-in shadow-[0_0_30px_rgba(0,242,254,0.15)] relative">
      <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-blue to-purple"></div>
      <div className="bg-black/60 border-b border-border/50 p-5 text-center">
        <h2 className="text-lg font-bold text-white font-mono tracking-[0.2em] uppercase drop-shadow-[0_0_8px_rgba(0,242,254,0.5)]">
          {isRegistering ? 'System Access : Register' : 'System Access : Login'}
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

        <div className="mt-4 text-center space-y-3">
          <button 
            type="button" 
            onClick={() => setIsRegistering(!isRegistering)}
            className="text-xs text-text-muted hover:text-primary transition-colors block w-full"
          >
            {isRegistering ? 'Already have an account? Sign In' : 'Need an account? Register'}
          </button>
          
          <div className="pt-4 border-t border-border/50 mt-4 space-y-2">
            <div className="flex items-center justify-center">
              <button 
                type="button" 
                onClick={handleGuestSession}
                disabled={loading}
                className="text-xs font-semibold text-blue hover:text-white transition-colors flex items-center gap-1 drop-shadow-[0_0_5px_rgba(0,242,254,0.4)] disabled:opacity-50"
              >
                Initialize Guest Session &rarr;
              </button>
            </div>
            <p className="text-[11px] text-text-muted font-mono text-center">
              Demo Credentials: <span className="text-cyan-400 font-semibold">admin</span> / <span className="text-cyan-400 font-semibold">password123</span>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

LoginForm.propTypes = {
  onLogin: PropTypes.func.isRequired,
};
