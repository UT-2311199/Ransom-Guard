import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  LayoutDashboard, Activity, Cpu, ShieldAlert,
  History, BarChart3, FileText, Settings, ChevronLeft,
  ChevronRight, Shield, Zap, Radio,
} from 'lucide-react';
import { cn } from '../utils/helpers';
import { useApp } from '../context/AppContext';
import { ThreatBadge } from '../components/ThreatBadge';

interface NavItem {
  path: string;
  label: string;
  icon: React.FC<{ className?: string }>;
  badge?: string;
  group?: string;
}

const NAV_ITEMS: NavItem[] = [
  { path: '/', label: 'Dashboard', icon: LayoutDashboard, group: 'Overview' },
  { path: '/monitoring', label: 'Live File Activity', icon: Activity, group: 'Monitoring' },
  { path: '/process-monitor', label: 'Process Monitor', icon: Cpu, group: 'Monitoring' },
  { path: '/threat-detection', label: 'Threat Detection', icon: ShieldAlert, group: 'Security' },
  { path: '/threat-history', label: 'Threat History', icon: History, group: 'Security' },
  { path: '/analytics', label: 'Analytics', icon: BarChart3, group: 'Insights' },
  { path: '/reports', label: 'Reports', icon: FileText, group: 'Insights' },
  { path: '/settings', label: 'Settings', icon: Settings, group: 'System' },
];

const GROUP_ORDER = ['Overview', 'Monitoring', 'Security', 'Insights', 'System'];

interface SidebarProps {
  collapsed: boolean;
  setCollapsed: (v: boolean) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ collapsed, setCollapsed }) => {
  const location = useLocation();
  const { isMonitoring, threatLevel, alerts } = useApp();
  const unresolvedAlerts = alerts.filter(a => !a.resolved).length;

  const grouped = GROUP_ORDER.map(group => ({
    group,
    items: NAV_ITEMS.filter(i => i.group === group),
  })).filter(g => g.items.length > 0);

  return (
    <motion.aside
      className="fixed left-0 top-0 h-full z-40 flex flex-col bg-slate-900/95 border-r border-slate-700/50 backdrop-blur-xl"
      animate={{ width: collapsed ? 72 : 256 }}
      transition={{ duration: 0.3, ease: 'easeInOut' }}
    >
      {/* Logo */}
      <div className="flex items-center h-16 px-4 border-b border-slate-700/50 flex-shrink-0 overflow-hidden">
        <div className="flex items-center gap-3 min-w-0">
          <div className="relative flex-shrink-0">
            <div className="w-9 h-9 rounded-xl bg-blue-600 flex items-center justify-center glow-blue">
              <Shield className="w-5 h-5 text-white" />
            </div>
            <div
              className={cn(
                'absolute -top-0.5 -right-0.5 w-3 h-3 rounded-full border-2 border-slate-900',
                isMonitoring ? 'bg-emerald-400 pulse-success' : 'bg-slate-500'
              )}
            />
          </div>
          <AnimatePresence>
            {!collapsed && (
              <motion.div
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -10 }}
                transition={{ duration: 0.2 }}
                className="min-w-0"
              >
                <div className="font-bold text-white text-base leading-none">RansomGuard</div>
                <div className="text-xs text-slate-400 mt-0.5 font-medium truncate">ML Detection System</div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* Status indicator */}
      <AnimatePresence>
        {!collapsed && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="mx-3 mt-3 mb-1 px-3 py-2.5 rounded-lg bg-slate-800/60 border border-slate-700/50"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Radio className={cn('w-3.5 h-3.5', isMonitoring ? 'text-emerald-400' : 'text-slate-500')} />
                <span className="text-xs font-medium text-slate-300">
                  {isMonitoring ? 'Live Monitoring' : 'Monitoring Off'}
                </span>
              </div>
              <ThreatBadge level={threatLevel} size="xs" showIcon={false} />
            </div>
            {unresolvedAlerts > 0 && (
              <div className="mt-1.5 flex items-center gap-1.5">
                <Zap className="w-3 h-3 text-red-400" />
                <span className="text-xs text-red-400 font-medium">{unresolvedAlerts} active alerts</span>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto overflow-x-hidden py-2 px-2 space-y-0.5">
        {grouped.map(({ group, items }) => (
          <div key={group}>
            <AnimatePresence>
              {!collapsed && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="px-3 py-2 mt-3 first:mt-0"
                >
                  <span className="text-[10px] font-semibold uppercase tracking-widest text-slate-500">
                    {group}
                  </span>
                </motion.div>
              )}
            </AnimatePresence>
            {items.map((item) => {
              const isActive = location.pathname === item.path;
              const Icon = item.icon;
              const hasBadge = item.path === '/threat-detection' && unresolvedAlerts > 0;

              return (
                <NavLink key={item.path} to={item.path}>
                  <motion.div
                    className={cn(
                      'relative flex items-center gap-3 px-3 py-2.5 rounded-lg cursor-pointer',
                      'transition-all duration-200 group overflow-hidden',
                      isActive
                        ? 'bg-blue-600/15 border border-blue-500/25 text-blue-400'
                        : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                    )}
                    whileHover={{ x: collapsed ? 0 : 2 }}
                    transition={{ duration: 0.15 }}
                  >
                    {isActive && (
                      <motion.div
                        layoutId="activeTab"
                        className="absolute left-0 top-0 bottom-0 w-[3px] bg-blue-500 rounded-r-full"
                      />
                    )}
                    <div className={cn(
                      'relative flex-shrink-0 transition-colors duration-200',
                      isActive ? 'text-blue-400' : 'text-slate-400 group-hover:text-slate-200'
                    )}>
                      <Icon className="w-5 h-5" />
                      {hasBadge && collapsed && (
                        <div className="absolute -top-1 -right-1 w-2 h-2 rounded-full bg-red-500" />
                      )}
                    </div>

                    <AnimatePresence>
                      {!collapsed && (
                        <motion.div
                          initial={{ opacity: 0, x: -10 }}
                          animate={{ opacity: 1, x: 0 }}
                          exit={{ opacity: 0, x: -10 }}
                          transition={{ duration: 0.2 }}
                          className="flex items-center justify-between flex-1 min-w-0"
                        >
                          <span className="text-sm font-medium truncate">{item.label}</span>
                          {hasBadge && (
                            <span className="ml-auto flex-shrink-0 bg-red-500/20 text-red-400 text-[10px] font-bold px-1.5 py-0.5 rounded-full border border-red-500/30">
                              {unresolvedAlerts > 9 ? '9+' : unresolvedAlerts}
                            </span>
                          )}
                        </motion.div>
                      )}
                    </AnimatePresence>

                    {/* Tooltip for collapsed state */}
                    {collapsed && (
                      <div className="absolute left-full ml-3 px-3 py-1.5 bg-slate-800 border border-slate-700 rounded-lg text-sm font-medium text-slate-200 whitespace-nowrap opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity duration-200 shadow-xl z-50">
                        {item.label}
                        {hasBadge && (
                          <span className="ml-2 bg-red-500 text-white text-[10px] px-1.5 py-0.5 rounded-full">
                            {unresolvedAlerts}
                          </span>
                        )}
                      </div>
                    )}
                  </motion.div>
                </NavLink>
              );
            })}
          </div>
        ))}
      </nav>

      {/* Footer */}
      <div className="border-t border-slate-700/50 p-3 flex-shrink-0">
        <AnimatePresence>
          {!collapsed && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="mb-3 px-2 py-1"
            >
              <div className="text-[10px] text-slate-500 font-medium">
                RansomGuard v1.0.0
              </div>
              <div className="text-[10px] text-slate-600 mt-0.5">
                B.Tech Final Year Project
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Collapse button */}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className={cn(
            'w-full flex items-center gap-2.5 px-3 py-2.5 rounded-lg',
            'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60',
            'transition-all duration-200',
            collapsed ? 'justify-center' : ''
          )}
        >
          {collapsed
            ? <ChevronRight className="w-4.5 h-4.5" />
            : <>
                <ChevronLeft className="w-4.5 h-4.5" />
                <span className="text-sm font-medium">Collapse</span>
              </>
          }
        </button>
      </div>
    </motion.aside>
  );
};
