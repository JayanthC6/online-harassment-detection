import React, { useState, useEffect, useCallback } from 'react';
import { AlertTriangle, RefreshCw, CheckCircle2 } from 'lucide-react';

export default function BackendHealthBanner() {
  const [isHealthy, setIsHealthy] = useState(true);
  const [checking, setChecking] = useState(false);
  const [lastChecked, setLastChecked] = useState(null);

  const checkHealth = useCallback(async () => {
    setChecking(true);
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 4000);
      const res = await fetch('/api/health', { signal: controller.signal });
      clearTimeout(timeoutId);
      if (res.ok) {
        setIsHealthy(true);
      } else {
        setIsHealthy(false);
      }
    } catch {
      setIsHealthy(false);
    } finally {
      setChecking(false);
      setLastChecked(new Date());
    }
  }, []);

  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, 20000);
    return () => clearInterval(interval);
  }, [checkHealth]);

  if (isHealthy) return null;

  return (
    <div
      role="alert"
      className="w-full bg-gradient-to-r from-red-950/90 via-red-900/95 to-red-950/90 border-b border-red-500/40 text-red-200 px-4 py-2.5 flex items-center justify-between text-xs z-50 sticky top-0 backdrop-blur-md shadow-[0_4px_20px_rgba(239,68,68,0.25)] animate-fade-in"
    >
      <div className="flex items-center gap-2.5 max-w-4xl">
        <div className="p-1 rounded bg-red-500/20 text-red-400 shrink-0 animate-pulse">
          <AlertTriangle size={16} />
        </div>
        <div>
          <span className="font-bold text-red-100 tracking-wide uppercase font-mono mr-2">
            Backend Offline / Unreachable
          </span>
          <span className="text-red-200/90 hidden sm:inline">
            Unable to communicate with the ShieldAI API service. Ensure Flask is running on port 5000.
          </span>
        </div>
      </div>

      <div className="flex items-center gap-2 shrink-0">
        <button
          onClick={checkHealth}
          disabled={checking}
          className="flex items-center gap-1.5 px-3 py-1 rounded bg-red-500/20 hover:bg-red-500/30 border border-red-500/40 text-red-100 font-mono text-[11px] font-semibold transition-all cursor-pointer disabled:opacity-50"
        >
          <RefreshCw size={12} className={checking ? 'animate-spin' : ''} />
          {checking ? 'Checking...' : 'Retry Connection'}
        </button>
      </div>
    </div>
  );
}

