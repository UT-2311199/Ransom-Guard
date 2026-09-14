import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { format, formatDistanceToNow } from 'date-fns';
import type { ThreatLevel } from '../context/AppContext';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatTimestamp(date: Date): string {
  return format(date, 'HH:mm:ss');
}

export function formatDate(date: Date): string {
  return format(date, 'MMM dd, yyyy');
}

export function formatDateTime(date: Date): string {
  return format(date, 'MMM dd, yyyy HH:mm:ss');
}

export function timeAgo(date: Date): string {
  return formatDistanceToNow(date, { addSuffix: true });
}

export function getThreatColor(level: ThreatLevel): string {
  switch (level) {
    case 'critical': return '#EF4444';
    case 'high': return '#F97316';
    case 'medium': return '#F59E0B';
    case 'low': return '#3B82F6';
    case 'safe': return '#10B981';
    default: return '#64748B';
  }
}

export function getThreatBgClass(level: ThreatLevel): string {
  switch (level) {
    case 'critical': return 'bg-red-500/20 text-red-400 border border-red-500/30';
    case 'high': return 'bg-orange-500/20 text-orange-400 border border-orange-500/30';
    case 'medium': return 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30';
    case 'low': return 'bg-blue-500/20 text-blue-400 border border-blue-500/30';
    case 'safe': return 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30';
    default: return 'bg-slate-500/20 text-slate-400 border border-slate-500/30';
  }
}

export function getOperationColor(op: string): string {
  switch (op) {
    case 'ENCRYPT': return 'text-red-400';
    case 'DELETE': return 'text-orange-400';
    case 'MODIFY': return 'text-yellow-400';
    case 'CREATE': return 'text-blue-400';
    case 'RENAME': return 'text-purple-400';
    case 'READ': return 'text-slate-400';
    default: return 'text-slate-400';
  }
}

export function getOperationBg(op: string): string {
  switch (op) {
    case 'ENCRYPT': return 'bg-red-500/15 text-red-400';
    case 'DELETE': return 'bg-orange-500/15 text-orange-400';
    case 'MODIFY': return 'bg-yellow-500/15 text-yellow-400';
    case 'CREATE': return 'bg-blue-500/15 text-blue-400';
    case 'RENAME': return 'bg-purple-500/15 text-purple-400';
    case 'READ': return 'bg-slate-500/15 text-slate-400';
    default: return 'bg-slate-500/15 text-slate-400';
  }
}

export function getRiskColor(score: number): string {
  if (score >= 80) return '#EF4444';
  if (score >= 60) return '#F97316';
  if (score >= 40) return '#F59E0B';
  if (score >= 20) return '#3B82F6';
  return '#10B981';
}

export function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
}

export function formatPercent(value: number, decimals = 1): string {
  return `${value.toFixed(decimals)}%`;
}

export function generateId(): string {
  return crypto.randomUUID();
}

export function truncatePath(path: string, maxLen = 40): string {
  if (path.length <= maxLen) return path;
  const parts = path.split(/[/\\]/);
  if (parts.length <= 2) return path.substring(0, maxLen) + '…';
  return `…\\${parts.slice(-2).join('\\')}`;
}

export function generateTimeSeriesData(
  points: number,
  baseValue: number,
  variance: number,
  label: string
): { time: string; [key: string]: number | string }[] {
  const now = Date.now();
  return Array.from({ length: points }, (_, i) => ({
    time: format(new Date(now - (points - i - 1) * 60000), 'HH:mm'),
    [label]: Math.max(0, Math.min(100, baseValue + (Math.random() - 0.5) * variance)),
  }));
}

export function debounce<T extends (...args: unknown[]) => unknown>(fn: T, delay: number): (...args: Parameters<T>) => void {
  let timeout: ReturnType<typeof setTimeout>;
  return (...args: Parameters<T>) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => fn(...args), delay);
  };
}
