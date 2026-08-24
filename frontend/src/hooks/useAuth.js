import { useState, useEffect } from 'react';

export function useAuth() {
  const [token, setToken] = useState(() => localStorage.getItem('adminToken') || '');
  const [role, setRole] = useState(null);

  useEffect(() => {
    if (token) {
      try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        setRole(payload.role);
      } catch (e) {
        setRole(null);
      }
    } else {
      setRole(null);
    }
  }, [token]);

  const login = (newToken) => {
    setToken(newToken);
    localStorage.setItem('adminToken', newToken);
  };

  const logout = () => {
    setToken('');
    localStorage.removeItem('adminToken');
  };

  useEffect(() => {
    const handleUnauthorized = () => logout();
    window.addEventListener('auth:unauthorized', handleUnauthorized);
    return () => window.removeEventListener('auth:unauthorized', handleUnauthorized);
  }, []);

  return { token, role, login, logout };
}
