import React from 'react';
import PropTypes from 'prop-types';

export default function RiskGauge({ score = 0, size = 200, label = 'Risk Score', isUnsupported = false }) {
  const safeScore = Math.min(100, Math.max(0, Math.round(score)));

  // Risk color mapping
  const getColor = (s) => {
    if (isUnsupported) return { hex: '#A855F7', name: 'Unsupported', bg: 'rgba(168, 85, 247, 0.15)' };
    if (s >= 80) return { hex: '#EF4444', name: 'Critical', bg: 'rgba(239, 68, 68, 0.15)' };
    if (s >= 55) return { hex: '#F97316', name: 'High', bg: 'rgba(249, 115, 22, 0.15)' };
    if (s >= 30) return { hex: '#F59E0B', name: 'Medium', bg: 'rgba(245, 158, 11, 0.15)' };
    return { hex: '#10B981', name: 'Low', bg: 'rgba(16, 185, 129, 0.15)' };
  };

  const riskInfo = getColor(safeScore);

  // SVG Gauge calculations
  const radius = 70;
  const strokeWidth = 14;
  const arcLength = Math.PI * radius; // Half circumference
  const strokeDashoffset = isUnsupported ? arcLength : (arcLength - (arcLength * safeScore) / 100);

  return (
    <div className="flex flex-col items-center justify-center relative p-3">
      <div className="relative" style={{ width: size, height: size * 0.62 }}>
        <svg
          viewBox="0 0 180 105"
          className="w-full h-full overflow-visible"
        >
          <defs>
            <linearGradient id="gaugeBgGradient" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#10B981" stopOpacity="0.25" />
              <stop offset="35%" stopColor="#F59E0B" stopOpacity="0.25" />
              <stop offset="70%" stopColor="#F97316" stopOpacity="0.25" />
              <stop offset="100%" stopColor="#EF4444" stopOpacity="0.25" />
            </linearGradient>

            <linearGradient id="gaugeActiveGradient" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#10B981" />
              <stop offset="35%" stopColor="#F59E0B" />
              <stop offset="70%" stopColor="#F97316" />
              <stop offset="100%" stopColor="#EF4444" />
            </linearGradient>

            <filter id="gaugeGlow" x="-20%" y="-20%" width="140%" height="140%">
              <feDropShadow dx="0" dy="0" stdDeviation="4" floodColor={riskInfo.hex} floodOpacity="0.5" />
            </filter>
          </defs>

          {/* Background Track */}
          <path
            d="M 20 90 A 70 70 0 0 1 160 90"
            fill="none"
            stroke="rgba(255, 255, 255, 0.08)"
            strokeWidth={strokeWidth}
            strokeLinecap="round"
          />

          {/* Colored Background Hint */}
          <path
            d="M 20 90 A 70 70 0 0 1 160 90"
            fill="none"
            stroke="url(#gaugeBgGradient)"
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            opacity="0.4"
          />

          {/* Active Value Arc */}
          <path
            d="M 20 90 A 70 70 0 0 1 160 90"
            fill="none"
            stroke={riskInfo.hex}
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            strokeDasharray={arcLength}
            strokeDashoffset={strokeDashoffset}
            filter="url(#gaugeGlow)"
            className="transition-all duration-1000 ease-out"
          />

          {/* Ticks */}
          <text x="18" y="102" fill="#64748B" fontSize="8" fontFamily="monospace" textAnchor="middle">0</text>
          <text x="65" y="32" fill="#64748B" fontSize="7" fontFamily="monospace" textAnchor="middle">30</text>
          <text x="115" y="32" fill="#64748B" fontSize="7" fontFamily="monospace" textAnchor="middle">70</text>
          <text x="162" y="102" fill="#64748B" fontSize="8" fontFamily="monospace" textAnchor="middle">100</text>
        </svg>

        {/* Center Readout */}
        <div className="absolute inset-x-0 bottom-0 flex flex-col items-center justify-center text-center">
          <div
            className="text-4xl font-extrabold font-mono tracking-tight leading-none"
            style={{ color: riskInfo.hex, textShadow: `0 0 15px ${riskInfo.hex}66` }}
          >
            {isUnsupported ? '—' : safeScore}
          </div>
          <span
            className="mt-1 text-[11px] font-mono font-bold uppercase tracking-wider px-2 py-0.5 rounded"
            style={{ color: riskInfo.hex, backgroundColor: riskInfo.bg, border: `1px solid ${riskInfo.hex}55` }}
          >
            {isUnsupported ? 'UNVERIFIED' : `${riskInfo.name} Risk`}
          </span>
        </div>
      </div>
      <p className="text-[11px] font-mono text-text-muted mt-2 tracking-wide uppercase">{isUnsupported ? 'Language Unverified' : label}</p>
    </div>
  );
}

RiskGauge.propTypes = {
  score: PropTypes.number,
  size: PropTypes.number,
  label: PropTypes.string,
  isUnsupported: PropTypes.bool,
};

