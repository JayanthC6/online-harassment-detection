import { useState, useEffect, useCallback } from 'react';
import { apiClient } from '../api/client';

export function useAdminData(refreshKey) {
  const [stats, setStats] = useState(null);
  const [reportsData, setReportsData] = useState({ reports: [], total: 0, page: 1, total_pages: 1 });
  const [conversationsData, setConversationsData] = useState({ conversations: [], total: 0, page: 1, total_pages: 1 });
  const [profilesData, setProfilesData] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  
  // Daily trends
  const [dailyCounts, setDailyCounts] = useState([]);
  const [anomalies, setAnomalies] = useState([]);

  const [loading, setLoading] = useState(true);
  const [reportsLoading, setReportsLoading] = useState(true);

  // Filters state
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [sortBy, setSortBy] = useState('logged_at');
  const [sortOrder, setSortOrder] = useState('desc');
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('');
  const [riskLevel, setRiskLevel] = useState('');

  const fetchStats = useCallback(async () => {
    try {
      const [s, a, d] = await Promise.all([
        apiClient('/admin/stats'),
        apiClient('/admin/analytics').catch(() => null),
        apiClient('/admin/daily_counts').catch(() => null)
      ]);
      setStats(s);
      setAnalytics(a);
      if (d) {
        setDailyCounts(d.daily_counts || []);
        setAnomalies(d.anomalies || []);
      }
    } catch (e) {
      console.error(e);
    }
  }, []);

  const fetchReports = useCallback(async () => {
    setReportsLoading(true);
    try {
      const query = new URLSearchParams({
        page,
        page_size: pageSize,
        sort_by: sortBy,
        sort_order: sortOrder,
        search,
        category,
        risk_level: riskLevel
      }).toString();
      
      const r = await apiClient(`/admin/reports?${query}`);
      setReportsData(r);
    } catch (e) {
      console.error(e);
    } finally {
      setReportsLoading(false);
    }
  }, [page, pageSize, sortBy, sortOrder, search, category, riskLevel]);

  const fetchConversations = useCallback(async () => {
    try {
      const query = new URLSearchParams({
        page,
        page_size: pageSize,
        sort_by: sortBy,
        sort_order: sortOrder
      }).toString();
      
      const r = await apiClient(`/admin/conversations?${query}`);
      setConversationsData(r);
    } catch (e) {
      console.error(e);
    }
  }, [page, pageSize, sortBy, sortOrder]);

  const fetchProfiles = useCallback(async () => {
    try {
      const r = await apiClient('/admin/profiles');
      setProfilesData(r.profiles);
    } catch (e) {
      console.error(e);
    }
  }, []);

  const [complaintsData, setComplaintsData] = useState([]);
  
  const fetchComplaints = useCallback(async () => {
    try {
      const r = await apiClient('/admin/complaints');
      setComplaintsData(r.complaints || []);
    } catch (e) {
      console.error(e);
    }
  }, []);

  // Initial load
  useEffect(() => {
    setLoading(true);
    Promise.all([fetchStats(), fetchReports(), fetchConversations(), fetchProfiles(), fetchComplaints()]).finally(() => setLoading(false));
  }, [refreshKey, fetchStats, fetchReports, fetchConversations, fetchProfiles, fetchComplaints]);

  return {
    stats,
    reportsData,
    conversationsData,
    profilesData,
    complaintsData,
    analytics,
    dailyCounts,
    anomalies,
    loading,
    reportsLoading,
    filters: {
      page, setPage,
      pageSize, setPageSize,
      sortBy, setSortBy,
      sortOrder, setSortOrder,
      search, setSearch,
      category, setCategory,
      riskLevel, setRiskLevel
    }
  };
}
