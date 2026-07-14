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
  hate_speech: '#E24B4A',
  offensive_language: '#EF9F27',
  none: '#888780',
}

export default function Dashboard({ refreshKey }) {
  const [stats, setStats] = useState({ total_flagged: 0, category_breakdown: {} })
  const [recent, setRecent] = useState([])

  useEffect(() => {
    fetch('/api/admin/stats').then((r) => r.json()).then(setStats).catch(() => {})
    fetch('/api/admin/recent?limit=10').then((r) => r.json()).then(setRecent).catch(() => {})
  }, [refreshKey])

  const categories = Object.keys(stats.category_breakdown)
  const chartData = {
    labels: categories.map((c) => c.replace('_', ' ')),
    datasets: [
      {
        data: categories.map((c) => stats.category_breakdown[c]),
        backgroundColor: categories.map((c) => CATEGORY_COLORS[c] || '#888780'),
        borderRadius: 4,
        maxBarThickness: 40,
      },
    ],
  }

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
        <StatCard label="Flagged messages" value={stats.total_flagged} />
        <StatCard label="Categories seen" value={categories.length} />
        <StatCard label="Model" value="TF-IDF + LR" />
      </div>

      {categories.length > 0 && (
        <div className="bg-white border border-gray-200 rounded-xl p-4">
          <p className="text-sm text-gray-600 mb-2">Flagged content by category</p>
          <div className="h-48">
            <Bar
              data={chartData}
              options={{
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { y: { beginAtZero: true } },
              }}
            />
          </div>
        </div>
      )}

      <div className="bg-white border border-gray-200 rounded-xl p-4">
        <p className="text-sm text-gray-600 mb-2">Recently flagged</p>
        {recent.length === 0 ? (
          <p className="text-sm text-gray-400">Nothing flagged yet. Try the analyzer above.</p>
        ) : (
          <table className="w-full text-sm">
            <tbody>
              {recent.map((r, i) => (
                <tr key={i} className="border-t border-gray-100">
                  <td className="py-2 pr-2 truncate max-w-[240px]">{r.text_preview}</td>
                  <td className="py-2 pr-2 text-gray-500">{r.category.replace('_', ' ')}</td>
                  <td className="py-2 text-right text-gray-500">{Math.round(r.confidence * 100)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}

function StatCard({ label, value }) {
  return (
    <div className="bg-white border border-gray-200 rounded-xl p-4">
      <p className="text-xs text-gray-500 mb-1">{label}</p>
      <p className="text-xl font-medium text-gray-900">{value}</p>
    </div>
  )
}
