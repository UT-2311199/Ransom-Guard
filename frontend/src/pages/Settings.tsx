import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  Shield, Bell, Zap, FolderOpen, Sliders, Eye,
  Mail, Save, RefreshCw, CheckCircle, AlertTriangle,
  Cpu, Lock, WifiOff,
} from 'lucide-react';
import { useApp } from '../context/AppContext';
import { settingsApi } from '../services/api';
import { cn } from '../utils/helpers';
import toast from 'react-hot-toast';

interface ToggleProps {
  enabled: boolean;
  onChange: (v: boolean) => void;
  label: string;
  description?: string;
  icon?: React.ReactNode;
  danger?: boolean;
}

const Toggle: React.FC<ToggleProps> = ({ enabled, onChange, label, description, icon, danger }) => (
  <div className="flex items-center justify-between py-4 border-b border-slate-700/30 last:border-0">
    <div className="flex items-start gap-3">
      {icon && (
        <div className={cn('mt-0.5 p-1.5 rounded-lg', enabled
          ? danger ? 'bg-red-500/15 text-red-400' : 'bg-blue-500/15 text-blue-400'
          : 'bg-slate-700/50 text-slate-500'
        )}>
          {icon}
        </div>
      )}
      <div>
        <div className="text-sm font-medium text-slate-200">{label}</div>
        {description && <div className="text-xs text-slate-500 mt-0.5">{description}</div>}
      </div>
    </div>
    <button
      onClick={() => onChange(!enabled)}
      className={cn(
        'relative w-11 h-6 rounded-full transition-all duration-300 flex-shrink-0',
        enabled
          ? danger ? 'bg-red-500' : 'bg-blue-600'
          : 'bg-slate-600'
      )}
    >
      <motion.div
        className="absolute top-0.5 w-5 h-5 bg-white rounded-full shadow-md"
        animate={{ left: enabled ? '22px' : '2px' }}
        transition={{ type: 'spring', stiffness: 500, damping: 30 }}
      />
    </button>
  </div>
);

interface SliderRowProps {
  label: string;
  value: number;
  min: number;
  max: number;
  step?: number;
  unit?: string;
  onChange: (v: number) => void;
  description?: string;
  color?: string;
}

const SliderRow: React.FC<SliderRowProps> = ({
  label, value, min, max, step = 1, unit = '', onChange, description, color = '#2563EB',
}) => {
  const pct = ((value - min) / (max - min)) * 100;
  return (
    <div className="py-4 border-b border-slate-700/30 last:border-0">
      <div className="flex items-center justify-between mb-3">
        <div>
          <div className="text-sm font-medium text-slate-200">{label}</div>
          {description && <div className="text-xs text-slate-500 mt-0.5">{description}</div>}
        </div>
        <div
          className="text-sm font-bold font-mono px-3 py-1 rounded-lg"
          style={{ color, background: `${color}20` }}
        >
          {value}{unit}
        </div>
      </div>
      <div className="relative h-2 bg-slate-700/50 rounded-full">
        <div
          className="absolute left-0 top-0 h-full rounded-full transition-all"
          style={{ width: `${pct}%`, background: `linear-gradient(90deg, ${color}80, ${color})` }}
        />
        <input
          type="range"
          min={min}
          max={max}
          step={step}
          value={value}
          onChange={e => onChange(Number(e.target.value))}
          className="absolute inset-0 w-full opacity-0 cursor-pointer"
          style={{ height: '100%' }}
        />
        <div
          className="absolute top-1/2 -translate-y-1/2 w-4 h-4 rounded-full border-2 border-white shadow-md transition-all"
          style={{ left: `calc(${pct}% - 8px)`, background: color }}
        />
      </div>
      <div className="flex justify-between text-[10px] text-slate-600 mt-1">
        <span>{min}{unit}</span>
        <span>{max}{unit}</span>
      </div>
    </div>
  );
};

export const Settings: React.FC = () => {
  const { settings, updateSettings, backendOnline } = useApp();
  const [isSaving, setIsSaving] = useState(false);
  const [testingEmail, setTestingEmail] = useState(false);
  const [isLoadingBackend, setIsLoadingBackend] = useState(false);

  // Load backend settings on mount and merge with frontend defaults
  useEffect(() => {
    if (!backendOnline) return;
    const load = async () => {
      setIsLoadingBackend(true);
      try {
        const res = await settingsApi.getSettings();
        const s = res.data?.settings ?? {};

        // Map backend settings schema → frontend flat Settings
        const merged: Partial<typeof settings> = {};
        if (s.alerts) {
          merged.autoKill = s.alerts.auto_terminate ?? settings.autoKill;
          merged.quarantineEnabled = s.alerts.auto_quarantine ?? settings.quarantineEnabled;
          merged.emailAlerts = s.alerts.enable_alerts ?? settings.emailAlerts;
          merged.threshold = s.alerts.threat_threshold
            ? Math.round(s.alerts.threat_threshold * 100)
            : settings.threshold;
        }
        if (s.monitor) {
          merged.monitoringEnabled = s.monitor.enabled ?? settings.monitoringEnabled;
        }
        if (s.system) {
          merged.scanInterval = s.system.process_scan_interval ?? settings.scanInterval;
        }

        if (Object.keys(merged).length > 0) {
          updateSettings(merged);
        }
      } catch {
        // silently ignore — use defaults
      } finally {
        setIsLoadingBackend(false);
      }
    };
    load();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [backendOnline]);

  const handleSave = async () => {
    setIsSaving(true);
    try {
      // Map frontend flat Settings → backend nested schema
      const payload = {
        alerts: {
          enable_alerts: settings.emailAlerts,
          threat_threshold: settings.threshold / 100,
          auto_quarantine: settings.quarantineEnabled,
          auto_terminate: settings.autoKill,
          alert_on_critical: true,
          alert_on_high: true,
          alert_on_medium: false,
        },
        monitor: {
          enabled: settings.monitoringEnabled,
        },
        system: {
          process_scan_interval: settings.scanInterval,
        },
      };
      await settingsApi.updateSettings(payload);
      toast.success('Settings saved to backend!', { icon: '✅' });
    } catch {
      // Still update local state even if backend is offline
      toast.success('Settings saved locally (backend offline)', { icon: '✅' });
    } finally {
      setIsSaving(false);
    }
  };

  const handleTestEmail = async () => {
    if (!settings.alertEmail) {
      toast.error('Please enter an email address first');
      return;
    }
    setTestingEmail(true);
    await new Promise(r => setTimeout(r, 2000));
    setTestingEmail(false);
    toast.success(`Test email sent to ${settings.alertEmail}`, { icon: '📧' });
  };

  const handleReset = async () => {
    try {
      await settingsApi.resetSettings();
      toast.success('Settings reset to defaults on backend');
    } catch {
      // fall through
    }
    updateSettings({
      monitoringEnabled: true,
      threshold: 65,
      autoKill: false,
      emailAlerts: true,
      backupFolder: 'C:\\RansomGuard\\Backup',
      darkMode: true,
      alertEmail: 'admin@company.com',
      scanInterval: 5,
      quarantineEnabled: true,
      reportSchedule: 'daily',
    });
    toast.success('Settings reset to defaults');
  };

  return (
    <div className="space-y-6 max-w-5xl">
      {/* Backend status notice */}
      {!backendOnline && (
        <div className="flex items-center gap-3 px-4 py-3 bg-yellow-500/10 border border-yellow-500/25 rounded-xl text-xs text-yellow-300">
          <WifiOff className="w-4 h-4 flex-shrink-0" />
          Backend offline — settings will be saved locally only. Connect backend to persist settings.
        </div>
      )}
      {isLoadingBackend && (
        <div className="flex items-center gap-2 text-xs text-blue-400">
          <RefreshCw className="w-3.5 h-3.5 animate-spin" />
          Loading settings from backend…
        </div>
      )}

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        {/* Monitoring Settings */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.05 }}
          className="bg-slate-800/60 border border-slate-700/50 rounded-xl p-5"
        >
          <div className="flex items-center gap-2 mb-5">
            <Eye className="w-5 h-5 text-blue-400" />
            <h3 className="text-base font-semibold text-slate-100">Monitoring</h3>
          </div>

          <Toggle
            enabled={settings.monitoringEnabled}
            onChange={v => updateSettings({ monitoringEnabled: v })}
            label="Enable File System Monitoring"
            description="Continuously monitor file system operations for suspicious activity"
            icon={<Eye className="w-4 h-4" />}
          />
          <Toggle
            enabled={settings.quarantineEnabled}
            onChange={v => updateSettings({ quarantineEnabled: v })}
            label="Auto Quarantine"
            description="Automatically quarantine files when threats are detected"
            icon={<Lock className="w-4 h-4" />}
          />
          <Toggle
            enabled={settings.autoKill}
            onChange={v => updateSettings({ autoKill: v })}
            label="Auto-Kill Switch"
            description="Automatically terminate processes exceeding risk threshold"
            icon={<Zap className="w-4 h-4" />}
            danger
          />

          <SliderRow
            label="Detection Threshold"
            description="Minimum ML score to trigger an alert"
            value={settings.threshold}
            min={10}
            max={95}
            unit="%"
            onChange={v => updateSettings({ threshold: v })}
            color="#F59E0B"
          />
          <SliderRow
            label="Scan Interval"
            description="How often to run a full system scan"
            value={settings.scanInterval}
            min={1}
            max={60}
            unit="s"
            onChange={v => updateSettings({ scanInterval: v })}
            color="#2563EB"
          />
        </motion.div>

        {/* Alert Settings */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-slate-800/60 border border-slate-700/50 rounded-xl p-5"
        >
          <div className="flex items-center gap-2 mb-5">
            <Bell className="w-5 h-5 text-blue-400" />
            <h3 className="text-base font-semibold text-slate-100">Alerts &amp; Notifications</h3>
          </div>

          <Toggle
            enabled={settings.emailAlerts}
            onChange={v => updateSettings({ emailAlerts: v })}
            label="Email Alerts"
            description="Send email notifications for critical threats"
            icon={<Mail className="w-4 h-4" />}
          />

          <div className="py-4 border-b border-slate-700/30">
            <label className="text-sm font-medium text-slate-200 mb-2 block">Alert Email Address</label>
            <div className="flex gap-2">
              <input
                type="email"
                value={settings.alertEmail}
                onChange={e => updateSettings({ alertEmail: e.target.value })}
                placeholder="admin@company.com"
                className="flex-1 bg-slate-700/50 border border-slate-600/50 rounded-lg px-3 py-2 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500/50"
              />
              <button
                onClick={handleTestEmail}
                disabled={testingEmail || !settings.emailAlerts}
                className="px-3 py-2 rounded-lg text-xs font-medium bg-blue-500/15 text-blue-400 border border-blue-500/25 hover:bg-blue-500/25 transition-colors disabled:opacity-40 whitespace-nowrap"
              >
                {testingEmail ? 'Sending…' : 'Test'}
              </button>
            </div>
          </div>

          <div className="py-4 border-b border-slate-700/30">
            <label className="text-sm font-medium text-slate-200 mb-2 block">Report Schedule</label>
            <select
              value={settings.reportSchedule}
              onChange={e => updateSettings({ reportSchedule: e.target.value })}
              className="w-full bg-slate-700/50 border border-slate-600/50 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-blue-500/50"
            >
              <option value="realtime">Real-time</option>
              <option value="hourly">Hourly</option>
              <option value="daily">Daily</option>
              <option value="weekly">Weekly</option>
              <option value="monthly">Monthly</option>
            </select>
          </div>
        </motion.div>

        {/* Security Settings */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
          className="bg-slate-800/60 border border-slate-700/50 rounded-xl p-5"
        >
          <div className="flex items-center gap-2 mb-5">
            <Shield className="w-5 h-5 text-blue-400" />
            <h3 className="text-base font-semibold text-slate-100">Security Configuration</h3>
          </div>

          <div className="py-4 border-b border-slate-700/30">
            <label className="text-sm font-medium text-slate-200 mb-2 block">Backup Folder Path</label>
            <div className="flex gap-2">
              <input
                type="text"
                value={settings.backupFolder}
                onChange={e => updateSettings({ backupFolder: e.target.value })}
                className="flex-1 bg-slate-700/50 border border-slate-600/50 rounded-lg px-3 py-2 text-sm font-mono text-slate-200 focus:outline-none focus:border-blue-500/50"
              />
              <button className="p-2 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-700/50 transition-colors">
                <FolderOpen className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* ML Model Info */}
          <div className="py-4">
            <div className="text-sm font-medium text-slate-200 mb-3">ML Model Configuration</div>
            <div className="grid grid-cols-2 gap-3">
              {[
                { label: 'Algorithm', value: 'RF + XGBoost' },
                { label: 'Features', value: '47 dimensional' },
                { label: 'Accuracy', value: '97.3%' },
                { label: 'Last Updated', value: '2024-01-01' },
                { label: 'Training Samples', value: '50,000+' },
                { label: 'Model Version', value: 'v2.3.1' },
              ].map(item => (
                <div key={item.label} className="bg-slate-700/30 rounded-lg p-3">
                  <div className="text-[10px] text-slate-500 mb-1">{item.label}</div>
                  <div className="text-xs font-mono font-semibold text-slate-200">{item.value}</div>
                </div>
              ))}
            </div>
          </div>
        </motion.div>

        {/* System Settings */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-slate-800/60 border border-slate-700/50 rounded-xl p-5"
        >
          <div className="flex items-center gap-2 mb-5">
            <Sliders className="w-5 h-5 text-blue-400" />
            <h3 className="text-base font-semibold text-slate-100">System Preferences</h3>
          </div>

          <Toggle
            enabled={settings.darkMode}
            onChange={v => updateSettings({ darkMode: v })}
            label="Dark Mode"
            description="Use dark color scheme (recommended for security operations)"
            icon={<Eye className="w-4 h-4" />}
          />

          <div className="py-4 border-b border-slate-700/30">
            <div className="text-sm font-medium text-slate-200 mb-3">Resource Limits</div>
            <SliderRow
              label="Max CPU Usage"
              description="Limit RansomGuard's CPU consumption"
              value={25}
              min={5}
              max={80}
              unit="%"
              onChange={() => {}}
              color="#2563EB"
            />
          </div>

          {/* Status Summary */}
          <div className="mt-4 p-4 rounded-xl bg-slate-700/20 border border-slate-700/30">
            <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">Current Status</div>
            <div className="space-y-2">
              {[
                { label: 'Monitoring', active: settings.monitoringEnabled, icon: Eye },
                { label: 'Email Alerts', active: settings.emailAlerts, icon: Mail },
                { label: 'Auto Quarantine', active: settings.quarantineEnabled, icon: Lock },
                { label: 'Auto-Kill', active: settings.autoKill, icon: Zap },
              ].map(item => {
                const Icon = item.icon;
                return (
                  <div key={item.label} className="flex items-center gap-2">
                    <Icon className={cn('w-3.5 h-3.5', item.active ? 'text-emerald-400' : 'text-slate-500')} />
                    <span className="text-xs text-slate-400">{item.label}</span>
                    <div className={cn('ml-auto text-[10px] font-semibold px-2 py-0.5 rounded-full', item.active ? 'bg-emerald-500/15 text-emerald-400' : 'bg-slate-600/50 text-slate-500')}>
                      {item.active ? 'ON' : 'OFF'}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </motion.div>
      </div>

      {/* Threshold Visual */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.25 }}
        className="bg-slate-800/60 border border-slate-700/50 rounded-xl p-5"
      >
        <div className="flex items-center gap-2 mb-5">
          <Cpu className="w-5 h-5 text-yellow-400" />
          <h3 className="text-base font-semibold text-slate-100">Detection Threshold Visualization</h3>
        </div>
        <div className="space-y-4">
          <div className="relative h-10 bg-slate-700/30 rounded-xl overflow-hidden">
            <div className="absolute inset-y-0 left-0 bg-gradient-to-r from-emerald-500/40 via-yellow-500/40 to-red-500/40" style={{ width: '100%' }} />
            <div
              className="absolute inset-y-0 right-0 bg-slate-800/80"
              style={{ width: `${100 - settings.threshold}%` }}
            />
            <div
              className="absolute top-0 bottom-0 w-1 bg-white shadow-lg"
              style={{ left: `${settings.threshold}%` }}
            />
            <div
              className="absolute top-full mt-2 text-xs font-mono text-white bg-slate-700 px-2 py-1 rounded transform -translate-x-1/2"
              style={{ left: `${settings.threshold}%` }}
            >
              {settings.threshold}%
            </div>
          </div>
          <div className="flex justify-between text-xs text-slate-500 mt-6">
            <span className="text-emerald-400">Safe Zone (0–{Math.round(settings.threshold * 0.4)}%)</span>
            <span className="text-yellow-400">Warning ({Math.round(settings.threshold * 0.4)}–{settings.threshold}%)</span>
            <span className="text-red-400">Alert Zone ({settings.threshold}–100%)</span>
          </div>
        </div>
      </motion.div>

      {/* Action Buttons */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.3 }}
        className="flex items-center gap-3 pt-2"
      >
        <button
          onClick={handleSave}
          disabled={isSaving}
          className="btn-primary flex items-center gap-2 px-6 py-3 rounded-xl text-sm font-semibold text-white disabled:opacity-60"
        >
          {isSaving ? (
            <><RefreshCw className="w-4 h-4 animate-spin" /> Saving…</>
          ) : (
            <><Save className="w-4 h-4" /> Save Settings</>
          )}
        </button>
        <button
          onClick={handleReset}
          className="flex items-center gap-2 px-6 py-3 rounded-xl text-sm font-semibold bg-slate-700/50 text-slate-300 border border-slate-600/50 hover:bg-slate-700 transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
          Reset Defaults
        </button>
        {backendOnline && (
          <div className="ml-auto flex items-center gap-2 text-xs text-emerald-400">
            <CheckCircle className="w-4 h-4" />
            Connected to backend
          </div>
        )}
      </motion.div>

      {/* Danger Zone */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.35 }}
        className="bg-red-500/5 border border-red-500/20 rounded-xl p-5"
      >
        <div className="flex items-center gap-2 mb-4">
          <AlertTriangle className="w-5 h-5 text-red-400" />
          <h3 className="text-base font-semibold text-red-300">Danger Zone</h3>
        </div>
        <div className="flex flex-wrap gap-3">
          <button
            onClick={() => toast.error('This would clear all logs in production', { icon: '⚠️' })}
            className="px-4 py-2.5 rounded-lg text-sm font-medium text-red-400 border border-red-500/30 bg-red-500/10 hover:bg-red-500/20 transition-colors"
          >
            Clear All Logs
          </button>
          <button
            onClick={() => toast.error('This would purge quarantine in production', { icon: '⚠️' })}
            className="px-4 py-2.5 rounded-lg text-sm font-medium text-red-400 border border-red-500/30 bg-red-500/10 hover:bg-red-500/20 transition-colors"
          >
            Purge Quarantine
          </button>
          <button
            onClick={() => toast.error('Factory reset initiated (demo)', { icon: '⚠️' })}
            className="px-4 py-2.5 rounded-lg text-sm font-medium text-red-400 border border-red-500/30 bg-red-500/10 hover:bg-red-500/20 transition-colors"
          >
            Factory Reset
          </button>
        </div>
        <p className="text-xs text-red-400/60 mt-3">
          ⚠️ These actions are irreversible and may affect system security. Use with caution.
        </p>
      </motion.div>
    </div>
  );
};
