import React, { useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Radio, AlertTriangle } from 'lucide-react';
import { useApp } from '../context/AppContext';
import { ThreatBadge } from './ThreatBadge';
import { timeAgo } from '../utils/helpers';

export const LiveThreatFeed: React.FC<{ maxItems?: number }> = ({ maxItems = 6 }) => {
  const { alerts } = useApp();
  const feedRef = useRef<HTMLDivElement>(null);

  const recentAlerts = alerts
    .filter(a => !a.resolved)
    .slice(0, maxItems);

  useEffect(() => {
    if (feedRef.current) {
      feedRef.current.scrollTop = 0;
    }
  }, [alerts.length]);

  return (
    <div className="bg-slate-900/80 rounded-xl border border-slate-700/50 overflow-hidden">
      <div className="flex items-center gap-2 px-4 py-3 border-b border-slate-700/50 bg-slate-800/40">
        <div className="flex items-center gap-1.5">
          <div className="w-1.5 h-1.5 rounded-full bg-red-400 animate-pulse" />
          <Radio className="w-3.5 h-3.5 text-red-400" />
        </div>
        <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">Live Threat Feed</span>
        <span className="ml-auto text-[10px] text-slate-500 font-mono">{recentAlerts.length} active</span>
      </div>

      <div ref={feedRef} className="divide-y divide-slate-700/20 max-h-[360px] overflow-y-auto">
        <AnimatePresence mode="popLayout">
          {recentAlerts.length === 0 ? (
            <div className="flex items-center justify-center py-8 text-slate-500 text-sm">
              <div className="text-center">
                <AlertTriangle className="w-6 h-6 mx-auto mb-2 opacity-40" />
                <div className="text-xs">No active threats</div>
              </div>
            </div>
          ) : (
            recentAlerts.map((alert, idx) => (
              <motion.div
                key={alert.id}
                layout
                initial={{ opacity: 0, x: -20, height: 0 }}
                animate={{ opacity: 1, x: 0, height: 'auto' }}
                exit={{ opacity: 0, x: 20, height: 0 }}
                transition={{ duration: 0.3, delay: idx * 0.03 }}
                className="flex items-start gap-3 px-4 py-3 hover:bg-slate-700/20 transition-colors"
              >
                <ThreatBadge level={alert.type} size="xs" showIcon={false} className="flex-shrink-0 mt-0.5" />
                <div className="flex-1 min-w-0">
                  <p className="text-xs text-slate-200 leading-relaxed line-clamp-2">{alert.message}</p>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="text-[10px] font-mono text-slate-500">{alert.process}</span>
                    <span className="text-[10px] text-slate-600">•</span>
                    <span className="text-[10px] text-slate-500">{timeAgo(alert.timestamp)}</span>
                  </div>
                </div>
              </motion.div>
            ))
          )}
        </AnimatePresence>
      </div>
    </div>
  );
};
