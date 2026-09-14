import React from 'react';
import { motion } from 'framer-motion';
import { Shield } from 'lucide-react';
import { cn } from '../utils/helpers';

export const PageLoader: React.FC = () => (
  <div className="flex items-center justify-center h-full min-h-[400px]">
    <motion.div
      className="flex flex-col items-center gap-6"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
    >
      <div className="relative">
        <motion.div
          className="w-16 h-16 rounded-full border-2 border-blue-500/30"
          animate={{ rotate: 360 }}
          transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
        />
        <motion.div
          className="absolute inset-2 rounded-full border-2 border-t-blue-500 border-r-transparent border-b-transparent border-l-transparent"
          animate={{ rotate: -360 }}
          transition={{ duration: 1.5, repeat: Infinity, ease: 'linear' }}
        />
        <div className="absolute inset-0 flex items-center justify-center">
          <Shield className="w-6 h-6 text-blue-400" />
        </div>
      </div>
      <div className="text-center">
        <div className="text-sm font-medium text-slate-400">Loading...</div>
        <div className="flex gap-1 mt-2 justify-center">
          {[0, 1, 2].map(i => (
            <motion.div
              key={i}
              className="w-1.5 h-1.5 rounded-full bg-blue-400"
              animate={{ opacity: [0.3, 1, 0.3] }}
              transition={{ duration: 1.2, delay: i * 0.2, repeat: Infinity }}
            />
          ))}
        </div>
      </div>
    </motion.div>
  </div>
);

interface SkeletonProps {
  className?: string;
  lines?: number;
}

export const Skeleton: React.FC<SkeletonProps> = ({ className, lines = 1 }) => (
  <div className={cn('space-y-2', className)}>
    {Array.from({ length: lines }, (_, i) => (
      <div
        key={i}
        className="skeleton rounded h-4"
        style={{ width: `${85 - i * 15}%` }}
      />
    ))}
  </div>
);

export const CardSkeleton: React.FC<{ className?: string }> = ({ className }) => (
  <div className={cn('bg-slate-800/60 rounded-xl border border-slate-700/50 p-5', className)}>
    <div className="flex items-start justify-between mb-4">
      <div className="skeleton rounded-lg w-10 h-10" />
      <div className="skeleton rounded-full w-16 h-6" />
    </div>
    <div className="skeleton rounded h-8 w-24 mb-2" />
    <div className="skeleton rounded h-4 w-32" />
  </div>
);

export const TableSkeleton: React.FC<{ rows?: number; cols?: number }> = ({
  rows = 8,
  cols = 6,
}) => (
  <div className="space-y-2">
    {Array.from({ length: rows }, (_, i) => (
      <div key={i} className={cn('flex gap-4 py-3 px-4 rounded-lg', i % 2 === 0 ? 'bg-slate-800/30' : '')}>
        {Array.from({ length: cols }, (_, j) => (
          <div
            key={j}
            className="skeleton rounded h-4 flex-1"
            style={{ opacity: 1 - i * 0.08 }}
          />
        ))}
      </div>
    ))}
  </div>
);

interface SpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  color?: string;
}

export const Spinner: React.FC<SpinnerProps> = ({ size = 'md', color = '#2563EB' }) => {
  const s = { sm: 16, md: 24, lg: 40 }[size];
  return (
    <motion.div
      className="rounded-full border-2"
      style={{
        width: s,
        height: s,
        borderColor: `${color}30`,
        borderTopColor: color,
      }}
      animate={{ rotate: 360 }}
      transition={{ duration: 0.8, repeat: Infinity, ease: 'linear' }}
    />
  );
};
