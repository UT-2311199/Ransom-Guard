import { format, subHours, subDays, subMinutes } from 'date-fns';

// ─── Time Series ──────────────────────────────────────────────────────────────
export function generateCpuHistory(points = 60, seed = 35) {
  let cpu = seed;
  return Array.from({ length: points }, (_, i) => {
    cpu = Math.max(5, Math.min(95, cpu + (Math.random() - 0.45) * 10));
    return {
      time: format(subMinutes(new Date(), points - i), 'HH:mm'),
      cpu: parseFloat(cpu.toFixed(1)),
    };
  });
}

export function generateMemoryHistory(points = 60, seed = 60) {
  let mem = seed;
  return Array.from({ length: points }, (_, i) => {
    mem = Math.max(20, Math.min(90, mem + (Math.random() - 0.48) * 5));
    return {
      time: format(subMinutes(new Date(), points - i), 'HH:mm'),
      memory: parseFloat(mem.toFixed(1)),
    };
  });
}

export function generateNetworkHistory(points = 60) {
  let inbound = 10;
  let outbound = 3;
  return Array.from({ length: points }, (_, i) => {
    inbound = Math.max(0, inbound + (Math.random() - 0.4) * 5);
    outbound = Math.max(0, outbound + (Math.random() - 0.4) * 2);
    return {
      time: format(subMinutes(new Date(), points - i), 'HH:mm'),
      inbound: parseFloat(inbound.toFixed(1)),
      outbound: parseFloat(outbound.toFixed(1)),
    };
  });
}

export function generateThreatsOverTime(range: '1h' | '24h' | '7d' | '30d' = '24h') {
  const configs = {
    '1h': { points: 12, interval: 5, unit: 'min', fn: (i: number, total: number) => subMinutes(new Date(), (total - i) * 5) },
    '24h': { points: 24, interval: 1, unit: 'h', fn: (i: number, total: number) => subHours(new Date(), total - i) },
    '7d': { points: 7, interval: 1, unit: 'd', fn: (i: number, total: number) => subDays(new Date(), total - i) },
    '30d': { points: 30, interval: 1, unit: 'd', fn: (i: number, total: number) => subDays(new Date(), total - i) },
  };
  const { points, fn } = configs[range];
  const fmtMap = { '1h': 'HH:mm', '24h': 'HH:00', '7d': 'EEE', '30d': 'MMM dd' };
  const fmt = fmtMap[range];
  return Array.from({ length: points }, (_, i) => ({
    time: format(fn(i, points), fmt),
    critical: Math.floor(Math.random() * 5),
    high: Math.floor(Math.random() * 12),
    medium: Math.floor(Math.random() * 20),
    low: Math.floor(Math.random() * 35),
  }));
}

// ─── Risk Distribution ────────────────────────────────────────────────────────
export const riskDistribution = [
  { name: 'Critical', value: 8, color: '#EF4444' },
  { name: 'High', value: 15, color: '#F97316' },
  { name: 'Medium', value: 27, color: '#F59E0B' },
  { name: 'Low', value: 34, color: '#3B82F6' },
  { name: 'Safe', value: 16, color: '#10B981' },
];

// ─── Threat History ───────────────────────────────────────────────────────────
export interface ThreatHistoryItem {
  id: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  threat: string;
  process: string;
  path: string;
  date: Date;
  status: 'blocked' | 'quarantined' | 'resolved' | 'active';
  details: string;
  filesAffected: number;
  mlScore: number;
  attackType: string;
}

export const threatHistory: ThreatHistoryItem[] = [
  {
    id: '1',
    severity: 'critical',
    threat: 'WannaCry Variant',
    process: 'ransomware_sample.exe',
    path: 'C:\\Users\\Admin\\Downloads\\ransomware_sample.exe',
    date: new Date(Date.now() - 120000),
    status: 'blocked',
    details: 'ML model detected WannaCry-like encryption pattern with 98.7% confidence. Process attempted to encrypt 1,247 files across 34 directories before being blocked.',
    filesAffected: 1247,
    mlScore: 98.7,
    attackType: 'Crypto Ransomware',
  },
  {
    id: '2',
    severity: 'critical',
    threat: 'Shadow Copy Deletion',
    process: 'shadow_copy.exe',
    path: 'C:\\Users\\Admin\\AppData\\Roaming\\shadow_copy.exe',
    date: new Date(Date.now() - 3600000),
    status: 'quarantined',
    details: 'Process attempted to delete all volume shadow copies using vssadmin. This is a common ransomware evasion technique to prevent file recovery.',
    filesAffected: 0,
    mlScore: 94.2,
    attackType: 'Defense Evasion',
  },
  {
    id: '3',
    severity: 'high',
    threat: 'Mass File Encryption',
    process: 'encrypt_tool.exe',
    path: 'C:\\Users\\Admin\\AppData\\Local\\Temp\\encrypt_tool.exe',
    date: new Date(Date.now() - 7200000),
    status: 'blocked',
    details: 'Anomalous encryption activity detected: 847 files encrypted in 45 seconds. Behavior matches known Locky ransomware signature.',
    filesAffected: 847,
    mlScore: 89.3,
    attackType: 'Locker Ransomware',
  },
  {
    id: '4',
    severity: 'high',
    threat: 'PowerShell Obfuscation',
    process: 'powershell.exe',
    path: 'C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe',
    date: new Date(Date.now() - 86400000),
    status: 'resolved',
    details: 'PowerShell executing base64-encoded commands detected. Script downloaded secondary payload from remote C2 server.',
    filesAffected: 12,
    mlScore: 76.5,
    attackType: 'Script-based Attack',
  },
  {
    id: '5',
    severity: 'medium',
    threat: 'Suspicious File Access Pattern',
    process: 'python.exe',
    path: 'C:\\Python311\\python.exe',
    date: new Date(Date.now() - 172800000),
    status: 'resolved',
    details: 'Unusual file access pattern detected: script accessing 500+ files per minute with systematic read operations.',
    filesAffected: 523,
    mlScore: 62.8,
    attackType: 'Data Exfiltration',
  },
  {
    id: '6',
    severity: 'medium',
    threat: 'Registry Modification',
    process: 'reg.exe',
    path: 'C:\\Windows\\System32\\reg.exe',
    date: new Date(Date.now() - 259200000),
    status: 'resolved',
    details: 'Suspicious registry modification detected in HKLM\\Software\\Microsoft\\Windows\\CurrentVersion\\Run. Possible persistence mechanism.',
    filesAffected: 3,
    mlScore: 55.4,
    attackType: 'Persistence',
  },
  {
    id: '7',
    severity: 'low',
    threat: 'Unusual Process Spawn',
    process: 'chrome.exe',
    path: 'C:\\Program Files\\Google\\Chrome\\chrome.exe',
    date: new Date(Date.now() - 345600000),
    status: 'resolved',
    details: 'Browser spawned cmd.exe with unusual arguments. Possible drive-by download attempt.',
    filesAffected: 1,
    mlScore: 34.2,
    attackType: 'Browser Exploit',
  },
  {
    id: '8',
    severity: 'low',
    threat: 'Network Port Scan',
    process: 'nmap.exe',
    path: 'C:\\Tools\\nmap\\nmap.exe',
    date: new Date(Date.now() - 432000000),
    status: 'resolved',
    details: 'Internal network scanning detected from workstation. May indicate lateral movement preparation.',
    filesAffected: 0,
    mlScore: 28.7,
    attackType: 'Reconnaissance',
  },
];

// ─── Feature Importance ───────────────────────────────────────────────────────
export const featureImportanceData = [
  { feature: 'File Encryption Rate', importance: 0.285, description: 'Rate of file encryption operations per second' },
  { feature: 'Entropy Change', importance: 0.223, description: 'Change in file entropy indicating encryption' },
  { feature: 'File Extension Rename', importance: 0.178, description: 'Mass renaming to unknown extensions' },
  { feature: 'Shadow Copy Deletion', importance: 0.134, description: 'Attempts to delete backup shadow copies' },
  { feature: 'Registry Modification', importance: 0.089, description: 'Suspicious registry key changes' },
  { feature: 'Network C2 Contact', importance: 0.056, description: 'Contact with known C2 servers' },
  { feature: 'Process Injection', importance: 0.035, description: 'Code injection into other processes' },
];

// ─── Heatmap Data ─────────────────────────────────────────────────────────────
export function generateHeatmapData() {
  const hours = Array.from({ length: 24 }, (_, i) => i);
  const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
  return days.flatMap(day =>
    hours.map(hour => ({
      day,
      hour: `${hour.toString().padStart(2, '0')}:00`,
      value: Math.floor(Math.random() * 100),
    }))
  );
}

// ─── Reports Mock ─────────────────────────────────────────────────────────────
export const reportSummary = {
  totalThreats: 1847,
  criticalThreats: 23,
  highThreats: 89,
  mediumThreats: 234,
  lowThreats: 1501,
  blockedAttacks: 1801,
  quarantinedFiles: 156,
  systemsProtected: 1,
  avgResponseTime: '1.2s',
  mlAccuracy: '97.3%',
  falsePositiveRate: '0.8%',
  uptime: '99.97%',
  lastScanTime: new Date(),
  reportPeriod: '30 days',
};

// ─── Analytics Summary ────────────────────────────────────────────────────────
export const attackTypeData = [
  { name: 'Crypto Ransomware', count: 45, color: '#EF4444' },
  { name: 'Locker Ransomware', count: 23, color: '#F97316' },
  { name: 'Data Exfiltration', count: 67, color: '#F59E0B' },
  { name: 'Script-based', count: 89, color: '#8B5CF6' },
  { name: 'Browser Exploit', count: 34, color: '#3B82F6' },
  { name: 'Persistence', count: 12, color: '#10B981' },
];

export const weeklyStats = [
  { day: 'Mon', threats: 12, blocked: 11, resolved: 1 },
  { day: 'Tue', threats: 8, blocked: 8, resolved: 0 },
  { day: 'Wed', threats: 23, blocked: 21, resolved: 2 },
  { day: 'Thu', threats: 15, blocked: 15, resolved: 0 },
  { day: 'Fri', threats: 31, blocked: 28, resolved: 3 },
  { day: 'Sat', threats: 6, blocked: 6, resolved: 0 },
  { day: 'Sun', threats: 4, blocked: 4, resolved: 0 },
];
