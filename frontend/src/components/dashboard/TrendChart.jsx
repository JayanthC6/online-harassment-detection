import React from 'react';
import PropTypes from 'prop-types';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from 'recharts';
import { Activity } from 'lucide-react';
import Card from '../common/Card';

export default function TrendChart({ dailyCounts, anomalies }) {
  if (!dailyCounts || dailyCounts.length === 0) return null;

  const anomalyDates = new Set((anomalies || []).map((a) => a.date));

  const data = dailyCounts.map((d) => {
    const date = new Date(d.date);
    const formattedDate = date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
    const isAnomaly = anomalyDates.has(d.date);
    return {
      date: formattedDate,
      rawDate: d.date,
      count: d.count,
      isAnomaly,
    };
  });

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const item = payload[0].payload;
      return (
        <div className="bg-[#0E121E] border border-border p-3 rounded-lg shadow-xl text-xs font-mono">
          <p className="text-text-muted mb-1">{item.rawDate}</p>
          <p className="text-text-primary font-bold text-sm">
            <span className="text-cyan-400">●</span> {item.count} Incidents
          </p>
          {item.isAnomaly && (
            <p className="text-rose-500 font-bold mt-1">⚠️ High-Volume Spike Anomaly</p>
          )}
        </div>
      );
    }
    return null;
  };

  return (
    <Card className="p-5 bg-black/40 border border-border/50 rounded-xl shadow-[inset_0_0_15px_rgba(0,0,0,0.5)]">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-xs font-bold text-text-muted font-mono uppercase tracking-wider flex items-center gap-1.5 drop-shadow-[0_0_2px_rgba(255,255,255,0.1)]">
          <Activity size={14} className="text-cyan-400" />
          Incident Activity & Threat Volume Trends (Recharts)
        </h3>
        {anomalies && anomalies.length > 0 && (
          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-rose-500/20 text-rose-400 border border-rose-500/40">
            {anomalies.length} Spike Anomalies Detected
          </span>
        )}
      </div>
      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="trendGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#00F2FE" stopOpacity={0.35} />
                <stop offset="95%" stopColor="#00F2FE" stopOpacity={0.0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.07)" vertical={false} />
            <XAxis
              dataKey="date"
              stroke="#64748B"
              fontSize={11}
              tickLine={false}
              axisLine={{ stroke: 'rgba(255,255,255,0.1)' }}
            />
            <YAxis
              stroke="#64748B"
              fontSize={11}
              tickLine={false}
              axisLine={false}
              allowDecimals={false}
            />
            <Tooltip content={<CustomTooltip />} />
            <Area
              type="monotone"
              dataKey="count"
              stroke="#00F2FE"
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#trendGradient)"
              dot={(props) => {
                const { cx, cy, payload } = props;
                if (payload.isAnomaly) {
                  return (
                    <circle
                      key={`dot-${payload.rawDate}`}
                      cx={cx}
                      cy={cy}
                      r={5}
                      fill="#F43F5E"
                      stroke="#FFFFFF"
                      strokeWidth={1.5}
                    />
                  );
                }
                return (
                  <circle
                    key={`dot-${payload.rawDate}`}
                    cx={cx}
                    cy={cy}
                    r={3}
                    fill="#00F2FE"
                    stroke="#060913"
                    strokeWidth={1.5}
                  />
                );
              }}
              activeDot={{ r: 6, fill: '#00F2FE', stroke: '#FFFFFF', strokeWidth: 2 }}
            />
          </AreaChart>
        </ResponsiveContainer>
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
  ).isRequired,
  anomalies: PropTypes.arrayOf(
    PropTypes.shape({
      date: PropTypes.string.isRequired,
    })
  ),
};
