import React, { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Search, Download, ChevronDown, ChevronUp, ChevronRight,
  Calendar, FileWarning, Shield, Terminal, Hash, AlertTriangle,
  Filter, X,
} from 'lucide-react';
import { ThreatBadge } from '../components/ThreatBadge';
import { cn, formatDateTime, timeAgo } from '../utils/helpers';
import { threatHistory, type ThreatHistoryItem } from '../utils/mockData';
import toast from 'react-hot-toast';

const STATUS_MAP: Record<string, { label: string; cls: string }> = {
  blocked: { label: 'Blocked', cls: 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/25' },
  quarantined: { label: 'Quarantined', cls: 'bg-purple-500/15 text-purple-400 border border-purple-500/25' },
  resolved: { label: 'Resolved', cls: 'bg-blue-500/15 text-blue-400 border border-blue-500/25' },
  active: { label: 'Active', cls: 'bg-red-500/15 text-red-400 border border-red-500/25' },
};

const ThreatCard: React.FC<{
  threat: ThreatHistoryItem;
  isExpanded: boolean;
  onToggle: () => void;
}> = ({ threat, isExpanded, onToggle }) => {
  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn(
        'border rounded-xl overflow-hidden transition-all duration-200',
        threat.severity === 'critical' ? 'border-red-500/30 bg-red-500/5' :
        threat.severity === 'high' ? 'border-orange-500/25 bg-orange-500/5' :
        threat.severity === 'medium' ? 'border-yellow-500/20 bg-yellow-500/5' :
        'border-slate-700/50 bg-slate-800/40'
      )}
    >
      {/* Header */}
      <button
        className="w-full text-left p-4 flex items-start gap-4"
        onClick={onToggle}
      >
        {/* Timeline dot */}
        <div className="flex flex-col items-center gap-1 flex-shrink-0 mt-1">
          <div className={cn(
            'w-3 h-3 rounded-full border-2',
            threat.severity === 'critical' ? 'bg-red-400 border-red-500' :
            threat.severity === 'high' ? 'bg-orange-400 border-orange-500' :
            threat.severity === 'medium' ? 'bg-yellow-400 border-yellow-500' :
            'bg-blue-400 border-blue-500'
          )} />
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-3">
            <div className="flex items-center gap-2 flex-wrap">
              <ThreatBadge level={threat.severity} size="xs" />
              <span className="text-sm font-semibold text-slate-100">{threat.threat}</span>
              <span className={cn('text-[10px] font-semibold px-2 py-0.5 rounded-full', STATUS_MAP[threat.status].cls)}>
                {STATUS_MAP[threat.status].label}
              </span>
            </div>
            <div className="flex items-center gap-2 flex-shrink-0">
              <div className="text-right">
                <div className="text-xs text-slate-400">{timeAgo(threat.date)}</div>
                <div className="text-[10px] text-slate-600">{formatDateTime(threat.date)}</div>
              </div>
              {isExpanded
                ? <ChevronUp className="w-4 h-4 text-slate-400" />
                : <ChevronDown className="w-4 h-4 text-slate-400" />
              }
            </div>
          </div>

          <div className="flex items-center gap-3 mt-2 text-xs text-slate-400">
            <div className="flex items-center gap-1">
              <Terminal className="w-3 h-3" />
              <span className="font-mono">{threat.process}</span>
            </div>
            <div className="flex items-center gap-1">
              <FileWarning className="w-3 h-3" />
              <span>{threat.filesAffected} files affected</span>
            </div>
            <div className="flex items-center gap-1">
              <Hash className="w-3 h-3" />
              <span>ML: {threat.mlScore.toFixed(1)}%</span>
            </div>
          </div>
        </div>
      </button>

      {/* Expanded content */}
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25 }}
          >
            <div className="px-4 pb-4 border-t border-slate-700/30 pt-4 ml-7">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                {/* Details */}
                <div className="space-y-3">
                  <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Incident Details</h4>
                  <p className="text-sm text-slate-300 leading-relaxed">{threat.details}</p>

                  <div className="space-y-2">
                    {[
                      { label: 'Attack Type', value: threat.attackType, icon: <AlertTriangle className="w-3 h-3" /> },
                      { label: 'Process Path', value: threat.path, icon: <Terminal className="w-3 h-3" />, mono: true },
                    ].map(item => (
                      <div key={item.label} className="flex items-start gap-2">
                        <div className="text-slate-500 mt-0.5">{item.icon}</div>
                        <div className="flex-1">
                          <span className="text-[10px] text-slate-500 block">{item.label}</span>
                          <span className={cn('text-xs text-slate-300', item.mono && 'font-mono break-all')}>
                            {item.value}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Metrics */}
                <div className="space-y-3">
                  <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Metrics</h4>
                  <div className="grid grid-cols-2 gap-3">
                    {[
                      { label: 'ML Confidence', value: `${threat.mlScore.toFixed(1)}%`, color: threat.mlScore > 80 ? 'text-red-400' : 'text-yellow-400' },
                      { label: 'Files Affected', value: threat.filesAffected.toLocaleString(), color: 'text-orange-400' },
                      { label: 'Severity', value: threat.severity.toUpperCase(), color: 'text-slate-200' },
                      { label: 'Status', value: STATUS_MAP[threat.status].label, color: 'text-emerald-400' },
                    ].map(m => (
                      <div key={m.label} className="bg-slate-800/60 rounded-lg p-3 border border-slate-700/50">
                        <div className="text-[10px] text-slate-500 mb-1">{m.label}</div>
                        <div className={cn('text-sm font-bold font-mono', m.color)}>{m.value}</div>
                      </div>
                    ))}
                  </div>

                  <div className="flex gap-2 pt-2">
                    <button className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-blue-500/15 text-blue-400 border border-blue-500/25 hover:bg-blue-500/25 transition-colors">
                      <Shield className="w-3 h-3" />
                      View Report
                    </button>
                    <button className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-700/50 text-slate-300 border border-slate-600/50 hover:bg-slate-700 transition-colors">
                      <ChevronRight className="w-3 h-3" />
                      Analyze
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};

export const ThreatHistory: React.FC = () => {
  const [search, setSearch] = useState('');
  const [severityFilter, setSeverityFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set(['1']));

  const filtered = useMemo(() => {
    return threatHistory.filter(t => {
      const matchSearch = !search || [t.threat, t.process, t.attackType].some(
        s => s.toLowerCase().includes(search.toLowerCase())
      );
      const matchSev = severityFilter === 'all' || t.severity === severityFilter;
      const matchStatus = statusFilter === 'all' || t.status === statusFilter;
      return matchSearch && matchSev && matchStatus;
    });
  }, [search, severityFilter, statusFilter]);

  const toggleExpand = (id: string) => {
    setExpandedIds(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const handleExport = () => {
    const csv = [
      'Date,Severity,Threat,Process,Attack Type,Files Affected,ML Score,Status',
      ...filtered.map(t =>
        `"${formatDateTime(t.date)}","${t.severity}","${t.threat}","${t.process}","${t.attackType}",${t.filesAffected},${t.mlScore},"${t.status}"`
      ),
    ].join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `threat-history-${Date.now()}.csv`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success('Threat history exported!');
  };

  const summary = {
    total: threatHistory.length,
    critical: threatHistory.filter(t => t.severity === 'critical').length,
    blocked: threatHistory.filter(t => t.status === 'blocked').length,
    resolved: threatHistory.filter(t => t.status === 'resolved').length,
  };

  return (
    <div className="space-y-5">
      {/* Summary */}
      <div className="grid grid-cols-4 gap-4">
        {[
          { label: 'Total Incidents', value: summary.total, color: 'text-slate-200' },
          { label: 'Critical', value: summary.critical, color: 'text-red-400' },
          { label: 'Blocked', value: summary.blocked, color: 'text-emerald-400' },
          { label: 'Resolved', value: summary.resolved, color: 'text-blue-400' },
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
            placeholder="Search threats, processes..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="w-full bg-slate-700/50 border border-slate-600/50 rounded-lg pl-9 pr-4 py-2 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500/50"
          />
          {search && (
            <button onClick={() => setSearch('')} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-200">
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>

        <div className="flex items-center gap-1 bg-slate-700/30 border border-slate-600/50 rounded-lg p-1">
          {['all', 'critical', 'high', 'medium', 'low'].map(s => (
            <button
              key={s}
              onClick={() => setSeverityFilter(s)}
              className={cn(
                'px-2.5 py-1 text-xs font-medium rounded-md capitalize transition-all',
                severityFilter === s ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-slate-200'
              )}
            >
              {s}
            </button>
          ))}
        </div>

        <select
          value={statusFilter}
          onChange={e => setStatusFilter(e.target.value)}
          className="bg-slate-700/50 border border-slate-600/50 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none"
        >
          <option value="all">All Statuses</option>
          <option value="blocked">Blocked</option>
          <option value="quarantined">Quarantined</option>
          <option value="resolved">Resolved</option>
          <option value="active">Active</option>
        </select>

        <button
          onClick={handleExport}
          className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium btn-primary text-white ml-auto"
        >
          <Download className="w-4 h-4" />
          Export CSV
        </button>
      </div>

      {/* Timeline */}
      <div className="space-y-3">
        <div className="flex items-center gap-2 mb-2">
          <Calendar className="w-4 h-4 text-slate-500" />
          <span className="text-xs text-slate-500">
            Showing {filtered.length} of {threatHistory.length} incidents
          </span>
        </div>

        {filtered.length === 0 ? (
          <div className="text-center py-16 text-slate-500">
            <Filter className="w-8 h-8 mx-auto mb-3 opacity-50" />
            <p>No threats match your filters</p>
          </div>
        ) : (
          filtered.map(threat => (
            <ThreatCard
              key={threat.id}
              threat={threat}
              isExpanded={expandedIds.has(threat.id)}
              onToggle={() => toggleExpand(threat.id)}
            />
          ))
        )}
      </div>
    </div>
  );
};
