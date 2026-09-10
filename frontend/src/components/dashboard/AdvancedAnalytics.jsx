import PropTypes from 'prop-types';
import { Bar } from 'react-chartjs-2';

import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Tooltip,
} from 'chart.js';

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip);

export default function AdvancedAnalytics({ analytics }) {
  if (!analytics) return null;

  const { risk_distribution, label_frequency, top_combinations } = analytics;

  // Risk Chart
  const riskLabels = ['High Risk', 'Medium Risk', 'Low Risk'];
  const riskData = {
    labels: riskLabels,
    datasets: [{
      data: [risk_distribution?.high || 0, risk_distribution?.medium || 0, risk_distribution?.low || 0],
      backgroundColor: ['#F43F5E', '#F59E0B', '#10B981'],
      borderRadius: 0,
      barThickness: 24,
    }]
  };

  // Multi-Label Chart
  const labelFreqEntries = Object.entries(label_frequency || {}).sort((a, b) => b[1] - a[1]).slice(0, 5);
  const freqData = {
    labels: labelFreqEntries.map(e => e[0].replace('_', ' ')),
    datasets: [{
      data: labelFreqEntries.map(e => e[1]),
      backgroundColor: '#00F2FE',
      borderRadius: 0,
      barThickness: 24,
    }]
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { 
      legend: { display: false },
      tooltip: {
        backgroundColor: '#0E121E',
        titleColor: '#F1F5F9',
        bodyColor: '#94A3B8',
        borderColor: '#1E293B',
        borderWidth: 1,
        padding: 12,
        titleFont: { size: 13, family: 'monospace' },
        bodyFont: { size: 13, family: 'monospace' },
        cornerRadius: 0,
      }
    },
    scales: {
      y: { 
        beginAtZero: true, 
        grid: { color: 'rgba(51, 65, 85, 0.5)' },
        border: { display: false },
        ticks: { font: { family: 'monospace', size: 11 }, color: '#64748b' }
      },
      x: { 
        grid: { display: false },
        border: { display: false },
        ticks: { font: { family: 'monospace', size: 11 }, color: '#64748b' }
      }
    }
  };

  return (
    <div className="space-y-4">
      <h2 className="text-sm font-bold text-white font-display uppercase tracking-wider mb-2 drop-shadow-[0_0_5px_rgba(255,255,255,0.3)]">Analytics Overview</h2>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-black/40 p-5 border border-border/50 rounded-xl shadow-[inset_0_0_15px_rgba(0,0,0,0.5)]">
          <h3 className="text-xs font-bold text-text-muted font-mono uppercase tracking-wider mb-6 drop-shadow-[0_0_2px_rgba(255,255,255,0.1)]">Risk Distribution</h3>
          <div className="h-56">
            <Bar data={riskData} options={chartOptions} />
          </div>
        </div>
        
        <div className="bg-black/40 p-5 border border-border/50 rounded-xl shadow-[inset_0_0_15px_rgba(0,0,0,0.5)]">
          <h3 className="text-xs font-bold text-text-muted font-mono uppercase tracking-wider mb-6 drop-shadow-[0_0_2px_rgba(255,255,255,0.1)]">Most Common Categories</h3>
          <div className="h-56">
            {labelFreqEntries.length > 0 ? (
              <Bar data={freqData} options={chartOptions} />
            ) : (
              <div className="h-full flex items-center justify-center text-slate-500 font-mono text-sm">No data</div>
            )}
          </div>
        </div>

        <div className="bg-black/40 p-5 border border-border/50 rounded-xl shadow-[inset_0_0_15px_rgba(0,0,0,0.5)] flex flex-col">
          <h3 className="text-xs font-bold text-text-muted font-mono uppercase tracking-wider mb-4 drop-shadow-[0_0_2px_rgba(255,255,255,0.1)]">Top Label Combinations</h3>
          <div className="flex-1 overflow-y-auto pr-2 space-y-2">
            {top_combinations && Object.keys(top_combinations).length > 0 ? (
              Object.entries(top_combinations).sort((a, b) => b[1] - a[1]).map(([combo, count]) => (
                <div key={combo} className="flex justify-between items-center text-sm p-3 bg-black/60 border border-border/50 rounded-md shadow-inner">
                  <span className="text-blue font-mono truncate mr-2 drop-shadow-[0_0_2px_rgba(0,242,254,0.3)]" title={combo}>{combo.replace(/,/g, ' + ')}</span>
                  <span className="font-bold text-text-secondary bg-black/40 px-2 py-1 border border-border/50 tabular-nums rounded">{count}</span>
                </div>
              ))
            ) : (
              <div className="h-full flex items-center justify-center text-slate-500 font-mono text-sm">No data</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

AdvancedAnalytics.propTypes = {
  analytics: PropTypes.shape({
    risk_distribution: PropTypes.object,
    confidence_distribution: PropTypes.object,
    model_usage: PropTypes.object,
    label_frequency: PropTypes.object,
    top_combinations: PropTypes.object
  })
};
