import React from 'react';
import { AlertTriangle, AlertCircle, Info, CheckCircle, Shield } from 'lucide-react';
import type { ThreatLevel } from '../context/AppContext';
import { getThreatBgClass } from '../utils/helpers';
import { cn } from '../utils/helpers';

interface ThreatBadgeProps {
  level: ThreatLevel;
  showIcon?: boolean;
  size?: 'xs' | 'sm' | 'md' | 'lg';
  pulse?: boolean;
  className?: string;
}

const icons: Record<ThreatLevel, React.FC<{ className?: string }>> = {
  critical: ({ className }) => <AlertTriangle className={className} />,
  high: ({ className }) => <AlertCircle className={className} />,
  medium: ({ className }) => <AlertCircle className={className} />,
  low: ({ className }) => <Info className={className} />,
  safe: ({ className }) => <CheckCircle className={className} />,
};

const labels: Record<ThreatLevel, string> = {
  critical: 'CRITICAL',
  high: 'HIGH',
  medium: 'MEDIUM',
  low: 'LOW',
  safe: 'SAFE',
};

const sizes = {
  xs: 'text-[10px] px-1.5 py-0.5 gap-1',
  sm: 'text-xs px-2 py-0.5 gap-1',
  md: 'text-xs px-2.5 py-1 gap-1.5',
  lg: 'text-sm px-3 py-1.5 gap-2',
};

const iconSizes = {
  xs: 'w-2.5 h-2.5',
  sm: 'w-3 h-3',
  md: 'w-3.5 h-3.5',
  lg: 'w-4 h-4',
};

export const ThreatBadge: React.FC<ThreatBadgeProps> = ({
  level,
  showIcon = true,
  size = 'sm',
  pulse = false,
  className,
}) => {
  const Icon = icons[level];
  const pulseClass = pulse && (level === 'critical' || level === 'high') ? 'animate-pulse' : '';

  return (
    <span
      className={cn(
        'inline-flex items-center font-semibold rounded-full font-mono tracking-wider',
        getThreatBgClass(level),
        sizes[size],
        pulseClass,
        className
      )}
    >
      {showIcon && <Icon className={iconSizes[size]} />}
      {labels[level]}
    </span>
  );
};

interface StatusDotProps {
  status: 'online' | 'offline' | 'warning' | 'scanning';
  label?: string;
  className?: string;
}

export const StatusDot: React.FC<StatusDotProps> = ({ status, label, className }) => {
  const colors = {
    online: 'bg-emerald-400',
    offline: 'bg-red-400',
    warning: 'bg-yellow-400',
    scanning: 'bg-blue-400',
  };
  const pulseColors = {
    online: 'pulse-success',
    offline: 'pulse-danger',
    warning: 'pulse-warning',
    scanning: '',
  };

  return (
    <div className={cn('flex items-center gap-2', className)}>
      <span
        className={cn(
          'status-dot flex-shrink-0',
          colors[status],
          pulseColors[status]
        )}
      />
      {label && <span className="text-sm text-slate-300">{label}</span>}
    </div>
  );
};

interface ShieldIconProps {
  level: ThreatLevel;
  size?: number;
}

export const ShieldIcon: React.FC<ShieldIconProps> = ({ level, size = 40 }) => {
  const colors: Record<ThreatLevel, string> = {
    critical: '#EF4444',
    high: '#F97316',
    medium: '#F59E0B',
    low: '#3B82F6',
    safe: '#10B981',
  };

  return (
    <div
      className="flex items-center justify-center rounded-full"
      style={{
        width: size,
        height: size,
        background: `${colors[level]}20`,
        border: `1px solid ${colors[level]}40`,
      }}
    >
      <Shield style={{ width: size * 0.5, height: size * 0.5, color: colors[level] }} />
    </div>
  );
};
