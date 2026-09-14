import React from 'react';
import { motion } from 'framer-motion';
import { cn } from '../utils/helpers';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface MetricCardProps {
  title: string;
  value: string | number;
  unit?: string;
  icon: React.ReactNode;
  trend?: number;
  trendLabel?: string;
  color?: 'blue' | 'red' | 'green' | 'yellow' | 'purple' | 'orange';
  subtitle?: string;
  className?: string;
  delay?: number;
  gradient?: boolean;
  progress?: number;
}

const colorMap = {
  blue: {
    icon: 'bg-blue-500/15 text-blue-400',
    glow: 'hover:shadow-blue-500/10',
    progress: 'bg-blue-500',
    text: 'text-blue-400',
    border: 'hover:border-blue-500/30',
  },
  red: {
    icon: 'bg-red-500/15 text-red-400',
    glow: 'hover:shadow-red-500/10',
    progress: 'bg-red-500',
    text: 'text-red-400',
    border: 'hover:border-red-500/30',
  },
  green: {
    icon: 'bg-emerald-500/15 text-emerald-400',
    glow: 'hover:shadow-emerald-500/10',
    progress: 'bg-emerald-500',
    text: 'text-emerald-400',
    border: 'hover:border-emerald-500/30',
  },
  yellow: {
    icon: 'bg-yellow-500/15 text-yellow-400',
    glow: 'hover:shadow-yellow-500/10',
    progress: 'bg-yellow-500',
    text: 'text-yellow-400',
    border: 'hover:border-yellow-500/30',
  },
  purple: {
    icon: 'bg-purple-500/15 text-purple-400',
    glow: 'hover:shadow-purple-500/10',
    progress: 'bg-purple-500',
    text: 'text-purple-400',
    border: 'hover:border-purple-500/30',
  },
  orange: {
    icon: 'bg-orange-500/15 text-orange-400',
    glow: 'hover:shadow-orange-500/10',
    progress: 'bg-orange-500',
    text: 'text-orange-400',
    border: 'hover:border-orange-500/30',
  },
};

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  unit,
  icon,
  trend,
  trendLabel,
  color = 'blue',
  subtitle,
  className,
  delay = 0,
  progress,
}) => {
  const colors = colorMap[color];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay }}
      whileHover={{ y: -2, transition: { duration: 0.2 } }}
      className={cn(
        'relative bg-slate-800/60 rounded-xl border border-slate-700/50 p-5',
        'hover:shadow-lg transition-all duration-300 overflow-hidden group',
        colors.glow,
        colors.border,
        className
      )}
    >
      {/* Background gradient */}
      <div
        className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500"
        style={{
          background: 'radial-gradient(ellipse at top right, rgba(37,99,235,0.05) 0%, transparent 70%)',
        }}
      />

      <div className="relative z-10">
        <div className="flex items-start justify-between mb-4">
          <div className={cn('p-2.5 rounded-lg', colors.icon)}>
            {icon}
          </div>
          {trend !== undefined && (
            <div
              className={cn(
                'flex items-center gap-1 text-xs font-medium px-2 py-1 rounded-full',
                trend > 0 ? 'bg-red-500/10 text-red-400' :
                trend < 0 ? 'bg-emerald-500/10 text-emerald-400' :
                'bg-slate-500/10 text-slate-400'
              )}
            >
              {trend > 0 ? <TrendingUp className="w-3 h-3" /> :
               trend < 0 ? <TrendingDown className="w-3 h-3" /> :
               <Minus className="w-3 h-3" />}
              {Math.abs(trend).toFixed(1)}%
            </div>
          )}
        </div>

        <div className="space-y-1">
          <div className="flex items-baseline gap-1">
            <span className="text-2xl font-bold text-slate-100 counter-text">
              {value}
            </span>
            {unit && (
              <span className="text-sm text-slate-400 font-medium">{unit}</span>
            )}
          </div>
          <div className="text-sm font-medium text-slate-400">{title}</div>
          {subtitle && (
            <div className="text-xs text-slate-500">{subtitle}</div>
          )}
          {trendLabel && (
            <div className="text-xs text-slate-500">{trendLabel}</div>
          )}
        </div>

        {progress !== undefined && (
          <div className="mt-3 space-y-1">
            <div className="h-1.5 bg-slate-700/50 rounded-full overflow-hidden">
              <motion.div
                className={cn('h-full rounded-full', colors.progress)}
                initial={{ width: 0 }}
                animate={{ width: `${Math.min(progress, 100)}%` }}
                transition={{ duration: 1, delay: delay + 0.3, ease: 'easeOut' }}
              />
            </div>
          </div>
        )}
      </div>

      {/* Bottom accent line */}
      <div
        className="absolute bottom-0 left-0 right-0 h-[2px] opacity-0 group-hover:opacity-100 transition-opacity duration-300"
        style={{
          background: `linear-gradient(90deg, transparent, ${
            color === 'blue' ? '#2563EB' :
            color === 'red' ? '#EF4444' :
            color === 'green' ? '#10B981' :
            color === 'yellow' ? '#F59E0B' :
            color === 'purple' ? '#8B5CF6' : '#F97316'
          }, transparent)`,
        }}
      />
    </motion.div>
  );
};
