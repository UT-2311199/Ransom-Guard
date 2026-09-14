import React, { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Search, Filter, ChevronLeft, ChevronRight, Activity,
  RefreshCw, Download, X, Clock, Folder,
} from 'lucide-react';
import { useApp } from '../context/AppContext';
import { ThreatBadge } from '../components/ThreatBadge';
import { cn, formatTimestamp, getOperationBg, truncatePath } from '../utils/helpers';
import type { FileOperation, ThreatLevel } from '../context/AppContext';

const OPERATIONS: (FileOperation | 'ALL')[] = ['ALL', 'CREATE', 'MODIFY', 'DELETE', 'RENAME', 'ENCRYPT', 'READ'];
const STATUSES: (ThreatLevel | 'ALL')[] = ['ALL', 'critical', 'high', 'medium', 'low', 'safe'];
const PAGE_SIZE = 15;

export const Monitoring: React.FC = () => {
  const { monitoringData } = useApp();
  const [search, setSearch] = useState('');
  const [opFilter, setOpFilter] = useState<FileOperation | 'ALL'>('ALL');
  const [statusFilter, setStatusFilter] = useState<ThreatLevel | 'ALL'>('ALL');
  const [page, setPage] = useState(1);
  const [selectedEntry, setSelectedEntry] = useState<typeof monitoringData[0] | null>(null);
  const [isPaused, setIsPaused] = useState(false);

  const filtered = useMemo(() => {
    return monitoringData.filter(entry => {
      const matchSearch = !search || [entry.fileName, entry.path, entry.process].some(
        s => s.toLowerCase().includes(search.toLowerCase())
      );
      const matchOp = opFilter === 'ALL' || entry.operation === opFilter;
      const matchStatus = statusFilter === 'ALL' || entry.status === statusFilter;
      return matchSearch && matchOp && matchStatus;
    });
  }, [monitoringData, search, opFilter, statusFilter]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const paged = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  const stats = useMemo(() => ({
    total: filtered.length,
    critical: filtered.filter(e => e.status === 'critical').length,
    high: filtered.filter(e => e.status === 'high').length,
    encryptions: filtered.filter(e => e.operation === 'ENCRYPT').length,
  }), [filtered]);

  return (
    <div className="space-y-4">
      {/* Stats Bar */}
      <div className="grid grid-cols-4 gap-4">
        {[
          { label: 'Total Events', value: stats.total, color: 'text-slate-200' },
          { label: 'Critical', value: stats.critical, color: 'text-red-400' },
          { label: 'High Risk', value: stats.high, color: 'text-orange-400' },
          { label: 'Encryptions', value: stats.encryptions, color: 'text-yellow-400' },
        ].map((s, i) => (
          <motion.div
            key={s.label}
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.05 }}
            className="bg-slate-800/60 border border-slate-700/50 rounded-xl px-4 py-3"
          >
            <div className={cn('text-2xl font-bold counter-text', s.color)}>{s.value}</div>
            <div className="text-xs text-slate-500 mt-0.5">{s.label}</div>
          </motion.div>
        ))}
      </div>

      {/* Controls */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-slate-800/60 border border-slate-700/50 rounded-xl p-4"
      >
        <div className="flex flex-wrap items-center gap-3">
          {/* Search */}
          <div className="relative flex-1 min-w-[200px]">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type="text"
              placeholder="Search file, path, process..."
              value={search}
              onChange={e => { setSearch(e.target.value); setPage(1); }}
              className="w-full bg-slate-700/50 border border-slate-600/50 rounded-lg pl-9 pr-4 py-2 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500/50 transition-colors"
            />
            {search && (
              <button
                onClick={() => setSearch('')}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-200"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            )}
          </div>

          {/* Operation filter */}
          <div className="flex items-center gap-1 bg-slate-700/30 border border-slate-600/50 rounded-lg p-1">
            {OPERATIONS.map(op => (
              <button
                key={op}
                onClick={() => { setOpFilter(op); setPage(1); }}
                className={cn(
                  'px-2 py-1 text-[10px] font-semibold rounded-md transition-all duration-150',
                  opFilter === op
                    ? 'bg-blue-600 text-white'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-600/50'
                )}
              >
                {op}
              </button>
            ))}
          </div>

          {/* Status filter */}
          <select
            value={statusFilter}
            onChange={e => { setStatusFilter(e.target.value as ThreatLevel | 'ALL'); setPage(1); }}
            className="bg-slate-700/50 border border-slate-600/50 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-blue-500/50"
          >
            {STATUSES.map(s => (
              <option key={s} value={s}>{s === 'ALL' ? 'All Statuses' : s.toUpperCase()}</option>
            ))}
          </select>

          {/* Actions */}
          <div className="flex items-center gap-2 ml-auto">
            <button
              onClick={() => setIsPaused(v => !v)}
              className={cn(
                'flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-medium transition-all',
                isPaused
                  ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/25 hover:bg-emerald-500/25'
                  : 'bg-yellow-500/15 text-yellow-400 border border-yellow-500/25 hover:bg-yellow-500/25'
              )}
            >
              {isPaused ? <Activity className="w-3.5 h-3.5" /> : <RefreshCw className="w-3.5 h-3.5 animate-spin" />}
              {isPaused ? 'Resume' : 'Live'}
            </button>
            <button className="flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-medium bg-slate-700/50 text-slate-300 border border-slate-600/50 hover:bg-slate-700 transition-all">
              <Download className="w-3.5 h-3.5" />
              Export
            </button>
          </div>
        </div>
      </motion.div>

      {/* Table */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.2 }}
        className="bg-slate-800/60 border border-slate-700/50 rounded-xl overflow-hidden"
      >
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-700/50">
                {['Timestamp', 'File Name', 'Operation', 'Path', 'Process', 'PID', 'Status'].map(h => (
                  <th key={h} className="px-4 py-3 text-left text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              <AnimatePresence mode="popLayout">
                {paged.map((entry, idx) => (
                  <motion.tr
                    key={entry.id}
                    layout
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: 20 }}
                    transition={{ duration: 0.2, delay: idx * 0.01 }}
                    onClick={() => setSelectedEntry(entry)}
                    className={cn(
                      'border-b border-slate-700/20 cursor-pointer table-row-hover',
                      entry.status === 'critical' && 'bg-red-500/5',
                      entry.status === 'high' && 'bg-orange-500/5',
                    )}
                  >
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-1.5">
                        <Clock className="w-3 h-3 text-slate-500 flex-shrink-0" />
                        <span className="text-xs font-mono text-slate-400">
                          {formatTimestamp(entry.timestamp)}
                        </span>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-sm font-medium text-slate-200">{entry.fileName}</span>
                    </td>
                    <td className="px-4 py-3">
                      <span className={cn('text-[10px] font-bold px-2 py-0.5 rounded-md', getOperationBg(entry.operation))}>
                        {entry.operation}
                      </span>
                    </td>
                    <td className="px-4 py-3 max-w-[200px]">
                      <div className="flex items-center gap-1.5">
                        <Folder className="w-3 h-3 text-slate-500 flex-shrink-0" />
                        <span className="text-xs text-slate-400 truncate font-mono">
                          {truncatePath(entry.path, 35)}
                        </span>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-xs font-mono text-slate-300">{entry.process}</span>
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-xs font-mono text-slate-500">{entry.pid}</span>
                    </td>
                    <td className="px-4 py-3">
                      <ThreatBadge level={entry.status} size="xs" pulse={entry.status === 'critical'} />
                    </td>
                  </motion.tr>
                ))}
              </AnimatePresence>
              {paged.length === 0 && (
                <tr>
                  <td colSpan={7} className="px-4 py-16 text-center">
                    <Filter className="w-8 h-8 text-slate-600 mx-auto mb-3" />
                    <p className="text-slate-400 text-sm">No events match your filters</p>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="flex items-center justify-between px-4 py-3 border-t border-slate-700/50">
          <span className="text-xs text-slate-500">
            Showing {Math.min((page - 1) * PAGE_SIZE + 1, filtered.length)}–{Math.min(page * PAGE_SIZE, filtered.length)} of {filtered.length} events
          </span>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page === 1}
              className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-700/50 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
              const p = Math.max(1, Math.min(totalPages - 4, page - 2)) + i;
              return (
                <button
                  key={p}
                  onClick={() => setPage(p)}
                  className={cn(
                    'w-7 h-7 rounded-lg text-xs font-medium transition-colors',
                    p === page
                      ? 'bg-blue-600 text-white'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-700/50'
                  )}
                >
                  {p}
                </button>
              );
            })}
            <button
              onClick={() => setPage(p => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-700/50 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </motion.div>

      {/* Detail Panel */}
      <AnimatePresence>
        {selectedEntry && (
          <motion.div
            initial={{ opacity: 0, x: 50 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 50 }}
            className="fixed right-0 top-16 h-[calc(100vh-64px)] w-96 bg-slate-900/98 border-l border-slate-700/80 z-40 overflow-y-auto shadow-2xl"
          >
            <div className="p-5">
              <div className="flex items-center justify-between mb-5">
                <h3 className="text-base font-semibold text-slate-100">Event Details</h3>
                <button
                  onClick={() => setSelectedEntry(null)}
                  className="p-1.5 rounded-lg hover:bg-slate-700/50 text-slate-400 hover:text-slate-200 transition-colors"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <ThreatBadge level={selectedEntry.status} size="md" />
                  <span className={cn('text-[10px] font-bold px-2 py-0.5 rounded-md', getOperationBg(selectedEntry.operation))}>
                    {selectedEntry.operation}
                  </span>
                </div>

                {[
                  { label: 'File Name', value: selectedEntry.fileName },
                  { label: 'Process', value: selectedEntry.process, mono: true },
                  { label: 'PID', value: selectedEntry.pid.toString(), mono: true },
                  { label: 'Full Path', value: selectedEntry.path, mono: true },
                  { label: 'Timestamp', value: selectedEntry.timestamp.toISOString(), mono: true },
                  { label: 'File Size', value: selectedEntry.size || 'N/A' },
                ].map(item => (
                  <div key={item.label} className="space-y-1">
                    <label className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">
                      {item.label}
                    </label>
                    <div className={cn(
                      'text-sm text-slate-200 bg-slate-800/60 rounded-lg px-3 py-2 break-all',
                      item.mono && 'font-mono'
                    )}>
                      {item.value}
                    </div>
                  </div>
                ))}

                {(selectedEntry.status === 'critical' || selectedEntry.status === 'high') && (
                  <div className="pt-2 space-y-2">
                    <button className="btn-danger w-full py-2.5 rounded-lg text-sm font-semibold text-white">
                      Kill Process
                    </button>
                    <button className="w-full py-2.5 rounded-lg text-sm font-semibold bg-yellow-500/15 text-yellow-400 border border-yellow-500/25 hover:bg-yellow-500/25 transition-colors">
                      Quarantine File
                    </button>
                  </div>
                )}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};
