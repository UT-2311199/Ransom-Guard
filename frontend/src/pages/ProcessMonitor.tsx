import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Search, Zap, AlertTriangle, Shield, RefreshCw,
  ChevronUp, ChevronDown, X, Terminal, Info,
} from 'lucide-react';
import { useApp } from '../context/AppContext';
import { ConfirmModal } from '../components/Modal';
import { LinearRiskBar } from '../components/RiskMeter';
import { ThreatBadge } from '../components/ThreatBadge';
import { cn, getRiskColor } from '../utils/helpers';
import type { ProcessEntry, ProcessStatus } from '../context/AppContext';
import toast from 'react-hot-toast';

type SortKey = 'pid' | 'name' | 'cpu' | 'ram' | 'riskScore';
type SortDir = 'asc' | 'desc';

const STATUS_MAP: Record<ProcessStatus, { label: string; cls: string }> = {
  running: { label: 'Running', cls: 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/25' },
  suspicious: { label: 'Suspicious', cls: 'bg-yellow-500/15 text-yellow-400 border border-yellow-500/25' },
  terminated: { label: 'Terminated', cls: 'bg-slate-500/15 text-slate-400 border border-slate-500/25' },
  quarantined: { label: 'Quarantined', cls: 'bg-purple-500/15 text-purple-400 border border-purple-500/25' },
};

export const ProcessMonitor: React.FC = () => {
  const { processes, terminateProcess } = useApp();
  const [search, setSearch] = useState('');
  const [sortKey, setSortKey] = useState<SortKey>('riskScore');
  const [sortDir, setSortDir] = useState<SortDir>('desc');
  const [statusFilter, setStatusFilter] = useState<ProcessStatus | 'all'>('all');
  const [confirmPid, setConfirmPid] = useState<number | null>(null);
  const [selectedProcess, setSelectedProcess] = useState<ProcessEntry | null>(null);

  const handleSort = (key: SortKey) => {
    if (sortKey === key) setSortDir(d => d === 'asc' ? 'desc' : 'asc');
    else { setSortKey(key); setSortDir('desc'); }
  };

  const filtered = processes
    .filter(p => {
      const matchSearch = !search || [p.name, p.pid.toString(), p.user].some(
        s => s.toLowerCase().includes(search.toLowerCase())
      );
      const matchStatus = statusFilter === 'all' || p.status === statusFilter;
      return matchSearch && matchStatus;
    })
    .sort((a, b) => {
      const av = a[sortKey], bv = b[sortKey];
      const cmp = typeof av === 'string' ? av.localeCompare(bv as string) : (av as number) - (bv as number);
      return sortDir === 'asc' ? cmp : -cmp;
    });

  const handleTerminate = (pid: number) => {
    terminateProcess(pid);
    toast.success(`Process ${pid} terminated`, { icon: '🛑' });
    setConfirmPid(null);
    if (selectedProcess?.pid === pid) setSelectedProcess(null);
  };

  const SortIcon = ({ col }: { col: SortKey }) => {
    if (sortKey !== col) return <div className="w-3 h-3 opacity-30"><ChevronUp className="w-3 h-3" /></div>;
    return sortDir === 'asc' ? <ChevronUp className="w-3 h-3 text-blue-400" /> : <ChevronDown className="w-3 h-3 text-blue-400" />;
  };

  const suspiciousCount = processes.filter(p => p.status === 'suspicious').length;
  const highRiskCount = processes.filter(p => p.riskScore >= 70).length;

  return (
    <div className="space-y-4">
      {/* Alert */}
      {suspiciousCount > 0 && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center gap-3 p-4 rounded-xl bg-yellow-500/10 border border-yellow-500/25"
        >
          <AlertTriangle className="w-5 h-5 text-yellow-400 flex-shrink-0" />
          <div className="flex-1">
            <span className="text-sm font-semibold text-yellow-300">
              {suspiciousCount} suspicious {suspiciousCount === 1 ? 'process' : 'processes'} detected
            </span>
            <span className="text-sm text-yellow-400/70 ml-2">
              — Review and terminate if required
            </span>
          </div>
          <ThreatBadge level={highRiskCount > 2 ? 'critical' : 'high'} size="sm" />
        </motion.div>
      )}

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4">
        {[
          { label: 'Total', value: processes.length, color: 'text-slate-200' },
          { label: 'Running', value: processes.filter(p => p.status === 'running').length, color: 'text-emerald-400' },
          { label: 'Suspicious', value: suspiciousCount, color: 'text-yellow-400' },
          { label: 'High Risk (>70)', value: highRiskCount, color: 'text-red-400' },
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
      <div className="flex flex-wrap items-center gap-3 bg-slate-800/60 border border-slate-700/50 rounded-xl p-4">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search process, PID, user..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="w-full bg-slate-700/50 border border-slate-600/50 rounded-lg pl-9 pr-4 py-2 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500/50"
          />
        </div>
        <div className="flex items-center gap-1 bg-slate-700/30 border border-slate-600/50 rounded-lg p-1">
          {(['all', 'running', 'suspicious', 'terminated'] as const).map(s => (
            <button
              key={s}
              onClick={() => setStatusFilter(s)}
              className={cn(
                'px-3 py-1.5 text-xs font-medium rounded-md capitalize transition-all',
                statusFilter === s ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-slate-200'
              )}
            >
              {s}
            </button>
          ))}
        </div>
        <button className="flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-medium bg-slate-700/50 text-slate-300 border border-slate-600/50 hover:bg-slate-700 transition-colors">
          <RefreshCw className="w-3.5 h-3.5" />
          Refresh
        </button>
      </div>

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
              <tr className="border-b border-slate-700/50 bg-slate-800/50">
                {[
                  { key: 'pid', label: 'PID' },
                  { key: 'name', label: 'Process Name' },
                  { key: 'cpu', label: 'CPU %' },
                  { key: 'ram', label: 'RAM (MB)' },
                  { key: 'riskScore', label: 'Risk Score' },
                ].map(col => (
                  <th
                    key={col.key}
                    onClick={() => handleSort(col.key as SortKey)}
                    className="px-4 py-3 text-left text-[11px] font-semibold text-slate-400 uppercase tracking-wider cursor-pointer hover:text-slate-200 select-none"
                  >
                    <div className="flex items-center gap-1">
                      {col.label}
                      <SortIcon col={col.key as SortKey} />
                    </div>
                  </th>
                ))}
                <th className="px-4 py-3 text-left text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Status</th>
                <th className="px-4 py-3 text-left text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody>
              <AnimatePresence>
                {filtered.map((proc, idx) => (
                  <motion.tr
                    key={proc.pid}
                    layout
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    transition={{ delay: idx * 0.02 }}
                    onClick={() => setSelectedProcess(proc)}
                    className={cn(
                      'border-b border-slate-700/20 cursor-pointer table-row-hover',
                      proc.riskScore >= 80 && 'bg-red-500/5',
                      proc.riskScore >= 60 && proc.riskScore < 80 && 'bg-orange-500/5',
                      proc.status === 'terminated' && 'opacity-50',
                    )}
                  >
                    <td className="px-4 py-3">
                      <span className="text-xs font-mono text-slate-400">{proc.pid}</span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <div
                          className="w-1.5 h-1.5 rounded-full flex-shrink-0"
                          style={{ background: getRiskColor(proc.riskScore) }}
                        />
                        <span className="text-sm font-medium text-slate-200">{proc.name}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <div className="space-y-1 min-w-[80px]">
                        <span className={cn(
                          'text-sm font-mono font-semibold',
                          proc.cpu > 70 ? 'text-red-400' : proc.cpu > 40 ? 'text-yellow-400' : 'text-slate-200'
                        )}>
                          {proc.cpu.toFixed(1)}%
                        </span>
                        <div className="h-1 bg-slate-700/50 rounded-full overflow-hidden">
                          <div
                            className="h-full rounded-full transition-all duration-500"
                            style={{
                              width: `${Math.min(proc.cpu, 100)}%`,
                              background: proc.cpu > 70 ? '#EF4444' : proc.cpu > 40 ? '#F59E0B' : '#10B981',
                            }}
                          />
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-sm font-mono text-slate-300">{proc.ram.toFixed(0)}</span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="min-w-[120px]">
                        <LinearRiskBar score={proc.riskScore} animated={false} />
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <span className={cn('text-xs font-semibold px-2 py-0.5 rounded-full', STATUS_MAP[proc.status].cls)}>
                        {STATUS_MAP[proc.status].label}
                      </span>
                    </td>
                    <td className="px-4 py-3" onClick={e => e.stopPropagation()}>
                      <div className="flex items-center gap-1.5">
                        <button
                          onClick={() => setSelectedProcess(proc)}
                          className="p-1.5 rounded-lg text-slate-400 hover:text-blue-400 hover:bg-blue-500/10 transition-colors"
                          title="Details"
                        >
                          <Info className="w-3.5 h-3.5" />
                        </button>
                        {proc.status !== 'terminated' && (
                          <button
                            onClick={() => setConfirmPid(proc.pid)}
                            className="p-1.5 rounded-lg text-slate-400 hover:text-red-400 hover:bg-red-500/10 transition-colors"
                            title="Terminate"
                          >
                            <Zap className="w-3.5 h-3.5" />
                          </button>
                        )}
                      </div>
                    </td>
                  </motion.tr>
                ))}
              </AnimatePresence>
            </tbody>
          </table>
        </div>
        <div className="px-4 py-3 border-t border-slate-700/50 flex items-center justify-between">
          <span className="text-xs text-slate-500">{filtered.length} processes</span>
          <div className="flex items-center gap-4 text-xs text-slate-500">
            <div className="flex items-center gap-1.5">
              <div className="w-2 h-2 rounded-full bg-emerald-400" />
              <span>Safe</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="w-2 h-2 rounded-full bg-yellow-400" />
              <span>Medium</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="w-2 h-2 rounded-full bg-red-400" />
              <span>High Risk</span>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Detail Side Panel */}
      <AnimatePresence>
        {selectedProcess && (
          <motion.div
            initial={{ opacity: 0, x: 50 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 50 }}
            className="fixed right-0 top-16 h-[calc(100vh-64px)] w-96 bg-slate-900/98 border-l border-slate-700/80 z-40 overflow-y-auto shadow-2xl"
          >
            <div className="p-5">
              <div className="flex items-center justify-between mb-5">
                <h3 className="text-base font-semibold text-slate-100">Process Details</h3>
                <button onClick={() => setSelectedProcess(null)} className="p-1.5 rounded-lg hover:bg-slate-700/50 text-slate-400 hover:text-slate-200">
                  <X className="w-4 h-4" />
                </button>
              </div>

              <div className="space-y-5">
                <div className="flex items-start gap-3 p-4 rounded-xl bg-slate-800/60 border border-slate-700/50">
                  <Terminal className="w-5 h-5 text-slate-400 mt-0.5" />
                  <div>
                    <div className="text-base font-semibold text-slate-100">{selectedProcess.name}</div>
                    <div className="text-xs text-slate-500 font-mono mt-0.5">{selectedProcess.path}</div>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-slate-800/60 rounded-lg p-3 border border-slate-700/50">
                    <div className="text-xs text-slate-500 mb-1">CPU Usage</div>
                    <div className="text-xl font-bold font-mono text-slate-100">{selectedProcess.cpu.toFixed(1)}%</div>
                  </div>
                  <div className="bg-slate-800/60 rounded-lg p-3 border border-slate-700/50">
                    <div className="text-xs text-slate-500 mb-1">RAM Usage</div>
                    <div className="text-xl font-bold font-mono text-slate-100">{selectedProcess.ram.toFixed(0)} MB</div>
                  </div>
                </div>

                <div className="space-y-2">
                  <div className="text-xs text-slate-500 font-semibold uppercase tracking-wider">Risk Score</div>
                  <LinearRiskBar score={selectedProcess.riskScore} label={`${selectedProcess.riskScore.toFixed(0)}/100`} />
                </div>

                {[
                  { label: 'PID', value: selectedProcess.pid.toString() },
                  { label: 'User', value: selectedProcess.user },
                  { label: 'Start Time', value: selectedProcess.startTime },
                  { label: 'Status', value: STATUS_MAP[selectedProcess.status].label },
                ].map(item => (
                  <div key={item.label} className="flex items-center justify-between py-2 border-b border-slate-700/30">
                    <span className="text-xs text-slate-500">{item.label}</span>
                    <span className="text-xs font-mono text-slate-200">{item.value}</span>
                  </div>
                ))}

                {selectedProcess.status !== 'terminated' && (
                  <div className="pt-3 space-y-2">
                    <button
                      onClick={() => setConfirmPid(selectedProcess.pid)}
                      className="btn-danger w-full py-2.5 rounded-lg text-sm font-semibold text-white flex items-center justify-center gap-2"
                    >
                      <Zap className="w-4 h-4" />
                      Terminate Process
                    </button>
                    <button className="w-full py-2.5 rounded-lg text-sm font-semibold bg-slate-700/50 text-slate-300 border border-slate-600/50 hover:bg-slate-700 transition-colors flex items-center justify-center gap-2">
                      <Shield className="w-4 h-4" />
                      Quarantine
                    </button>
                  </div>
                )}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Confirm Modal */}
      <ConfirmModal
        isOpen={confirmPid !== null}
        onClose={() => setConfirmPid(null)}
        onConfirm={() => confirmPid && handleTerminate(confirmPid)}
        title="Terminate Process"
        message={`Are you sure you want to terminate PID ${confirmPid}? This action cannot be undone.`}
        confirmText="Terminate"
        confirmColor="red"
      />
    </div>
  );
};
