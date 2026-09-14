import React, { useMemo } from 'react';
import { motion } from 'framer-motion';
import {
  Cpu, HardDrive, MemoryStick, Activity, ShieldAlert,
  FileWarning, AlertTriangle, CheckCircle, TrendingUp, Clock,
  Server, Zap, Eye, Lock,
} from 'lucide-react';
import {
  AreaChart, Area, LineChart, Line, XAxis, YAxis,
  CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from 'recharts';
import { useApp } from '../context/AppContext';
import { MetricCard } from '../components/MetricCard';
import { ThreatBadge } from '../components/ThreatBadge';
import { RiskMeter } from '../components/RiskMeter';
import { cn, timeAgo } from '../utils/helpers';
import { useCpuHistory, useMemoryHistory } from '../hooks/useRealTimeData';
import { generateThreatsOverTime } from '../utils/mockData';
import { LiveThreatFeed } from '../components/LiveThreatFeed';

const CustomTooltip = ({ active, payload, label }: { active?: boolean; payload?: { name: string; value: number; color: string }[]; label?: string }) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-slate-800 border border-slate-700/80 rounded-lg p-3 shadow-xl">
        <p className="text-xs text-slate-400 mb-2 font-medium">{label}</p>
        {payload.map((entry, i) => (
          <div key={i} className="flex items-center gap-2 text-xs">
            <div className="w-2 h-2 rounded-full" style={{ background: entry.color }} />
            <span className="text-slate-300">{entry.name}:</span>
            <span className="font-semibold" style={{ color: entry.color }}>
              {typeof entry.value === 'number' ? entry.value.toFixed(1) : entry.value}
              {entry.name.toLowerCase().includes('cpu') || entry.name.toLowerCase().includes('memory') ? '%' : ''}
            </span>
          </div>
        ))}
      </div>
    );
  }
  return null;
};

export const Dashboard: React.FC = () => {
  const { systemMetrics, alerts } = useApp();
  const cpuHistory = useCpuHistory(true, systemMetrics.cpu || undefined);
  const memoryHistory = useMemoryHistory(true, systemMetrics.memory || undefined);
  const threatsData = useMemo(() => generateThreatsOverTime('24h'), []);
  const activeAlerts = alerts.filter(a => !a.resolved).slice(0, 5);
  const criticalAlerts = alerts.filter(a => a.type === 'critical' && !a.resolved);

  return (
    <div className="space-y-6">
      {/* Critical Alert Banner */}
      {criticalAlerts.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="relative overflow-hidden rounded-xl bg-red-500/10 border border-red-500/30 p-4"
        >
          <div className="absolute inset-0 bg-gradient-to-r from-red-500/5 to-transparent" />
          <div className="relative flex items-center gap-3">
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-red-500/20 flex items-center justify-center pulse-danger">
              <AlertTriangle className="w-4 h-4 text-red-400" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <span className="text-sm font-semibold text-red-300">CRITICAL THREAT DETECTED</span>
                <ThreatBadge level="critical" size="xs" pulse />
              </div>
              <p className="text-xs text-red-400/80 mt-0.5 truncate">
                {criticalAlerts[0].message}
              </p>
            </div>
            <div className="text-xs text-red-400/60 font-mono flex-shrink-0">
              {timeAgo(criticalAlerts[0].timestamp)}
            </div>
          </div>
        </motion.div>
      )}

      {/* Top Metrics Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="CPU Usage"
          value={systemMetrics.cpu.toFixed(1)}
          unit="%"
          icon={<Cpu className="w-5 h-5" />}
          color={systemMetrics.cpu > 80 ? 'red' : systemMetrics.cpu > 60 ? 'yellow' : 'blue'}
          trend={2.3}
          subtitle="4 cores active"
          progress={systemMetrics.cpu}
          delay={0}
        />
        <MetricCard
          title="Memory Usage"
          value={systemMetrics.memory.toFixed(1)}
          unit="%"
          icon={<MemoryStick className="w-5 h-5" />}
          color={systemMetrics.memory > 80 ? 'red' : 'purple'}
          trend={-1.2}
          subtitle="16 GB total"
          progress={systemMetrics.memory}
          delay={0.05}
        />
        <MetricCard
          title="Disk Usage"
          value={systemMetrics.disk.toFixed(1)}
          unit="%"
          icon={<HardDrive className="w-5 h-5" />}
          color="orange"
          trend={0.4}
          subtitle="512 GB SSD"
          progress={systemMetrics.disk}
          delay={0.1}
        />
        <MetricCard
          title="Active Processes"
          value={systemMetrics.activeProcesses}
          icon={<Activity className="w-5 h-5" />}
          color="green"
          trend={-3.1}
          subtitle="3 flagged suspicious"
          delay={0.15}
        />
      </div>

      {/* Second Row Metrics */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Files Modified"
          value={systemMetrics.filesModified.toLocaleString()}
          icon={<FileWarning className="w-5 h-5" />}
          color="yellow"
          trend={12.4}
          subtitle="Last 24 hours"
          delay={0.2}
        />
        <MetricCard
          title="Active Alerts"
          value={activeAlerts.length}
          icon={<ShieldAlert className="w-5 h-5" />}
          color="red"
          trend={8.9}
          subtitle={`${criticalAlerts.length} critical`}
          delay={0.25}
        />
        <MetricCard
          title="Protected Files"
          value={systemMetrics.protectedFiles.toLocaleString()}
          icon={<Lock className="w-5 h-5" />}
          color="green"
          subtitle="Under active guard"
          delay={0.3}
        />
        <MetricCard
          title="System Uptime"
          value={systemMetrics.uptime}
          icon={<Clock className="w-5 h-5" />}
          color="blue"
          subtitle="99.97% availability"
          delay={0.35}
        />
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* CPU + Memory Chart */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="xl:col-span-2 bg-slate-800/60 rounded-xl border border-slate-700/50 p-5"
        >
          <div className="flex items-center justify-between mb-5">
            <div>
              <h3 className="text-sm font-semibold text-slate-200">System Performance</h3>
              <p className="text-xs text-slate-500 mt-0.5">Real-time CPU & Memory usage</p>
            </div>
            <div className="flex items-center gap-4 text-xs">
              <div className="flex items-center gap-1.5">
                <div className="w-3 h-0.5 bg-blue-400 rounded" />
                <span className="text-slate-400">CPU</span>
              </div>
              <div className="flex items-center gap-1.5">
                <div className="w-3 h-0.5 bg-purple-400 rounded" />
                <span className="text-slate-400">Memory</span>
              </div>
            </div>
          </div>
          <div className="h-[220px]">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={cpuHistory.map((d, i) => ({
                time: d.time,
                CPU: d.cpu,
                Memory: memoryHistory[i]?.memory ?? 60,
              }))}>
                <defs>
                  <linearGradient id="cpuGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#2563EB" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#2563EB" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="memGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#8B5CF6" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#8B5CF6" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" />
                <XAxis
                  dataKey="time"
                  tick={{ fill: '#475569', fontSize: 10 }}
                  tickLine={false}
                  axisLine={false}
                  interval={11}
                />
                <YAxis
                  tick={{ fill: '#475569', fontSize: 10 }}
                  tickLine={false}
                  axisLine={false}
                  domain={[0, 100]}
                  tickFormatter={v => `${v}%`}
                />
                <Tooltip content={<CustomTooltip />} />
                <Area
                  type="monotone"
                  dataKey="CPU"
                  stroke="#2563EB"
                  strokeWidth={2}
                  fill="url(#cpuGrad)"
                  dot={false}
                  activeDot={{ r: 4, fill: '#2563EB' }}
                />
                <Area
                  type="monotone"
                  dataKey="Memory"
                  stroke="#8B5CF6"
                  strokeWidth={2}
                  fill="url(#memGrad)"
                  dot={false}
                  activeDot={{ r: 4, fill: '#8B5CF6' }}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </motion.div>

        {/* Threat Meter + Status */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.45 }}
          className="bg-slate-800/60 rounded-xl border border-slate-700/50 p-5"
        >
          <div className="mb-4">
            <h3 className="text-sm font-semibold text-slate-200">System Health</h3>
            <p className="text-xs text-slate-500 mt-0.5">Overall threat assessment</p>
          </div>

          <div className="flex justify-center mb-5">
            <RiskMeter score={systemMetrics.threatScore} size="lg" />
          </div>

          <div className="space-y-3">
            <StatusRow icon={<CheckCircle className="w-4 h-4 text-emerald-400" />} label="ML Engine" status="Active" color="emerald" />
            <StatusRow icon={<Eye className="w-4 h-4 text-blue-400" />} label="File Monitor" status="Scanning" color="blue" />
            <StatusRow icon={<Server className="w-4 h-4 text-purple-400" />} label="Process Guard" status="Active" color="purple" />
            <StatusRow
              icon={<Zap className="w-4 h-4 text-yellow-400" />}
              label="Auto-Kill"
              status="Standby"
              color="yellow"
            />
          </div>
        </motion.div>
      </div>

      {/* Bottom Grid: Threats Chart + Recent Alerts + Top Threats */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* Threats over time */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="xl:col-span-2 bg-slate-800/60 rounded-xl border border-slate-700/50 p-5"
        >
          <div className="flex items-center justify-between mb-5">
            <div>
              <h3 className="text-sm font-semibold text-slate-200">Threat Timeline</h3>
              <p className="text-xs text-slate-500 mt-0.5">Detection events over last 24 hours</p>
            </div>
            <div className="flex gap-2">
              {(['24h'] as const).map(r => (
                <button
                  key={r}
                  className="text-[10px] px-2 py-1 rounded-md bg-blue-600/20 text-blue-400 border border-blue-500/30 font-medium"
                >
                  {r}
                </button>
              ))}
            </div>
          </div>
          <div className="h-[200px]">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={threatsData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" />
                <XAxis dataKey="time" tick={{ fill: '#475569', fontSize: 10 }} tickLine={false} axisLine={false} />
                <YAxis tick={{ fill: '#475569', fontSize: 10 }} tickLine={false} axisLine={false} />
                <Tooltip content={<CustomTooltip />} />
                <Legend
                  wrapperStyle={{ fontSize: 10, color: '#94A3B8' }}
                  iconType="circle"
                  iconSize={6}
                />
                <Line type="monotone" dataKey="critical" stroke="#EF4444" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="high" stroke="#F97316" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="medium" stroke="#F59E0B" strokeWidth={1.5} dot={false} />
                <Line type="monotone" dataKey="low" stroke="#3B82F6" strokeWidth={1.5} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </motion.div>

        {/* Recent Alerts - Live Feed */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.55 }}
        >
          <LiveThreatFeed maxItems={5} />
        </motion.div>
      </div>

      {/* Top Threats */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6 }}
        className="bg-slate-800/60 rounded-xl border border-slate-700/50 p-5"
      >
        <div className="flex items-center justify-between mb-5">
          <div>
            <h3 className="text-sm font-semibold text-slate-200">Top Threats This Week</h3>
            <p className="text-xs text-slate-500 mt-0.5">Most frequent attack patterns detected</p>
          </div>
          <TrendingUp className="w-4 h-4 text-slate-500" />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[
            { name: 'WannaCry Variant', count: 23, level: 'critical' as const, icon: '🔐' },
            { name: 'Shadow Copy Deletion', count: 18, level: 'high' as const, icon: '🗑️' },
            { name: 'Mass Encryption', count: 15, level: 'high' as const, icon: '🔒' },
            { name: 'PowerShell Obfuscation', count: 34, level: 'medium' as const, icon: '💻' },
          ].map((threat, idx) => (
            <motion.div
              key={threat.name}
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.65 + idx * 0.05 }}
              className="p-4 rounded-lg bg-slate-700/30 border border-slate-700/50 hover:bg-slate-700/50 transition-colors"
            >
              <div className="flex items-start justify-between mb-3">
                <span className="text-2xl">{threat.icon}</span>
                <ThreatBadge level={threat.level} size="xs" showIcon={false} />
              </div>
              <div className="text-sm font-medium text-slate-200 mb-1">{threat.name}</div>
              <div className="text-2xl font-bold text-slate-100 counter-text">{threat.count}</div>
              <div className="text-xs text-slate-500">detections</div>
            </motion.div>
          ))}
        </div>
      </motion.div>
    </div>
  );
};

const StatusRow: React.FC<{
  icon: React.ReactNode;
  label: string;
  status: string;
  color: string;
}> = ({ icon, label, status, color }) => {
  const dotColor = {
    emerald: 'bg-emerald-400',
    blue: 'bg-blue-400',
    purple: 'bg-purple-400',
    yellow: 'bg-yellow-400',
    red: 'bg-red-400',
  }[color] ?? 'bg-slate-400';

  const textColor = {
    emerald: 'text-emerald-400',
    blue: 'text-blue-400',
    purple: 'text-purple-400',
    yellow: 'text-yellow-400',
    red: 'text-red-400',
  }[color] ?? 'text-slate-400';

  return (
    <div className="flex items-center justify-between py-2 border-b border-slate-700/30 last:border-0">
      <div className="flex items-center gap-2">
        {icon}
        <span className="text-xs text-slate-300">{label}</span>
      </div>
      <div className="flex items-center gap-1.5">
        <div className={cn('w-1.5 h-1.5 rounded-full', dotColor)} />
        <span className={cn('text-xs font-medium', textColor)}>{status}</span>
      </div>
    </div>
  );
};
