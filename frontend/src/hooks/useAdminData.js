import { useState, useEffect } from 'react';
import { apiClient } from '../api/client';

export function useAdminData(refreshKey) {
  const [stats, setStats] = useState({ total_flagged: 0, category_breakdown: {}, model: 'baseline' });
  const [recent, setRecent] = useState([]);
  const [dailyCounts, setDailyCounts] = useState(null);
  const [anomalies, setAnomalies] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    
    Promise.all([
      apiClient('/admin/stats'),
      apiClient('/admin/recent?limit=15'),
      apiClient('/admin/daily_counts').catch(() => null),
    ])
      .then(([s, r, dc]) => {
        setStats(s || { total_flagged: 0, category_breakdown: {}, model: 'baseline' });
        setRecent(r || []);
        if (dc) {
          setDailyCounts(dc.daily_counts || []);
          setAnomalies(dc.anomalies || []);
        }
      })
      .catch(() => {
        // Errors are already handled or intercepted by the client (e.g. 401 triggers logout)
      })
      .finally(() => setLoading(false));
  }, [refreshKey]);

  return { stats, recent, dailyCounts, anomalies, loading };
}
