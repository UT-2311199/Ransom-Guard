import React from 'react';
import { motion } from 'framer-motion';
import { useApp } from '../context/AppContext';
import { cn } from '../utils/helpers';
import { Shield, Wifi, AlertTriangle, CheckCircle } from 'lucide-react';

export const SystemHealthBar: React.FC = () => {
  const { systemMetrics, isMonitoring, alerts } = useApp();
  const activeAlerts = alerts.filter(a => !a.resolved).length;

  const healthScore = Math.max(0, 100 - systemMetrics.threatScore * 0.8);

  const healthColor = healthScore > 70 ? '#10B981' : healthScore > 40 ? '#F59E0B' : '#EF4444';

  return (
    <motion.div
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      className="fixed bottom-4 left-1/2 -translate-x-1/2 z-30 hidden xl:flex items-center gap-4 px-5 py-2.5 bg-slate-900/90 border border-slate-700/70 rounded-full backdrop-blur-xl shadow-2xl"
    >
      {/* Health indicator */}
      <div className="flex items-center gap-2">
        <div className="w-5 h-5 rounded-full flex items-center justify-center" style={{ background: `${healthColor}20` }}>
          {healthScore > 70
            ? <CheckCircle className="w-3 h-3" style={{ color: healthColor }} />
            : <AlertTriangle className="w-3 h-3" style={{ color: healthColor }} />
          }
        </div>
        <div className="text-[11px] font-mono" style={{ color: healthColor }}>
          {healthScore.toFixed(0)}% Health
        </div>
      </div>

      <div className="w-px h-4 bg-slate-700" />

      {/* CPU */}
      <div className="flex items-center gap-1.5">
        <span className="text-[10px] text-slate-500">CPU</span>
        <div className="w-16 h-1.5 bg-slate-700 rounded-full overflow-hidden">
          <div
            className="h-full rounded-full transition-all duration-1000"
            style={{
              width: `${systemMetrics.cpu}%`,
              background: systemMetrics.cpu > 80 ? '#EF4444' : '#2563EB',
            }}
          />
        </div>
        <span className="text-[10px] font-mono text-slate-400">{systemMetrics.cpu.toFixed(0)}%</span>
      </div>

      {/* Memory */}
      <div className="flex items-center gap-1.5">
        <span className="text-[10px] text-slate-500">MEM</span>
        <div className="w-16 h-1.5 bg-slate-700 rounded-full overflow-hidden">
          <div
            className="h-full rounded-full transition-all duration-1000"
            style={{
              width: `${systemMetrics.memory}%`,
              background: systemMetrics.memory > 85 ? '#EF4444' : '#8B5CF6',
            }}
          />
        </div>
        <span className="text-[10px] font-mono text-slate-400">{systemMetrics.memory.toFixed(0)}%</span>
      </div>

      <div className="w-px h-4 bg-slate-700" />

      {/* Status */}
      <div className="flex items-center gap-2">
        <div className={cn('flex items-center gap-1.5 text-[10px] font-medium', isMonitoring ? 'text-emerald-400' : 'text-slate-500')}>
          <Wifi className="w-3 h-3" />
          {isMonitoring ? 'Monitoring Active' : 'Paused'}
        </div>
      </div>

      {activeAlerts > 0 && (
        <>
          <div className="w-px h-4 bg-slate-700" />
          <div className="flex items-center gap-1.5">
            <div className="w-1.5 h-1.5 rounded-full bg-red-400 pulse-danger" />
            <span className="text-[10px] text-red-400 font-medium">{activeAlerts} alerts</span>
          </div>
        </>
      )}

      <div className="w-px h-4 bg-slate-700" />

      <div className="flex items-center gap-1.5">
        <Shield className="w-3 h-3 text-blue-400" />
        <span className="text-[10px] font-mono text-slate-400">RansomGuard v1.0</span>
      </div>
    </motion.div>
  );
};
