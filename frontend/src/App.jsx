import { useState } from 'react'
import AnalyzeForm from './components/AnalyzeForm'
import Dashboard from './components/Dashboard'

export default function App() {
  const [refreshKey, setRefreshKey] = useState(0)

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-2xl mx-auto space-y-6">
        <header>
          <h1 className="text-xl font-semibold text-gray-900">Online Harassment Detection</h1>
          <p className="text-sm text-gray-500">Paste a message below to check it, or review flagged activity.</p>
        </header>

        <AnalyzeForm onNewResult={() => setRefreshKey((k) => k + 1)} />
        <Dashboard refreshKey={refreshKey} />
      </div>
    </div>
  )
}
