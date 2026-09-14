import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';
import { systemApi, monitoringApi, threatApi, mlApi } from '../services/api';

export type ThreatLevel = 'critical' | 'high' | 'medium' | 'low' | 'safe';
export type ProcessStatus = 'running' | 'suspicious' | 'terminated' | 'quarantined';
export type FileOperation = 'CREATE' | 'MODIFY' | 'DELETE' | 'RENAME' | 'ENCRYPT' | 'READ';

export interface SystemMetrics {
  cpu: number;
  memory: number;
  disk: number;
  activeProcesses: number;
  filesModified: number;
  threatScore: number;
  networkIn: number;
  networkOut: number;
  uptime: string;
  protectedFiles: number;
}

export interface Alert {
  id: string;
  type: ThreatLevel;
  message: string;
  process: string;
  timestamp: Date;
  path?: string;
  resolved: boolean;
}

export interface MonitoringEntry {
  id: string;
  timestamp: Date;
  fileName: string;
  operation: FileOperation;
  path: string;
  process: string;
  pid: number;
  status: ThreatLevel;
  size?: string;
}

export interface ProcessEntry {
  pid: number;
  name: string;
  cpu: number;
  ram: number;
  riskScore: number;
  status: ProcessStatus;
  path: string;
  user: string;
  startTime: string;
}

export interface Settings {
  monitoringEnabled: boolean;
  threshold: number;
  autoKill: boolean;
  emailAlerts: boolean;
  backupFolder: string;
  darkMode: boolean;
  alertEmail: string;
  scanInterval: number;
  quarantineEnabled: boolean;
  reportSchedule: string;
}

export interface MLStatus {
  available: boolean;
  model_name: string | null;
  feature_count: number;
  error: string | null;
}

interface AppContextType {
  systemMetrics: SystemMetrics;
  alerts: Alert[];
  monitoringData: MonitoringEntry[];
  processes: ProcessEntry[];
  settings: Settings;
  isMonitoring: boolean;
  threatLevel: ThreatLevel;
  mlStatus: MLStatus;
  backendOnline: boolean;
  updateSettings: (s: Partial<Settings>) => void;
  dismissAlert: (id: string) => void;
  terminateProcess: (pid: number) => void;
  toggleMonitoring: () => void;
  addAlert: (alert: Omit<Alert, 'id' | 'timestamp'>) => void;
  refreshAll: () => void;
}

const AppContext = createContext<AppContextType | null>(null);

export const useApp = () => {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error('useApp must be used within AppProvider');
  return ctx;
};

function getThreatLevel(score: number): ThreatLevel {
  if (score >= 80) return 'critical';
  if (score >= 60) return 'high';
  if (score >= 40) return 'medium';
  if (score >= 20) return 'low';
  return 'safe';
}

// ─── Helpers to map backend → frontend types ─────────────────────────────────

function mapEventType(et: string): FileOperation {
  const map: Record<string, FileOperation> = {
    created: 'CREATE',
    modified: 'MODIFY',
    deleted: 'DELETE',
    renamed: 'RENAME',
    moved: 'RENAME',
    closed: 'READ',
    opened: 'READ',
  };
  return map[et?.toLowerCase()] ?? 'MODIFY';
}

function mapThreatLevel(level: string): ThreatLevel {
  const levels: ThreatLevel[] = ['critical', 'high', 'medium', 'low', 'safe'];
  return levels.includes(level as ThreatLevel) ? (level as ThreatLevel) : 'safe';
}

function mapProcessStatus(suspicious: boolean): ProcessStatus {
  return suspicious ? 'suspicious' : 'running';
}

// ─── Default/Fallback data (used until backend responds) ──────────────────────

const DEFAULT_METRICS: SystemMetrics = {
  cpu: 0, memory: 0, disk: 0,
  activeProcesses: 0, filesModified: 0,
  threatScore: 0, networkIn: 0, networkOut: 0,
  uptime: '—', protectedFiles: 0,
};

const DEFAULT_SETTINGS: Settings = {
  monitoringEnabled: true, threshold: 65,
  autoKill: false, emailAlerts: true,
  backupFolder: 'C:\\RansomGuard\\Backup',
  darkMode: true, alertEmail: 'admin@company.com',
  scanInterval: 5, quarantineEnabled: true,
  reportSchedule: 'daily',
};

// ─── Provider ────────────────────────────────────────────────────────────────

export const AppProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [systemMetrics, setSystemMetrics] = useState<SystemMetrics>(DEFAULT_METRICS);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [monitoringData, setMonitoringData] = useState<MonitoringEntry[]>([]);
  const [processes, setProcesses] = useState<ProcessEntry[]>([]);
  const [isMonitoring, setIsMonitoring] = useState(true);
  const [settings, setSettings] = useState<Settings>(DEFAULT_SETTINGS);
  const [mlStatus, setMlStatus] = useState<MLStatus>({ available: false, model_name: null, feature_count: 0, error: null });
  const [backendOnline, setBackendOnline] = useState(false);

  const threatLevel = getThreatLevel(systemMetrics.threatScore);

  // ── Fetch system metrics ──────────────────────────────────────────────────
  const fetchSystemMetrics = useCallback(async () => {
    try {
      const [sysRes, cpuRes, memRes, diskRes] = await Promise.all([
        systemApi.getSystem(),
        systemApi.getCpu(),
        systemApi.getMemory(),
        systemApi.getDisk(),
      ]);

      const sys = sysRes.data?.data ?? {};
      const cpu = cpuRes.data?.data ?? {};
      const mem = memRes.data?.data ?? {};
      const disk = diskRes.data?.data ?? {};

      setBackendOnline(true);
      setSystemMetrics(prev => ({
        ...prev,
        cpu: cpu.cpu_percent ?? cpu.percent ?? sys.cpu?.percent ?? prev.cpu,
        memory: mem.percent ?? sys.memory?.percent ?? prev.memory,
        disk: disk.percent ?? (disk.partitions?.[0]?.percent) ?? sys.disk?.percent ?? prev.disk,
        activeProcesses: sys.processes?.total ?? prev.activeProcesses,
        networkIn: sys.network?.bytes_recv_mb ?? prev.networkIn,
        networkOut: sys.network?.bytes_sent_mb ?? prev.networkOut,
        uptime: sys.uptime ?? prev.uptime,
        filesModified: prev.filesModified,
        threatScore: prev.threatScore,
        protectedFiles: prev.protectedFiles,
      }));
    } catch {
      setBackendOnline(false);
    }
  }, []);

  // ── Fetch file events ─────────────────────────────────────────────────────
  const fetchFileEvents = useCallback(async () => {
    try {
      const res = await monitoringApi.getFileEvents({ limit: 100, page: 1 });
      const events: unknown[] = res.data?.data?.events ?? res.data?.data ?? [];
      if (!Array.isArray(events) || events.length === 0) return;

      const mapped: MonitoringEntry[] = (events as Record<string, unknown>[]).map((e) => ({
        id: (e.event_id as string) ?? crypto.randomUUID(),
        timestamp: new Date((e.timestamp as string) ?? Date.now()),
        fileName: (e.file_name as string) ?? String((e.path as string ?? '').split(/[\\/]/).pop() ?? 'unknown'),
        operation: mapEventType((e.event_type as string) ?? ''),
        path: (e.path as string) ?? '',
        process: (e.process_name as string) ?? 'system',
        pid: (e.pid as number) ?? 0,
        status: mapThreatLevel((e.threat_level as string) ?? 'safe'),
        size: e.file_size ? `${((e.file_size as number) / 1024).toFixed(1)} KB` : undefined,
      }));

      setMonitoringData(mapped);

      // Derive new alerts from high/critical events
      const newAlerts = mapped
        .filter(e => e.status === 'critical' || e.status === 'high')
        .slice(0, 10)
        .map(e => ({
          id: e.id,
          type: e.status,
          message: e.status === 'critical'
            ? `Critical: ${e.operation} on ${e.fileName} by ${e.process}`
            : `Suspicious ${e.operation} detected: ${e.fileName}`,
          process: e.process,
          timestamp: e.timestamp,
          path: e.path,
          resolved: false,
        }));

      if (newAlerts.length > 0) {
        setAlerts(prev => {
          const existingIds = new Set(prev.map(a => a.id));
          const fresh = newAlerts.filter(a => !existingIds.has(a.id));
          return fresh.length > 0 ? [...fresh, ...prev].slice(0, 50) : prev;
        });
      }

      // Update threat score from monitoring data
      const critCount = mapped.filter(e => e.status === 'critical').length;
      const highCount = mapped.filter(e => e.status === 'high').length;
      const score = Math.min(100, critCount * 15 + highCount * 5);
      if (score > 0) {
        setSystemMetrics(prev => ({ ...prev, threatScore: Math.max(prev.threatScore, score) }));
      }
    } catch {
      // silently ignore — backend may not have events yet
    }
  }, []);

  // ── Fetch processes ───────────────────────────────────────────────────────
  const fetchProcesses = useCallback(async () => {
    try {
      const res = await systemApi.getProcesses({ limit: 100, sort_by: 'cpu_percent' });
      const procs: unknown[] = res.data?.data?.processes ?? res.data?.data ?? [];
      if (!Array.isArray(procs) || procs.length === 0) return;

      const mapped: ProcessEntry[] = (procs as Record<string, unknown>[]).map((p) => ({
        pid: (p.pid as number) ?? 0,
        name: (p.name as string) ?? 'unknown',
        cpu: (p.cpu_percent as number) ?? 0,
        ram: ((p.memory_mb as number) ?? ((p.memory_percent as number) ?? 0) * 160),
        riskScore: (p.risk_score as number) ?? 0,
        status: mapProcessStatus(!!(p.suspicious as boolean)),
        path: (p.exe as string) ?? (p.path as string) ?? '',
        user: (p.username as string) ?? 'system',
        startTime: (p.create_time as string) ?? '',
      }));

      setProcesses(mapped);
      setSystemMetrics(prev => ({ ...prev, activeProcesses: mapped.length }));
    } catch {
      // silently ignore
    }
  }, []);

  // ── Fetch threats ─────────────────────────────────────────────────────────
  const fetchThreats = useCallback(async () => {
    try {
      const [threatsRes, summaryRes] = await Promise.all([
        threatApi.getThreats({ limit: 50 }),
        threatApi.getSummary(),
      ]);

      const threats: unknown[] = threatsRes.data?.data?.threats ?? threatsRes.data?.data ?? [];
      const summary = summaryRes.data?.data ?? {};

      if (Array.isArray(threats) && threats.length > 0) {
        const threatAlerts: Alert[] = (threats as Record<string, unknown>[]).map(t => ({
          id: (t.prediction_id as string) ?? (t._id as string) ?? crypto.randomUUID(),
          type: mapThreatLevel((t.threat_level as string) ?? 'safe'),
          message: ((t.indicators as string[]) ?? [])[0] ?? `${t.threat_level} threat on ${t.file_name}`,
          process: (t.process_name as string) ?? 'unknown',
          timestamp: new Date((t.timestamp as string) ?? Date.now()),
          path: (t.file_path as string) ?? '',
          resolved: (t.status as string) === 'resolved',
        }));

        setAlerts(prev => {
          const existingIds = new Set(prev.map(a => a.id));
          const fresh = threatAlerts.filter(a => !existingIds.has(a.id));
          return fresh.length > 0 ? [...fresh, ...prev].slice(0, 50) : prev;
        });
      }

      // Update threat metrics from summary
      if (summary.total_threats !== undefined) {
        setSystemMetrics(prev => ({
          ...prev,
          filesModified: (summary.total_threats as number) ?? prev.filesModified,
          threatScore: Math.min(100,
            ((summary.critical_count as number) ?? 0) * 20 +
            ((summary.high_count as number) ?? 0) * 10 +
            ((summary.medium_count as number) ?? 0) * 3
          ) || prev.threatScore,
        }));
      }
    } catch {
      // silently ignore
    }
  }, []);

  // ── Fetch ML status ───────────────────────────────────────────────────────
  const fetchMlStatus = useCallback(async () => {
    try {
      const res = await mlApi.getStatus();
      const d = res.data?.data ?? {};
      setMlStatus({
        available: d.available ?? false,
        model_name: d.model_name ?? null,
        feature_count: d.feature_count ?? 0,
        error: d.error ?? null,
      });
    } catch {
      setMlStatus(prev => ({ ...prev, available: false }));
    }
  }, []);

  // ── Master refresh ────────────────────────────────────────────────────────
  const refreshAll = useCallback(() => {
    fetchSystemMetrics();
    fetchFileEvents();
    fetchProcesses();
    fetchThreats();
    fetchMlStatus();
  }, [fetchSystemMetrics, fetchFileEvents, fetchProcesses, fetchThreats, fetchMlStatus]);

  // ── Initial load + polling ────────────────────────────────────────────────
  useEffect(() => {
    refreshAll();
  }, [refreshAll]);

  // System metrics + ML status every 5s
  useEffect(() => {
    if (!isMonitoring) return;
    const id = setInterval(() => {
      fetchSystemMetrics();
      fetchMlStatus();
    }, 5000);
    return () => clearInterval(id);
  }, [isMonitoring, fetchSystemMetrics, fetchMlStatus]);

  // File events + processes every 8s
  useEffect(() => {
    if (!isMonitoring) return;
    const id = setInterval(() => {
      fetchFileEvents();
      fetchProcesses();
    }, 8000);
    return () => clearInterval(id);
  }, [isMonitoring, fetchFileEvents, fetchProcesses]);

  // Threats every 15s
  useEffect(() => {
    if (!isMonitoring) return;
    const id = setInterval(() => {
      fetchThreats();
    }, 15000);
    return () => clearInterval(id);
  }, [isMonitoring, fetchThreats]);

  // ── Action handlers ───────────────────────────────────────────────────────
  const updateSettings = useCallback((s: Partial<Settings>) => {
    setSettings(prev => ({ ...prev, ...s }));
  }, []);

  const dismissAlert = useCallback((id: string) => {
    setAlerts(prev => prev.map(a => a.id === id ? { ...a, resolved: true } : a));
  }, []);

  const terminateProcess = useCallback((pid: number) => {
    setProcesses(prev =>
      prev.map(p => p.pid === pid ? { ...p, status: 'terminated' as ProcessStatus, cpu: 0, riskScore: 0 } : p)
    );
  }, []);

  const toggleMonitoring = useCallback(() => {
    setIsMonitoring(prev => !prev);
  }, []);

  const addAlert = useCallback((alert: Omit<Alert, 'id' | 'timestamp'>) => {
    setAlerts(prev => [{ ...alert, id: crypto.randomUUID(), timestamp: new Date() }, ...prev]);
  }, []);

  return (
    <AppContext.Provider value={{
      systemMetrics, alerts, monitoringData, processes,
      settings, isMonitoring, threatLevel, mlStatus, backendOnline,
      updateSettings, dismissAlert, terminateProcess,
      toggleMonitoring, addAlert, refreshAll,
    }}>
      {children}
    </AppContext.Provider>
  );
};
