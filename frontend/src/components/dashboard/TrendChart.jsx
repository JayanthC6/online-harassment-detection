import PropTypes from 'prop-types';
import { Line } from 'react-chartjs-2';
import Card from '../common/Card';

export default function TrendChart({ dailyCounts, anomalies }) {
  if (!dailyCounts || dailyCounts.length === 0) return null;

  const trendData = {
    labels: dailyCounts.map((d) => d.date),
    datasets: [
      {
        label: 'Flagged reports',
        data: dailyCounts.map((d) => d.count),
        borderColor: '#4f46e5',
        backgroundColor: 'rgba(79, 70, 229, 0.06)',
        fill: true,
        tension: 0.3,
        pointBackgroundColor: dailyCounts.map((d) => {
          const isAnomaly = anomalies.some((a) => a.date === d.date);
          return isAnomaly ? '#dc2626' : '#4f46e5';
        }),
        pointBorderColor: dailyCounts.map((d) => {
          const isAnomaly = anomalies.some((a) => a.date === d.date);
          return isAnomaly ? '#dc2626' : '#4f46e5';
        }),
        pointRadius: dailyCounts.map((d) => {
          const isAnomaly = anomalies.some((a) => a.date === d.date);
          return isAnomaly ? 6 : 3;
        }),
      },
    ],
  };

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
  };

  return (
    <Card className="p-5">
      <p className="section-title">
        <span className="w-1.5 h-1.5 bg-indigo-500 rounded-full" />
        Daily Trend (Last 30 Days)
      </p>
      <div className="h-52">
        <Line data={trendData} options={trendOptions} />
      </div>
    </Card>
  );
}

TrendChart.propTypes = {
  dailyCounts: PropTypes.arrayOf(
    PropTypes.shape({
      date: PropTypes.string.isRequired,
      count: PropTypes.number.isRequired,
    })
  ),
  anomalies: PropTypes.arrayOf(
    PropTypes.shape({
      date: PropTypes.string.isRequired,
    })
  ).isRequired,
};
