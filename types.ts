
export enum UserRole {
  SUPER_ADMIN = 'SUPER_ADMIN',
  COMPANY_ADMIN = 'COMPANY_ADMIN',
  SECURITY_OFFICER = 'SECURITY_OFFICER',
  VIEWER = 'VIEWER'
}

export enum RiskLevel {
  NORMAL = 'NORMAL',
  ELEVATED = 'ELEVATED',
  HIGH = 'HIGH',
  CRITICAL = 'CRITICAL'
}

export enum AgentStatus {
  ONLINE = 'ONLINE',
  OFFLINE = 'OFFLINE',
  SUSPENDED = 'SUSPENDED',
  TAMPERED = 'TAMPERED',
  IDLE = 'IDLE'
}

/* Added MonitoringProfile interface used in Devices.tsx */
export interface MonitoringProfile {
  id: string;
  name: string;
  adaptiveLevel: RiskLevel;
  fileMonitoring: boolean;
  usbMonitoring: boolean;
  printMonitoring: boolean;
  printContentCapture: boolean;
  searchKeywordMonitoring: boolean;
  emailAiScan: boolean;
  idleTracking: boolean;
  behaviorAiStrictMode: boolean;
}

/* Added AuditLog interface used in mockBackend.ts */
export interface AuditLog {
  id: string;
  userId: string;
  action: string;
  resource: string;
  timestamp: string;
  ip: string;
}

export interface TenantConfig {
  id: string;
  name: string;
  plan: 'BASIC' | 'PRO' | 'ENTERPRISE';
  thresholds: {
    printLimit: number;
    riskDecayRate: number; // Percentage per day
    idleTimeout: number; // minutes
    criticalAlertLevel: number;
  };
  keywords: string[];
}

export interface Device {
  id: string;
  name: string;
  employeeName: string;
  department: string;
  os: string;
  status: AgentStatus;
  lastHeartbeat: string;
  riskScore: number;
  predictiveRiskScore: number;
  ipAddress: string;
  profileId: string;
  tenantId: string;
  agentVersion: string;
  peerDeviation: number;
  isTamperProtected: boolean;
  isTampered?: boolean; // Added for mock data compatibility
  workStats: {
    uptime: number;
    activeTime: number;
    idleTime: number;
    printCount: number;
    fileModCount: number;
    longestIdle?: number; // Added for mock data compatibility
  };
}

export interface SecurityEvent {
  id: string;
  deviceId: string;
  tenantId: string;
  timestamp: string;
  /* Expanded event types to include more specific forensic indicators used in the app */
  type: 'USB' | 'PRINT' | 'FILE' | 'NETWORK' | 'KEYWORD' | 'TAMPER' | 'USB_INSERT' | 'NETWORK_UPLOAD' | 'PROCESS_START' | 'PRINT_EVENT' | 'SEARCH_KEYWORD' | 'FILE_ACCESS' | 'EMAIL_PHISH';
  severity: RiskLevel;
  description: string;
  riskWeight: number;
  metadata: Record<string, any>;
}

export interface Command {
  id: string;
  deviceId: string;
  action: 'LOCK' | 'DISABLE_USB' | 'BLOCK_PROCESS' | 'UPDATE' | 'SCAN';
  /* Added RECEIVED status used in mockBackend.ts */
  status: 'PENDING' | 'SENT' | 'EXECUTED' | 'FAILED' | 'RECEIVED';
  issuedBy: string;
  signature: string;
  timestamp: string;
}

export interface AIAnalysis {
  summary: string;
  threatDetected: boolean;
  correlationChain: string[];
  recommendedActions: string[];
  behaviorScore: number;
  predictiveForecast: {
    probability7d: number;
    topRiskFactors: string[];
    timeToEscalation: string;
  };
}
