import { useEffect, useState } from 'react'
import { Bar, Line } from 'react-chartjs-2'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
} from 'chart.js'

ChartJS.register(CategoryScale, LinearScale, BarElement, PointElement, LineElement, Filler, Tooltip)

const CATEGORY_COLORS = {
  hate_speech: 'rgba(220, 38, 38, 0.75)',
  offensive_language: 'rgba(217, 119, 6, 0.75)',
  none: 'rgba(156, 163, 175, 0.5)',
}

const CATEGORY_LABELS = {
  hate_speech: 'Hate Speech',
  offensive_language: 'Offensive Language',
  none: 'Clean',
}

export default function Dashboard({ refreshKey, token, onLogout }) {
  const [stats, setStats] = useState({ total_flagged: 0, category_breakdown: {}, model: 'baseline' })
  const [recent, setRecent] = useState([])
  const [dailyCounts, setDailyCounts] = useState(null)
  const [anomalies, setAnomalies] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    const headers = { 'Authorization': `Bearer ${token}` }
    
    Promise.all([
      fetch('/api/admin/stats', { headers }).then(async (r) => {
        if (r.status === 401) throw new Error('Unauthorized')
        return r.json()
      }),
      fetch('/api/admin/recent?limit=15', { headers }).then(async (r) => {
        if (r.status === 401) throw new Error('Unauthorized')
        return r.json()
      }),
      fetch('/api/admin/daily_counts', { headers }).then(async (r) => {
        if (r.status === 401) throw new Error('Unauthorized')
        return r.json()
      }).catch(() => null),
    ])
      .then(([s, r, dc]) => {
        setStats(s)
        setRecent(r)
        if (dc) {
          setDailyCounts(dc.daily_counts || [])
          setAnomalies(dc.anomalies || [])
        }
      })
      .catch((err) => {
        if (err.message === 'Unauthorized' && onLogout) {
          onLogout()
        }
      })
      .finally(() => setLoading(false))
  }, [refreshKey, token, onLogout])

  const categories = Object.keys(stats.category_breakdown)
  const chartData = {
    labels: categories.map((c) => CATEGORY_LABELS[c] || c.replace('_', ' ')),
    datasets: [
      {
        data: categories.map((c) => stats.category_breakdown[c]),
        backgroundColor: categories.map((c) => CATEGORY_COLORS[c] || 'rgba(156,163,175,0.5)'),
        borderRadius: 6,
        maxBarThickness: 48,
      },
    ],
  }

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: false } },
    scales: {
      y: {
        beginAtZero: true,
        ticks: { color: '#6b7280', font: { size: 11 } },
        grid: { color: 'rgba(0,0,0,0.04)' },
      },
      x: {
        ticks: { color: '#374151', font: { size: 11 } },
        grid: { display: false },
      },
    },
  }

  /* ── Trend chart data ── */
  const trendData = dailyCounts ? {
    labels: dailyCounts.map((d) => d.date),
    datasets: [
      {
        label: 'Flagged reports',
        data: dailyCounts.map((d) => d.count),
        borderColor: '#4f46e5',
        backgroundColor: 'rgba(79, 70, 229, 0.06)',
        fill: true,
        tension: 0.3,
        pointRadius: 3,
        pointBackgroundColor: dailyCounts.map((d) => {
          const isAnomaly = anomalies.some((a) => a.date === d.date)
          return isAnomaly ? '#dc2626' : '#4f46e5'
        }),
        pointBorderColor: dailyCounts.map((d) => {
          const isAnomaly = anomalies.some((a) => a.date === d.date)
          return isAnomaly ? '#dc2626' : '#4f46e5'
        }),
        pointRadius: dailyCounts.map((d) => {
          const isAnomaly = anomalies.some((a) => a.date === d.date)
          return isAnomaly ? 6 : 3
        }),
      },
    ],
  } : null

  const trendOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: false } },
    scales: {
      y: {
        beginAtZero: true,
        ticks: { color: '#6b7280', font: { size: 11 }, stepSize: 1 },
        grid: { color: 'rgba(0,0,0,0.04)' },
      },
      x: {
        ticks: { color: '#374151', font: { size: 11 }, maxRotation: 45 },
        grid: { display: false },
      },
    },
  }

  if (loading) {
    return (
      <div className="glass-card p-12 text-center animate-pulse-soft">
        <p className="text-sm text-gray-400">Loading dashboard...</p>
      </div>
    )
  }

  return (
    <div className="space-y-4 animate-fade-in">

      {/* ── Anomaly banner ── */}
      {anomalies.length > 0 && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 animate-slide-up">
          <p className="text-sm font-semibold text-amber-800 flex items-center gap-2">
            <span>⚠️</span> Unusual Activity Detected
          </p>
          {anomalies.map((a, i) => (
            <p key={i} className="text-xs text-amber-700 mt-1">
              Spike on <strong>{a.date}</strong>: {a.count} reports vs {a.avg.toFixed(1)} avg (z-score: {a.z_score.toFixed(1)})
            </p>
          ))}
        </div>
      )}

      {/* ── Stat cards ── */}
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
        <StatCard label="Flagged Messages" value={stats.total_flagged} />
        <StatCard label="Categories Seen" value={categories.length} />
        <StatCard
          label="Active Model"
          value={stats.model === 'distilbert' ? 'DistilBERT' : 'TF-IDF + LR'}
        />
      </div>

      {/* ── Category chart ── */}
      {categories.length > 0 && (
        <div className="glass-card p-5">
          <p className="section-title">
            <span className="w-1.5 h-1.5 bg-orange-500 rounded-full" />
            Flagged Content by Category
          </p>
          <div className="h-52">
            <Bar data={chartData} options={chartOptions} />
          </div>
        </div>
      )}

      {/* ── Trend chart ── */}
      {trendData && dailyCounts.length > 0 && (
        <div className="glass-card p-5">
          <p className="section-title">
            <span className="w-1.5 h-1.5 bg-indigo-500 rounded-full" />
            Daily Trend (Last 30 Days)
          </p>
          <div className="h-52">
            <Line data={trendData} options={trendOptions} />
          </div>
        </div>
      )}

      {/* ── Recent table ── */}
      <div className="glass-card p-5">
        <p className="section-title">
          <span className="w-1.5 h-1.5 bg-red-500 rounded-full" />
          Recently Flagged (sorted by risk)
        </p>

        {recent.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-2xl mb-2">📭</p>
            <p className="text-sm text-gray-400">Nothing flagged yet.</p>
            <p className="text-xs text-gray-300 mt-1">Switch to the Analyze tab and submit some text.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-[11px] text-gray-500 uppercase tracking-wider">
                  <th className="text-left py-2 pr-3 font-medium">Preview</th>
                  <th className="text-left py-2 pr-3 font-medium">Category</th>
                  <th className="text-center py-2 pr-3 font-medium">Risk</th>
                  <th className="text-right py-2 font-medium">Confidence</th>
                </tr>
              </thead>
              <tbody>
                {recent.map((r, i) => (
                  <tr key={i} className="border-t border-gray-100 hover:bg-gray-50 transition-colors">
                    <td className="py-2.5 pr-3 text-gray-700 truncate max-w-[220px]">
                      {r.text_preview}
                      {r.cluster_id && (
                        <span className="ml-2 inline-flex items-center text-[10px] text-amber-700 bg-amber-50 border border-amber-200 rounded-full px-1.5 py-0.5">🔗 Similar</span>
                      )}
                    </td>
                    <td className="py-2.5 pr-3">
                      <span className={`badge text-[11px] border ${
                        r.category === 'hate_speech'
                          ? 'text-red-700 bg-red-50 border-red-200'
                          : r.category === 'offensive_language'
                          ? 'text-amber-700 bg-amber-50 border-amber-200'
                          : 'text-gray-500 bg-gray-50 border-gray-200'
                      }`}>
                        {CATEGORY_LABELS[r.category] || r.category}
                      </span>
                    </td>
                    <td className="py-2.5 pr-3 text-center">
                      {r.risk_score != null && (
                        <span className={`badge text-[11px] border ${
                          r.risk_score >= 70 ? 'bg-red-50 text-red-700 border-red-200'
                          : r.risk_score >= 40 ? 'bg-amber-50 text-amber-700 border-amber-200'
                          : 'bg-gray-50 text-gray-500 border-gray-200'
                        }`}>
                          {Math.round(r.risk_score)}
                        </span>
                      )}
                    </td>
                    <td className="py-2.5 text-right text-gray-500 font-mono text-xs">
                      {Math.round(r.confidence * 100)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}

function StatCard({ label, value }) {
  return (
    <div className="stat-card">
      <p className="text-[11px] text-gray-400 uppercase tracking-wider mb-1">{label}</p>
      <p className="text-xl font-semibold text-gray-800">{value}</p>
    </div>
  )
}
