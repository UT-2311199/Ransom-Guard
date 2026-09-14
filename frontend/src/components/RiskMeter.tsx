import React from 'react';
import { motion } from 'framer-motion';
import { cn } from '../utils/helpers';
import type { ThreatLevel } from '../context/AppContext';

interface RiskMeterProps {
  score: number;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
  className?: string;
}

function getThreatFromScore(score: number): ThreatLevel {
  if (score >= 80) return 'critical';
  if (score >= 60) return 'high';
  if (score >= 40) return 'medium';
  if (score >= 20) return 'low';
  return 'safe';
}

const levelColors: Record<ThreatLevel, { primary: string; glow: string; text: string }> = {
  critical: { primary: '#EF4444', glow: 'rgba(239,68,68,0.4)', text: 'text-red-400' },
  high: { primary: '#F97316', glow: 'rgba(249,115,22,0.4)', text: 'text-orange-400' },
  medium: { primary: '#F59E0B', glow: 'rgba(245,158,11,0.4)', text: 'text-yellow-400' },
  low: { primary: '#3B82F6', glow: 'rgba(59,130,246,0.4)', text: 'text-blue-400' },
  safe: { primary: '#10B981', glow: 'rgba(16,185,129,0.4)', text: 'text-emerald-400' },
};

export const RiskMeter: React.FC<RiskMeterProps> = ({
  score,
  size = 'md',
  showLabel = true,
  className,
}) => {
  const level = getThreatFromScore(score);
  const { primary, glow, text } = levelColors[level];

  const sizes = {
    sm: { radius: 36, stroke: 6, fontSize: 'text-xl', labelSize: 'text-xs' },
    md: { radius: 54, stroke: 8, fontSize: 'text-3xl', labelSize: 'text-sm' },
    lg: { radius: 72, stroke: 10, fontSize: 'text-4xl', labelSize: 'text-base' },
  };

  const { radius, stroke, fontSize, labelSize } = sizes[size];
  const circumference = 2 * Math.PI * radius;
  const svgSize = (radius + stroke + 4) * 2;
  const center = svgSize / 2;
  const dashOffset = circumference - (score / 100) * circumference;

  return (
    <div className={cn('flex flex-col items-center', className)}>
      <div className="relative" style={{ width: svgSize, height: svgSize }}>
        <svg width={svgSize} height={svgSize} className="-rotate-90">
          {/* Track */}
          <circle
            cx={center}
            cy={center}
            r={radius}
            fill="none"
            stroke="#1E293B"
            strokeWidth={stroke}
          />
          {/* Gradient definition */}
          <defs>
            <linearGradient id={`riskGrad-${score}`} x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor={primary} stopOpacity="0.6" />
              <stop offset="100%" stopColor={primary} />
            </linearGradient>
          </defs>
          {/* Progress arc */}
          <motion.circle
            cx={center}
            cy={center}
            r={radius}
            fill="none"
            stroke={`url(#riskGrad-${score})`}
            strokeWidth={stroke}
            strokeLinecap="round"
            strokeDasharray={circumference}
            initial={{ strokeDashoffset: circumference }}
            animate={{ strokeDashoffset: dashOffset }}
            transition={{ duration: 1.5, ease: 'easeOut' }}
            style={{ filter: `drop-shadow(0 0 6px ${glow})` }}
          />
        </svg>
        {/* Center content */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <motion.span
            className={cn('font-bold font-mono', fontSize, text)}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5 }}
          >
            {Math.round(score)}
          </motion.span>
          {showLabel && (
            <span className={cn('text-slate-400 font-medium', labelSize)}>
              {level.toUpperCase()}
            </span>
          )}
        </div>
      </div>
      {showLabel && (
        <div className="mt-2 flex items-center gap-2">
          <div
            className="w-2 h-2 rounded-full"
            style={{ background: primary, boxShadow: `0 0 6px ${glow}` }}
          />
          <span className={cn('font-semibold text-sm', text)}>Threat Score</span>
        </div>
      )}
    </div>
  );
};

interface LinearRiskBarProps {
  score: number;
  label?: string;
  className?: string;
  animated?: boolean;
}

export const LinearRiskBar: React.FC<LinearRiskBarProps> = ({
  score,
  label,
  className,
  animated = true,
}) => {
  const level = getThreatFromScore(score);
  const { primary } = levelColors[level];

  return (
    <div className={cn('space-y-1', className)}>
      {label && (
        <div className="flex justify-between items-center">
          <span className="text-xs text-slate-400">{label}</span>
          <span className="text-xs font-mono font-semibold" style={{ color: primary }}>
            {score.toFixed(1)}%
          </span>
        </div>
      )}
      <div className="h-2 bg-slate-700/50 rounded-full overflow-hidden">
        <motion.div
          className="h-full rounded-full"
          style={{ background: `linear-gradient(90deg, ${primary}80, ${primary})` }}
          initial={{ width: 0 }}
          animate={{ width: `${score}%` }}
          transition={{ duration: animated ? 1 : 0, ease: 'easeOut' }}
        />
      </div>
    </div>
  );
};
