import { useState, useEffect } from 'react';

function decodeJwtRole(token) {
  if (!token) return null;
  if (token === 'GUEST') return 'Guest';
  try {
    const parts = token.split('.');
    if (parts.length < 2) return null;
    const base64Url = parts[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split('')
        .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join('')
    );
    const parsed = JSON.parse(jsonPayload);
    return parsed.role || parsed.sub || null;
  } catch (e) {
    try {
      return JSON.parse(atob(token.split('.')[1])).role;
    } catch (e2) {
      return null;
    }
  }
}

export function useAuth() {
  const [token, setToken] = useState(() => localStorage.getItem('adminToken') || '');
  const [role, setRole] = useState(() => decodeJwtRole(localStorage.getItem('adminToken')));

  useEffect(() => {
    setRole(decodeJwtRole(token));
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
