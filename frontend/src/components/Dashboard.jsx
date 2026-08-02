import { useEffect, useState } from 'react'
import { Bar } from 'react-chartjs-2'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Tooltip,
} from 'chart.js'

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip)

const CATEGORY_COLORS = {
  hate_speech: 'rgba(239, 68, 68, 0.8)',
  offensive_language: 'rgba(245, 158, 11, 0.8)',
  none: 'rgba(107, 114, 128, 0.5)',
}

const CATEGORY_LABELS = {
  hate_speech: 'Hate Speech',
  offensive_language: 'Offensive Language',
  none: 'Clean',
}

export default function Dashboard({ refreshKey }) {
  const [stats, setStats] = useState({ total_flagged: 0, category_breakdown: {}, model: 'baseline' })
  const [recent, setRecent] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    Promise.all([
      fetch('/api/admin/stats').then((r) => r.json()),
      fetch('/api/admin/recent?limit=15').then((r) => r.json()),
    ])
      .then(([s, r]) => {
        setStats(s)
        setRecent(r)
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [refreshKey])

  const categories = Object.keys(stats.category_breakdown)
  const chartData = {
    labels: categories.map((c) => CATEGORY_LABELS[c] || c.replace('_', ' ')),
    datasets: [
      {
        data: categories.map((c) => stats.category_breakdown[c]),
        backgroundColor: categories.map((c) => CATEGORY_COLORS[c] || 'rgba(107,114,128,0.5)'),
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
        ticks: { color: 'rgba(255,255,255,0.35)', font: { size: 11 } },
        grid: { color: 'rgba(255,255,255,0.04)' },
      },
      x: {
        ticks: { color: 'rgba(255,255,255,0.5)', font: { size: 11 } },
        grid: { display: false },
      },
    },
  }

  if (loading) {
    return (
      <div className="glass-card p-12 text-center animate-pulse-soft">
        <p className="text-sm text-gray-500">Loading dashboard...</p>
      </div>
    )
  }

  return (
    <div className="space-y-4 animate-fade-in">
      {/* ── Stat cards ── */}
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
        <StatCard label="Flagged Messages" value={stats.total_flagged} />
        <StatCard label="Categories Seen" value={categories.length} />
        <StatCard
          label="Active Model"
          value={stats.model === 'distilbert' ? 'DistilBERT' : 'TF-IDF + LR'}
        />
      </div>

      {/* ── Chart ── */}
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

      {/* ── Recent table ── */}
      <div className="glass-card p-5">
        <p className="section-title">
          <span className="w-1.5 h-1.5 bg-red-500 rounded-full" />
          Recently Flagged
        </p>

        {recent.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-2xl mb-2">📭</p>
            <p className="text-sm text-gray-500">Nothing flagged yet.</p>
            <p className="text-xs text-gray-600 mt-1">Switch to the Analyze tab and submit some text.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-[11px] text-gray-600 uppercase tracking-wider">
                  <th className="text-left py-2 pr-3 font-medium">Preview</th>
                  <th className="text-left py-2 pr-3 font-medium">Category</th>
                  <th className="text-right py-2 font-medium">Confidence</th>
                </tr>
              </thead>
              <tbody>
                {recent.map((r, i) => (
                  <tr key={i} className="border-t border-white/[0.04] hover:bg-white/[0.02] transition-colors">
                    <td className="py-2.5 pr-3 text-gray-300 truncate max-w-[260px]">{r.text_preview}</td>
                    <td className="py-2.5 pr-3">
                      <span className={`badge text-[11px] border ${
                        r.category === 'hate_speech'
                          ? 'text-red-300 bg-red-500/10 border-red-500/20'
                          : r.category === 'offensive_language'
                          ? 'text-orange-300 bg-orange-500/10 border-orange-500/20'
                          : 'text-gray-400 bg-white/5 border-white/10'
                      }`}>
                        {CATEGORY_LABELS[r.category] || r.category}
                      </span>
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
      <p className="text-[11px] text-gray-500 uppercase tracking-wider mb-1">{label}</p>
      <p className="text-xl font-semibold text-gray-200">{value}</p>
    </div>
  )
}
