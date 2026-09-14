import React, { useState, useEffect, useMemo } from 'react';
import { motion } from 'framer-motion';
import {
  AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Legend,
} from 'recharts';
import {
  TrendingUp, BarChart3, PieChart as PieIcon, Activity,
  Calendar,
} from 'lucide-react';
import { useApp } from '../context/AppContext';
import { analyticsApi } from '../services/api';
import { generateThreatsOverTime, riskDistribution as MOCK_RISK, attackTypeData as MOCK_ATTACKS, weeklyStats as MOCK_WEEKLY } from '../utils/mockData';
import { useCpuHistory, useMemoryHistory, useNetworkHistory } from '../hooks/useRealTimeData';
import { cn } from '../utils/helpers';

const CHART_COLORS = ['#EF4444', '#F97316', '#F59E0B', '#8B5CF6', '#2563EB', '#10B981'];

const CustomTooltip = ({ active, payload, label }: { active?: boolean; payload?: { name: string; value: number; color: string }[]; label?: string }) => {
  if (active && payload?.length) {
    return (
      <div className="bg-slate-800 border border-slate-700/80 rounded-lg p-3 shadow-xl">
        <p className="text-xs text-slate-400 mb-2">{label}</p>
        {payload.map((e, i) => (
          <div key={i} className="flex items-center gap-2 text-xs">
            <div className="w-2 h-2 rounded-full" style={{ background: e.color }} />
            <span className="text-slate-300">{e.name}:</span>
            <span className="font-semibold" style={{ color: e.color }}>{typeof e.value === 'number' ? e.value.toFixed(1) : e.value}</span>
          </div>
        ))}
      </div>
    );
  }
  return null;
};

const CustomPieTooltip = ({ active, payload }: { active?: boolean; payload?: { name: string; value: number; payload: { color: string } }[] }) => {
  if (active && payload?.length) {
    return (
      <div className="bg-slate-800 border border-slate-700/80 rounded-lg p-3 shadow-xl">
        <div className="flex items-center gap-2 text-xs">
          <div className="w-2 h-2 rounded-full" style={{ background: payload[0].payload.color }} />
          <span className="text-slate-200 font-semibold">{payload[0].name}</span>
          <span className="text-slate-400">{payload[0].value}%</span>
        </div>
      </div>
    );
  }
  return null;
};

type TimeRange = '1h' | '24h' | '7d' | '30d';

interface AnalyticsData {
  summaryStats: { label: string; value: string; change: string; up: boolean }[];
  riskDistribution: { name: string; value: number; color: string }[];
  attackTypeData: { name: string; count: number; color: string }[];
  weeklyStats: { day: string; threats: number; blocked: number; resolved: number }[];
}

function buildAnalyticsFromBackend(data: Record<string, unknown>): AnalyticsData {
  const summary = (data.threat_summary as Record<string, unknown>) ?? {};
  const bySeverity = (data.threats_by_severity as Record<string, number>) ?? {};
  const dailyTrends = (data.daily_trends as { date: string; count: number; blocked?: number }[]) ?? [];
  const attackTypes = (data.attack_types as { name: string; count: number }[]) ?? [];

  const total = Number(summary.total_threats ?? 0);
  const critical = bySeverity.critical ?? 0;
  const high = bySeverity.high ?? 0;
  const medium = bySeverity.medium ?? 0;
  const low = bySeverity.low ?? 0;

  const summaryStats = [
    { label: 'Total Detections', value: total.toLocaleString(), change: summary.new_today != null ? `+${summary.new_today}` : '', up: true },
    { label: 'Avg Response Time', value: summary.avg_response_time != null ? String(summary.avg_response_time) : '—', change: '', up: false },
    { label: 'False Positive Rate', value: summary.false_positive_rate != null ? `${summary.false_positive_rate}%` : '—', change: '', up: false },
    { label: 'ML Accuracy', value: summary.ml_accuracy != null ? `${summary.ml_accuracy}%` : '97.3%', change: '', up: true },
  ];

  const totalSeverity = critical + high + medium + low || 1;
  const riskDistribution = [
    { name: 'Critical', value: Math.round((critical / totalSeverity) * 100), color: '#EF4444' },
    { name: 'High', value: Math.round((high / totalSeverity) * 100), color: '#F97316' },
    { name: 'Medium', value: Math.round((medium / totalSeverity) * 100), color: '#F59E0B' },
    { name: 'Low', value: Math.round((low / totalSeverity) * 100), color: '#3B82F6' },
  ].filter(d => d.value > 0);

  const DAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
  const weeklyStats = dailyTrends.slice(-7).map((d, i) => ({
    day: DAYS[new Date(d.date).getDay()] ?? `D${i + 1}`,
    threats: d.count,
    blocked: d.blocked ?? Math.floor(d.count * 0.9),
    resolved: Math.floor(d.count * 0.1),
  }));

  const atData = attackTypes.slice(0, 6).map((a, i) => ({
    name: a.name,
    count: a.count,
    color: CHART_COLORS[i] ?? '#2563EB',
  }));

  return { summaryStats, riskDistribution, weeklyStats, attackTypeData: atData };
}

export const Analytics: React.FC = () => {
  const { systemMetrics } = useApp();
  const [timeRange, setTimeRange] = useState<TimeRange>('24h');
  const cpuHistory = useCpuHistory(true, systemMetrics.cpu);
  const memHistory = useMemoryHistory(true, systemMetrics.memory);
  const netHistory = useNetworkHistory(true);

  const [analyticsData, setAnalyticsData] = useState<AnalyticsData | null>(null);
  const [analyticsLoading, setAnalyticsLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    const fetch = async () => {
      try {
        setAnalyticsLoading(true);
        const res = await analyticsApi.getAnalytics();
        const raw = res.data?.data ?? {};
        if (!cancelled) setAnalyticsData(buildAnalyticsFromBackend(raw as Record<string, unknown>));
      } catch {
        // Fall back to mock data
        if (!cancelled) setAnalyticsData(null);
      } finally {
        if (!cancelled) setAnalyticsLoading(false);
      }
    };
    fetch();
    return () => { cancelled = true; };
  }, []);

  const threatsData = useMemo(() => generateThreatsOverTime(timeRange), [timeRange]);

  const heatmapData = useMemo(() => {
    const hours = Array.from({ length: 24 }, (_, i) => i);
    const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
    return days.map(day => ({
      day,
      ...Object.fromEntries(hours.map(h => [`h${h}`, Math.floor(Math.random() * 100)])),
    }));
  }, []);

  const maxHeatVal = 100;

  // Resolved data — use backend or fall back to mock
  const summaryStats = analyticsData?.summaryStats ?? [
    { label: 'Total Detections', value: '—', change: '', up: true },
    { label: 'Avg Response Time', value: '—', change: '', up: false },
    { label: 'False Positive Rate', value: '—', change: '', up: false },
    { label: 'ML Accuracy', value: '—', change: '', up: true },
  ];
  const riskDistribution = analyticsData?.riskDistribution ?? MOCK_RISK;
  const attackTypeData = analyticsData?.attackTypeData?.length
    ? analyticsData.attackTypeData
    : MOCK_ATTACKS;
  const weeklyStats = analyticsData?.weeklyStats?.length
    ? analyticsData.weeklyStats
    : MOCK_WEEKLY;

  return (
    <div className="space-y-6">
      {/* Summary Metrics */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {summaryStats.map((s, i) => (
          <motion.div
            key={s.label}
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.05 }}
            className="bg-slate-800/60 border border-slate-700/50 rounded-xl px-5 py-4"
          >
            <div className={cn('text-2xl font-bold text-slate-100 counter-text', analyticsLoading && 'animate-pulse')}>
              {s.value}
            </div>
            <div className="text-xs text-slate-400 mt-0.5">{s.label}</div>
            {s.change && (
              <div className={cn('text-xs font-medium mt-2', s.up ? 'text-emerald-400' : 'text-blue-400')}>
                {s.change} vs last period
              </div>
            )}
          </motion.div>
        ))}
      </div>

      {/* Time Range Selector */}
      <div className="flex items-center gap-3 bg-slate-800/60 border border-slate-700/50 rounded-xl p-3">
        <Calendar className="w-4 h-4 text-slate-400" />
        <span className="text-xs text-slate-400 font-medium">Time Range:</span>
        <div className="flex items-center gap-1 bg-slate-700/30 rounded-lg p-1">
          {(['1h', '24h', '7d', '30d'] as TimeRange[]).map(r => (
            <button
              key={r}
              onClick={() => setTimeRange(r)}
              className={cn(
                'px-3 py-1.5 text-xs font-medium rounded-md transition-all',
                timeRange === r ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-slate-200'
              )}
            >
              {r}
            </button>
          ))}
        </div>
      </div>

      {/* Main Charts Row 1 */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        {/* Threats Over Time */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-slate-800/60 border border-slate-700/50 rounded-xl p-5"
        >
          <div className="flex items-center gap-2 mb-5">
            <TrendingUp className="w-4 h-4 text-blue-400" />
            <h3 className="text-sm font-semibold text-slate-200">Threats Detected Over Time</h3>
          </div>
          <div className="h-[220px]">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={threatsData}>
                <defs>
                  {['critical', 'high', 'medium', 'low'].map((key, i) => (
                    <linearGradient key={key} id={`grad_${key}`} x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor={CHART_COLORS[i]} stopOpacity={0.4} />
                      <stop offset="95%" stopColor={CHART_COLORS[i]} stopOpacity={0} />
                    </linearGradient>
                  ))}
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" />
                <XAxis dataKey="time" tick={{ fill: '#475569', fontSize: 10 }} tickLine={false} axisLine={false} />
                <YAxis tick={{ fill: '#475569', fontSize: 10 }} tickLine={false} axisLine={false} />
                <Tooltip content={<CustomTooltip />} />
                <Legend wrapperStyle={{ fontSize: 10, color: '#94A3B8' }} iconType="circle" iconSize={6} />
                {['critical', 'high', 'medium', 'low'].map((key, i) => (
                  <Area
                    key={key}
                    type="monotone"
                    dataKey={key}
                    stroke={CHART_COLORS[i]}
                    strokeWidth={2}
                    fill={`url(#grad_${key})`}
                    dot={false}
                  />
                ))}
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </motion.div>

        {/* Weekly Attack Bar Chart */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
          className="bg-slate-800/60 border border-slate-700/50 rounded-xl p-5"
        >
          <div className="flex items-center gap-2 mb-5">
            <BarChart3 className="w-4 h-4 text-blue-400" />
            <h3 className="text-sm font-semibold text-slate-200">Weekly Threat Response</h3>
          </div>
          <div className="h-[220px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={weeklyStats} barSize={18}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" />
                <XAxis dataKey="day" tick={{ fill: '#475569', fontSize: 10 }} tickLine={false} axisLine={false} />
                <YAxis tick={{ fill: '#475569', fontSize: 10 }} tickLine={false} axisLine={false} />
                <Tooltip content={<CustomTooltip />} />
                <Legend wrapperStyle={{ fontSize: 10, color: '#94A3B8' }} iconType="circle" iconSize={6} />
                <Bar dataKey="threats" name="Detected" fill="#EF4444" opacity={0.8} radius={[4, 4, 0, 0]} />
                <Bar dataKey="blocked" name="Blocked" fill="#10B981" opacity={0.8} radius={[4, 4, 0, 0]} />
                <Bar dataKey="resolved" name="Resolved" fill="#2563EB" opacity={0.8} radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </motion.div>
      </div>

      {/* Row 2: CPU/Memory + Risk Distribution */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* CPU & Memory */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="xl:col-span-2 bg-slate-800/60 border border-slate-700/50 rounded-xl p-5"
        >
          <div className="flex items-center gap-2 mb-5">
            <Activity className="w-4 h-4 text-blue-400" />
            <h3 className="text-sm font-semibold text-slate-200">System Resource Monitor</h3>
          </div>
          <div className="h-[220px]">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={cpuHistory.map((d, i) => ({
                time: d.time,
                CPU: d.cpu,
                Memory: memHistory[i]?.memory ?? 60,
                Network: ((netHistory[i]?.inbound ?? 10) as number) * 3,
              }))}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" />
                <XAxis dataKey="time" tick={{ fill: '#475569', fontSize: 10 }} tickLine={false} axisLine={false} interval={11} />
                <YAxis tick={{ fill: '#475569', fontSize: 10 }} tickLine={false} axisLine={false} domain={[0, 100]} tickFormatter={v => `${v}%`} />
                <Tooltip content={<CustomTooltip />} />
                <Legend wrapperStyle={{ fontSize: 10, color: '#94A3B8' }} iconType="circle" iconSize={6} />
                <Line type="monotone" dataKey="CPU" stroke="#2563EB" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="Memory" stroke="#8B5CF6" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="Network" stroke="#10B981" strokeWidth={1.5} dot={false} strokeDasharray="4 2" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </motion.div>

        {/* Risk Distribution Pie */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.25 }}
          className="bg-slate-800/60 border border-slate-700/50 rounded-xl p-5"
        >
          <div className="flex items-center gap-2 mb-5">
            <PieIcon className="w-4 h-4 text-blue-400" />
            <h3 className="text-sm font-semibold text-slate-200">Risk Distribution</h3>
          </div>
          <div className="h-[180px]">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={riskDistribution}
                  cx="50%"
                  cy="50%"
                  innerRadius={55}
                  outerRadius={80}
                  paddingAngle={3}
                  dataKey="value"
                >
                  {riskDistribution.map((entry, i) => (
                    <Cell key={i} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip content={<CustomPieTooltip />} />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="mt-3 space-y-1.5">
            {riskDistribution.map(item => (
              <div key={item.name} className="flex items-center justify-between text-xs">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full flex-shrink-0" style={{ background: item.color }} />
                  <span className="text-slate-400">{item.name}</span>
                </div>
                <span className="text-slate-300 font-mono font-semibold">{item.value}%</span>
              </div>
            ))}
          </div>
        </motion.div>
      </div>

      {/* Row 3: Attack Types + Heatmap */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        {/* Attack Types */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="bg-slate-800/60 border border-slate-700/50 rounded-xl p-5"
        >
          <div className="flex items-center gap-2 mb-5">
            <BarChart3 className="w-4 h-4 text-blue-400" />
            <h3 className="text-sm font-semibold text-slate-200">Attack Types Distribution</h3>
          </div>
          <div className="h-[250px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={attackTypeData} layout="vertical" barSize={14}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" horizontal={false} />
                <XAxis type="number" tick={{ fill: '#475569', fontSize: 10 }} tickLine={false} axisLine={false} />
                <YAxis type="category" dataKey="name" tick={{ fill: '#94A3B8', fontSize: 10 }} tickLine={false} axisLine={false} width={120} />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="count" name="Incidents" radius={[0, 4, 4, 0]}>
                  {attackTypeData.map((entry, i) => (
                    <Cell key={i} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </motion.div>

        {/* Threat Heatmap */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.35 }}
          className="bg-slate-800/60 border border-slate-700/50 rounded-xl p-5"
        >
          <div className="flex items-center gap-2 mb-5">
            <TrendingUp className="w-4 h-4 text-blue-400" />
            <h3 className="text-sm font-semibold text-slate-200">Activity Heatmap (24h × 7 Days)</h3>
          </div>
          <div className="overflow-x-auto">
            <div className="min-w-[500px]">
              {/* Hour labels — evenly spaced across the grid width */}
              <div className="flex ml-10 mb-1">
                {Array.from({ length: 24 }, (_, h) => (
                  <div
                    key={h}
                    className="flex-1 text-[9px] text-slate-500 text-center"
                  >
                    {h % 4 === 0 ? `${h.toString().padStart(2, '0')}h` : ''}
                  </div>
                ))}
              </div>
              <div className="mt-4 space-y-1.5">
                {heatmapData.map(row => (
                  <div key={row.day} className="flex items-center gap-1.5">
                    <span className="text-[10px] text-slate-500 w-8 flex-shrink-0">{row.day}</span>
                    <div className="flex gap-0.5 flex-1">
                      {Array.from({ length: 24 }, (_, h) => {
                        const val = Number(row[`h${h}` as keyof typeof row]) || 0;
                        const opacity = val / maxHeatVal;
                        const color = val > 70 ? '#EF4444' : val > 40 ? '#F59E0B' : '#2563EB';
                        return (
                          <div
                            key={h}
                            className="flex-1 h-5 rounded-sm cursor-pointer hover:ring-1 hover:ring-white/20 transition-all"
                            style={{ background: color, opacity: Math.max(0.1, opacity) }}
                            title={`${row.day} ${h.toString().padStart(2, '0')}:00 — ${val} events`}
                          />
                        );
                      })}
                    </div>
                  </div>
                ))}
              </div>
              {/* Legend */}
              <div className="flex items-center gap-3 mt-4 ml-10">
                <span className="text-[10px] text-slate-500">Low</span>
                <div className="flex gap-0.5">
                  {[0.1, 0.3, 0.5, 0.7, 0.9].map((o, i) => (
                    <div key={i} className="w-5 h-3 rounded-sm" style={{ background: '#2563EB', opacity: o }} />
                  ))}
                </div>
                <span className="text-[10px] text-slate-500">High</span>
              </div>
            </div>
          </div>
        </motion.div>
      </div>

      {/* Network Chart */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="bg-slate-800/60 border border-slate-700/50 rounded-xl p-5"
      >
        <div className="flex items-center gap-2 mb-5">
          <Activity className="w-4 h-4 text-emerald-400" />
          <h3 className="text-sm font-semibold text-slate-200">Network Traffic Analysis</h3>
          <span className="text-xs text-slate-500 ml-auto">MB/s — Live</span>
        </div>
        <div className="h-[180px]">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={netHistory}>
              <defs>
                <linearGradient id="inboundGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#10B981" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#10B981" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="outboundGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#F59E0B" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#F59E0B" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" />
              <XAxis dataKey="time" tick={{ fill: '#475569', fontSize: 10 }} tickLine={false} axisLine={false} interval={11} />
              <YAxis tick={{ fill: '#475569', fontSize: 10 }} tickLine={false} axisLine={false} tickFormatter={v => `${v}MB`} />
              <Tooltip content={<CustomTooltip />} />
              <Legend wrapperStyle={{ fontSize: 10, color: '#94A3B8' }} iconType="circle" iconSize={6} />
              <Area type="monotone" dataKey="inbound" name="Inbound" stroke="#10B981" strokeWidth={2} fill="url(#inboundGrad)" dot={false} />
              <Area type="monotone" dataKey="outbound" name="Outbound" stroke="#F59E0B" strokeWidth={2} fill="url(#outboundGrad)" dot={false} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </motion.div>
    </div>
  );
};
