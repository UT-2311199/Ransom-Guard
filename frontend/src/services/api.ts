import axios from 'axios';

const BASE_URL = 'http://localhost:8000';

export const api = axios.create({
  baseURL: BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('rg_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor — unwrap { success, data } envelope
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.warn('[RansomGuard API]', error?.response?.status, error.message);
    return Promise.reject(error);
  }
);

// ─── System ──────────────────────────────────────────────────────────────────
export const systemApi = {
  /** GET /api/v1/system → { cpu, memory, disk, network, uptime, ... } */
  getSystem: () => api.get('/api/v1/system'),
  getCpu: () => api.get('/api/v1/cpu'),
  getMemory: () => api.get('/api/v1/memory'),
  getDisk: () => api.get('/api/v1/disk'),
  /** GET /api/v1/processes */
  getProcesses: (params?: { limit?: number; sort_by?: string; suspicious_only?: boolean }) =>
    api.get('/api/v1/processes', { params }),
};

// ─── Monitor ─────────────────────────────────────────────────────────────────
export const monitoringApi = {
  /** GET /api/v1/monitor/files */
  getFileEvents: (params?: { limit?: number; event_type?: string; page?: number }) =>
    api.get('/api/v1/monitor/files', { params }),
  /** GET /api/v1/monitor/status */
  getMonitorStatus: () => api.get('/api/v1/monitor/status'),
};

// ─── Prediction ──────────────────────────────────────────────────────────────
export const predictionApi = {
  /** POST /api/v1/predict */
  predict: (data: {
    file_path: string;
    file_name?: string;
    file_extension?: string;
    file_size?: number;
    entropy?: number;
    process_name?: string;
    process_id?: number;
    event_type?: string;
    rapid_changes?: number;
    extensions_modified?: string[];
    suspicious_keywords?: string[];
  }) => api.post('/api/v1/predict', data),

  /** POST /api/v1/terminate */
  terminateProcess: (pid: number, reason?: string, force?: boolean) =>
    api.post('/api/v1/terminate', { pid, reason: reason ?? 'User requested termination', force: force ?? false }),

  /** POST /api/v1/quarantine */
  quarantineFile: (file_path: string, threat_id?: string, reason?: string) =>
    api.post('/api/v1/quarantine', { file_path, threat_id, reason: reason ?? 'User requested quarantine' }),
};

// ─── ML ──────────────────────────────────────────────────────────────────────
export const mlApi = {
  /** GET /api/v1/ml/status */
  getStatus: () => api.get('/api/v1/ml/status'),

  /** POST /api/v1/ml/predict-features */
  predictFeatures: (features: {
    files_modified_per_sec?: number;
    files_created?: number;
    files_deleted?: number;
    rename_operations?: number;
    read_operations?: number;
    write_operations?: number;
    entropy?: number;
    cpu_usage?: number;
    memory_usage?: number;
    disk_io?: number;
    extension_changes?: number;
    directories_accessed?: number;
    encryption_ratio?: number;
  }) => api.post('/api/v1/ml/predict-features', features),
};

// ─── Threats ─────────────────────────────────────────────────────────────────
export const threatApi = {
  /** GET /api/v1/threats */
  getThreats: (params?: {
    limit?: number;
    skip?: number;
    status?: string;
    threat_level?: string;
  }) => api.get('/api/v1/threats', { params }),

  /** GET /api/v1/threats/summary */
  getSummary: () => api.get('/api/v1/threats/summary'),

  /** PUT /api/v1/threats/status */
  updateStatus: (threat_id: string, status: string, notes?: string) =>
    api.put('/api/v1/threats/status', { threat_id, status, notes }),
};

// ─── Analytics ───────────────────────────────────────────────────────────────
export const analyticsApi = {
  /** GET /api/v1/analytics */
  getAnalytics: () => api.get('/api/v1/analytics'),
};

// ─── Reports ─────────────────────────────────────────────────────────────────
export const reportsApi = {
  /** GET /api/v1/reports */
  getReports: (params?: { limit?: number; skip?: number }) =>
    api.get('/api/v1/reports', { params }),

  /** POST /api/v1/reports */
  generateReport: (params: {
    report_type: 'threat_summary' | 'incident_report' | 'system_status' | 'full_audit';
    format: 'pdf' | 'csv' | 'json';
    start_date?: string;
    end_date?: string;
    include_system_info?: boolean;
    include_threats?: boolean;
    title?: string;
  }) => api.post('/api/v1/reports', params),

  /** GET /api/v1/reports/{id}/download */
  downloadReport: (report_id: string) =>
    api.get(`/api/v1/reports/${report_id}/download`, { responseType: 'blob' }),
};

// ─── Settings ────────────────────────────────────────────────────────────────
export const settingsApi = {
  /** GET /api/v1/settings */
  getSettings: () => api.get('/api/v1/settings'),

  /** POST /api/v1/settings */
  updateSettings: (settings: Record<string, unknown>) =>
    api.post('/api/v1/settings', settings),

  /** DELETE /api/v1/settings/reset */
  resetSettings: () => api.delete('/api/v1/settings/reset'),
};

export default api;
