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

function getStoredToken() {
  if (typeof window === 'undefined') return '';
  // sessionStorage maintains active session during refreshes (Ctrl+R),
  // but resets on new browser launch/tab so the app cleanly defaults to the Login page.
  return sessionStorage.getItem('adminToken') || '';
}

export function useAuth() {
  const [token, setToken] = useState(() => {
    const sessionToken = getStoredToken();
    // If opening fresh without an active session, clear any stale legacy localStorage token
    // so fresh project runs always present the Login portal
    if (!sessionToken && typeof window !== 'undefined') {
      try {
        localStorage.removeItem('adminToken');
      } catch (e) {}
    }
    return sessionToken;
  });
  const [role, setRole] = useState(() => decodeJwtRole(getStoredToken()));

  useEffect(() => {
    setRole(decodeJwtRole(token));
  }, [token]);

  const login = (newToken) => {
    setToken(newToken);
    try {
      sessionStorage.setItem('adminToken', newToken);
      localStorage.setItem('adminToken', newToken);
    } catch (e) {}
  };

  const logout = () => {
    setToken('');
    setRole(null);
    try {
      sessionStorage.removeItem('adminToken');
      localStorage.removeItem('adminToken');
      sessionStorage.removeItem('shieldai_active_tab');
      localStorage.removeItem('shieldai_active_tab');
    } catch (e) {}
  };

  useEffect(() => {
    const handleUnauthorized = () => logout();
    window.addEventListener('auth:unauthorized', handleUnauthorized);
    return () => window.removeEventListener('auth:unauthorized', handleUnauthorized);
  }, []);

  return { token, role, login, logout };
}
