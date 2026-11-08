import React from 'react';
import PropTypes from 'prop-types';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Cell,
} from 'recharts';
import Card from '../common/Card';

const CATEGORY_COLORS = {
  threat: '#EF4444',            // Critical Red
  sextortion: '#DC2626',        // Critical Deep Red
  blackmail: '#DC2626',
  hate_speech: '#F43F5E',       // Red/Rose
  phishing: '#F97316',          // High Orange
  scam: '#F59E0B',              // Medium Amber
  abusive_language: '#F59E0B',  // Amber
  harassment: '#F97316',        // Orange
  clean: '#10B981',             // Low Green
  none: '#10B981',
};

const CATEGORY_LABELS = {
  threat: 'Threat',
  sextortion: 'Sextortion',
  blackmail: 'Extortion',
  hate_speech: 'Hate Speech',
  phishing: 'Phishing',
  scam: 'Scam',
  abusive_language: 'Abusive',
  harassment: 'Harassment',
  clean: 'Clean',
  none: 'Clean',
};

export default function CategoryChart({ categories, stats }) {
  const cats = (categories && categories.length > 0)
    ? categories
    : Object.keys(stats?.category_breakdown || stats?.breakdown || {
        threat: 0,
        sextortion: 0,
        phishing: 0,
        scam: 0,
        harassment: 0,
        abusive_language: 0
      });

  if (!cats || cats.length === 0) return null;

  const data = cats.map((cat) => {
    const label = CATEGORY_LABELS[cat.toLowerCase()] || cat.replace(/_/g, ' ');
    const count = stats?.category_breakdown?.[cat] || stats?.breakdown?.[cat] || 0;
    const color = CATEGORY_COLORS[cat.toLowerCase()] || '#00F2FE';
    return { category: label, rawCat: cat, count, color };
  });

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const item = payload[0].payload;
      return (
        <div className="bg-[#0E121E] border border-border p-2.5 rounded-lg shadow-xl text-xs font-mono">
          <p className="text-text-muted mb-0.5">{item.category}</p>
          <p className="text-text-primary font-bold text-sm">
            <span style={{ color: item.color }}>●</span> {item.count} Reports
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <Card className="p-5 bg-black/40 border border-border/50 rounded-xl shadow-[inset_0_0_15px_rgba(0,0,0,0.5)]">
      <h3 className="text-xs font-bold text-text-muted font-mono uppercase tracking-wider mb-4 flex items-center gap-1.5 drop-shadow-[0_0_2px_rgba(255,255,255,0.1)]">
        <span className="w-1.5 h-1.5 bg-blue rounded-full shadow-[0_0_5px_rgba(0,242,254,0.5)]" />
        Flagged Incidents by Threat Category (Recharts)
      </h3>
      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 25 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.07)" vertical={false} />
            <XAxis
              dataKey="category"
              stroke="#64748B"
              fontSize={11}
              interval={0}
              angle={-25}
              textAnchor="end"
              tickLine={false}
            />
            <YAxis
              stroke="#64748B"
              fontSize={11}
              tickLine={false}
              axisLine={false}
              allowDecimals={false}
            />
            <Tooltip content={<CustomTooltip />} />
            <Bar dataKey="count" radius={[4, 4, 0, 0]} maxBarSize={44}>
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
}

CategoryChart.propTypes = {
  categories: PropTypes.arrayOf(PropTypes.string).isRequired,
  stats: PropTypes.shape({
    category_breakdown: PropTypes.objectOf(PropTypes.number).isRequired,
  }).isRequired,
};
