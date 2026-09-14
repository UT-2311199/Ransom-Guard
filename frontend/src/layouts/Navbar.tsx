import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Bell, Search, Shield, AlertTriangle, CheckCircle,
  Info, X, ChevronRight, Wifi, WifiOff, RefreshCw,
} from 'lucide-react';
import { useApp } from '../context/AppContext';
import { ThreatBadge } from '../components/ThreatBadge';
import { cn, timeAgo } from '../utils/helpers';
import toast from 'react-hot-toast';

interface NavbarProps {
  sidebarWidth: number;
  pageTitle: string;
  pageSubtitle?: string;
}

export const Navbar: React.FC<NavbarProps> = ({ sidebarWidth, pageTitle, pageSubtitle }) => {
  const { alerts, isMonitoring, toggleMonitoring, threatLevel, systemMetrics } = useApp();
  const [showNotifications, setShowNotifications] = useState(false);
  const [showSearch, setShowSearch] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const notifRef = useRef<HTMLDivElement>(null);
  const searchRef = useRef<HTMLInputElement>(null);

  const unresolvedAlerts = alerts.filter(a => !a.resolved);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (notifRef.current && !notifRef.current.contains(e.target as Node)) {
        setShowNotifications(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  useEffect(() => {
    if (showSearch && searchRef.current) {
      searchRef.current.focus();
    }
  }, [showSearch]);

  const getThreatIcon = (type: string) => {
    switch (type) {
      case 'critical': return <AlertTriangle className="w-4 h-4 text-red-400" />;
      case 'high': return <AlertTriangle className="w-4 h-4 text-orange-400" />;
      case 'medium': return <Info className="w-4 h-4 text-yellow-400" />;
      default: return <Info className="w-4 h-4 text-blue-400" />;
    }
  };

  const handleToggleMonitoring = () => {
    toggleMonitoring();
    toast.success(isMonitoring ? 'Monitoring paused' : 'Monitoring resumed', {
      icon: isMonitoring ? '⏸️' : '▶️',
    });
  };

  return (
    <header
      className="fixed top-0 right-0 z-30 h-16 flex items-center bg-slate-900/90 backdrop-blur-xl border-b border-slate-700/50"
      style={{ left: sidebarWidth }}
    >
      <div className="flex items-center justify-between w-full px-6">
        {/* Left: Page title */}
        <div>
          <h1 className="text-lg font-semibold text-slate-100 leading-none">{pageTitle}</h1>
          {pageSubtitle && (
            <p className="text-xs text-slate-500 mt-0.5">{pageSubtitle}</p>
          )}
        </div>

        {/* Right: Actions */}
        <div className="flex items-center gap-2">
          {/* Search */}
          <AnimatePresence>
            {showSearch ? (
              <motion.div
                initial={{ width: 0, opacity: 0 }}
                animate={{ width: 240, opacity: 1 }}
                exit={{ width: 0, opacity: 0 }}
                transition={{ duration: 0.2 }}
                className="flex items-center gap-2 bg-slate-800/80 border border-slate-700/50 rounded-lg px-3 overflow-hidden"
              >
                <Search className="w-4 h-4 text-slate-400 flex-shrink-0" />
                <input
                  ref={searchRef}
                  type="text"
                  placeholder="Search threats, files..."
                  value={searchQuery}
                  onChange={e => setSearchQuery(e.target.value)}
                  onKeyDown={e => e.key === 'Escape' && setShowSearch(false)}
                  className="bg-transparent text-sm text-slate-200 placeholder-slate-500 w-full py-2 focus:outline-none"
                />
                <button
                  onClick={() => { setShowSearch(false); setSearchQuery(''); }}
                  className="flex-shrink-0 text-slate-500 hover:text-slate-300"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              </motion.div>
            ) : (
              <motion.button
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                onClick={() => setShowSearch(true)}
                className="p-2 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 transition-colors"
              >
                <Search className="w-5 h-5" />
              </motion.button>
            )}
          </AnimatePresence>

          {/* Threat level badge */}
          <ThreatBadge level={threatLevel} size="sm" pulse={threatLevel === 'critical'} />

          {/* Monitoring toggle */}
          <button
            onClick={handleToggleMonitoring}
            className={cn(
              'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-200',
              isMonitoring
                ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/25 hover:bg-emerald-500/25'
                : 'bg-slate-700/50 text-slate-400 border border-slate-600/50 hover:bg-slate-700'
            )}
          >
            {isMonitoring
              ? <><Wifi className="w-3.5 h-3.5" /> Live</>
              : <><WifiOff className="w-3.5 h-3.5" /> Paused</>
            }
          </button>

          {/* Notifications */}
          <div ref={notifRef} className="relative">
            <button
              onClick={() => setShowNotifications(v => !v)}
              className={cn(
                'relative p-2 rounded-lg transition-colors',
                showNotifications
                  ? 'bg-blue-600/20 text-blue-400'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              )}
            >
              <Bell className="w-5 h-5" />
              {unresolvedAlerts.length > 0 && (
                <motion.span
                  key={unresolvedAlerts.length}
                  initial={{ scale: 0.6 }}
                  animate={{ scale: 1 }}
                  className="absolute -top-0.5 -right-0.5 w-4 h-4 rounded-full bg-red-500 text-white text-[10px] font-bold flex items-center justify-center"
                >
                  {unresolvedAlerts.length > 9 ? '9+' : unresolvedAlerts.length}
                </motion.span>
              )}
            </button>

            {/* Notification dropdown */}
            <AnimatePresence>
              {showNotifications && (
                <motion.div
                  initial={{ opacity: 0, y: -10, scale: 0.95 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: -10, scale: 0.95 }}
                  transition={{ duration: 0.2 }}
                  className="absolute right-0 top-full mt-2 w-96 bg-slate-800 border border-slate-700/80 rounded-xl shadow-2xl overflow-hidden"
                >
                  <div className="flex items-center justify-between px-4 py-3 border-b border-slate-700/50">
                    <div className="flex items-center gap-2">
                      <Bell className="w-4 h-4 text-slate-400" />
                      <span className="text-sm font-semibold text-slate-200">Alerts</span>
                      {unresolvedAlerts.length > 0 && (
                        <span className="bg-red-500/20 text-red-400 text-[10px] font-bold px-1.5 py-0.5 rounded-full">
                          {unresolvedAlerts.length} new
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-1">
                      <button
                        className="p-1.5 hover:bg-slate-700/50 rounded-lg text-slate-400 hover:text-slate-200 transition-colors"
                        title="Refresh"
                      >
                        <RefreshCw className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>

                  <div className="max-h-80 overflow-y-auto">
                    {alerts.slice(0, 10).map((alert, idx) => (
                      <motion.div
                        key={alert.id}
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: idx * 0.03 }}
                        className={cn(
                          'flex items-start gap-3 px-4 py-3 border-b border-slate-700/30 hover:bg-slate-700/20 transition-colors',
                          alert.resolved ? 'opacity-50' : ''
                        )}
                      >
                        <div className="flex-shrink-0 mt-0.5">
                          {alert.resolved
                            ? <CheckCircle className="w-4 h-4 text-emerald-400" />
                            : getThreatIcon(alert.type)
                          }
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-xs text-slate-200 leading-relaxed line-clamp-2">
                            {alert.message}
                          </p>
                          <div className="flex items-center gap-2 mt-1">
                            <span className="text-[10px] font-mono text-slate-500">{alert.process}</span>
                            <span className="text-[10px] text-slate-600">•</span>
                            <span className="text-[10px] text-slate-500">{timeAgo(alert.timestamp)}</span>
                          </div>
                        </div>
                        <ChevronRight className="w-3.5 h-3.5 text-slate-600 flex-shrink-0 mt-0.5" />
                      </motion.div>
                    ))}
                  </div>

                  <div className="px-4 py-3 bg-slate-800/50">
                    <button
                      onClick={() => setShowNotifications(false)}
                      className="w-full text-xs text-blue-400 font-medium hover:text-blue-300 transition-colors text-center"
                    >
                      View all alerts →
                    </button>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* System health dot */}
          <div className="flex items-center gap-2 pl-2 border-l border-slate-700/50">
            <div className="text-right">
              <div className="text-xs font-medium text-slate-300">
                {systemMetrics.cpu.toFixed(1)}% CPU
              </div>
              <div className="text-[10px] text-slate-500">
                {systemMetrics.memory.toFixed(1)}% MEM
              </div>
            </div>
            <div className="w-8 h-8 rounded-full bg-blue-600/20 border border-blue-500/30 flex items-center justify-center">
              <Shield className="w-4 h-4 text-blue-400" />
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};
