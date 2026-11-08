import React, { Suspense, useState, useEffect } from 'react';
import {
  Shield,
  Sparkles,
  AlertTriangle,
  Users,
  Trash2,
  BarChart3,
  TrendingUp
} from 'lucide-react';
import { useAdminData } from '../hooks/useAdminData';
import LoadingState from './common/LoadingState';
import DashboardStats from './dashboard/DashboardStats';
import ModeratorQueue from './dashboard/ModeratorQueue';
import BehavioralIntelligence from './dashboard/BehavioralIntelligence';
import RepeatOffendersView from './dashboard/RepeatOffendersView';
import DataRetentionPurge from './dashboard/DataRetentionPurge';
import CategoryChart from './dashboard/CategoryChart';
import TrendChart from './dashboard/TrendChart';

const AdvancedAnalytics = React.lazy(() => import('./dashboard/AdvancedAnalytics'));

/**
 * Maps the sidebar activeTab to the Dashboard's own sub-tab key.
 */
function resolveInitialSubTab(sidebarTab) {
  if (sidebarTab === 'behavioral') return 'behavior';
  if (sidebarTab === 'incidents') return 'incidents';
  if (sidebarTab === 'offenders') return 'offenders';
  if (sidebarTab === 'retention') return 'retention';
  return 'overview';
}

export default function Dashboard({ refreshKey, activeTab: sidebarTab, setActiveTab }) {
  const {
    stats, reportsData, conversationsData, profilesData, complaintsData,
    analytics, dailyCounts, anomalies, filters, loading, reportsLoading
  } = useAdminData(refreshKey);

  const [subTab, setSubTab] = useState(() => resolveInitialSubTab(sidebarTab));

  useEffect(() => {
    setSubTab(resolveInitialSubTab(sidebarTab));
  }, [sidebarTab]);

  const handleSubTabClick = (tabKey, sidebarKey) => {
    setSubTab(tabKey);
    if (setActiveTab) {
      setActiveTab(sidebarKey);
    }
  };

  if (loading) {
    return <LoadingState message="Loading Digital Safety Intelligence & Operations Center..." />;
  }

  const currentActive = sidebarTab === 'dashboard' ? subTab : sidebarTab;

  return (
    <div className="space-y-8 animate-fade-in pb-12">
      {/* ── Sub-tab navigation (shown on all SOC command views) ── */}
      {sidebarTab !== 'incidents' && (
        <div className="flex flex-wrap border-b border-border mb-6 pb-0 gap-1">
          <button
            onClick={() => handleSubTabClick('overview', 'dashboard')}
            className={`tab-btn ${currentActive === 'overview' || currentActive === 'dashboard' ? 'active' : ''}`}
          >
            <Shield size={14} />
            Operations Overview
          </button>
          <button
            onClick={() => handleSubTabClick('offenders', 'offenders')}
            className={`tab-btn ${currentActive === 'offenders' ? 'active' : ''}`}
          >
            <Users size={14} />
            Repeat Offenders
          </button>
          <button
            onClick={() => handleSubTabClick('behavior', 'behavioral')}
            className={`tab-btn ${currentActive === 'behavior' || currentActive === 'behavioral' ? 'active' : ''}`}
          >
            <Sparkles size={14} />
            Behavioral Intel
          </button>
          <button
            onClick={() => handleSubTabClick('retention', 'retention')}
            className={`tab-btn ${currentActive === 'retention' ? 'active' : ''}`}
          >
            <Trash2 size={14} />
            Retention & Purge
          </button>
        </div>
      )}

      {/* ── Incidents page: focused moderator queue ── */}
      {(sidebarTab === 'incidents' || subTab === 'incidents') && (
        <div className="space-y-4">
          <div className="flex items-center gap-2 mb-2 p-3 rounded-lg bg-surface border border-border">
            <AlertTriangle size={16} className="text-warning" />
            <p className="text-xs text-text-secondary font-mono">
              Moderation & Triage Queue: Review and update statuses (open, reviewing, resolved, dismissed).
            </p>
          </div>
          <ModeratorQueue
            reportsData={reportsData}
            conversationsData={conversationsData}
            filters={filters}
            loading={reportsLoading}
          />
        </div>
      )}

      {/* ── Repeat Offenders view ── */}
      {(sidebarTab === 'offenders' || (sidebarTab !== 'incidents' && subTab === 'offenders')) && (
        <RepeatOffendersView />
      )}

      {/* ── Data Retention & Purge control ── */}
      {(sidebarTab === 'retention' || (sidebarTab !== 'incidents' && subTab === 'retention')) && (
        <DataRetentionPurge />
      )}

      {/* ── Dashboard overview: stats + Recharts trend/category charts + queue ── */}
      {sidebarTab !== 'incidents' && sidebarTab !== 'offenders' && sidebarTab !== 'retention' && subTab === 'overview' && (
        <div className="space-y-8">
          {/* Key Metric Stat Cards */}
          <DashboardStats stats={stats} />

          {/* Recharts Visualizations Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* 1. Daily Trend Area Chart (Recharts) */}
            <div className="min-w-0">
              <TrendChart dailyCounts={dailyCounts} anomalies={anomalies} />
            </div>

            {/* 2. Flagged Incidents by Threat Category Bar Chart (Recharts) */}
            <div className="min-w-0">
              <CategoryChart
                categories={stats?.categories || []}
                stats={stats}
              />
            </div>
          </div>

          {/* Legacy multi-label breakdown if available */}
          {analytics && (
            <Suspense fallback={<div className="h-24 card flex items-center justify-center text-text-muted text-xs">Loading analytics...</div>}>
              <AdvancedAnalytics analytics={analytics} />
            </Suspense>
          )}

          {/* Moderation Queue */}
          <div className="pt-4 border-t border-border/50">
            <ModeratorQueue
              reportsData={reportsData}
              conversationsData={conversationsData}
              complaintsData={complaintsData}
              filters={filters}
              loading={reportsLoading}
            />
          </div>
        </div>
      )}

      {/* ── Behavioral Intelligence ── */}
      {sidebarTab !== 'incidents' && sidebarTab !== 'offenders' && sidebarTab !== 'retention' && subTab === 'behavior' && (
        <BehavioralIntelligence profilesData={profilesData} />
      )}
    </div>
  );
}
