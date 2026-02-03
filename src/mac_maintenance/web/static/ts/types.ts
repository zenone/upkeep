/**
 * Re-export all API types for use in frontend TypeScript code
 */
export * from '../../../../../types/api';

// Extended Schedule type with frontend-specific fields
import type { Schedule as BaseSchedule } from '../../../../../types/api';

export interface Schedule extends BaseSchedule {
  // API may return extra UI-only fields
  message?: string;
}

// Additional frontend-specific types
export interface SparklineData {
  cpu: number[];
  memory: number[];
  disk: number[];
  timestamps: string[];
}

export interface PreviousMetrics {
  cpu: number | null;
  memory: number | null;
  disk: number | null;
}

export interface SystemInfoData {
  system: {
    os: string;
    os_version: string;
    hostname: string;
    architecture: string;
    python_version: string;
    uptime_seconds: number;
    uptime_formatted: string;
    boot_time: string;
    username: string;
  };
  cpu: {
    percent: number;
    count: number;
    history: number[];
  };
  memory: {
    percent: number;
    available_gb: number;
    used_gb: number;
    total_gb: number;
    history: number[];
  };
  disk: {
    percent: number;
    free_gb: number;
    total_gb: number;
    used_gb: number;
    history: number[];
  };
  network: {
    upload_mbps: number;
    download_mbps: number;
    total_sent_gb: number;
    total_recv_gb: number;
  };
  swap: {
    total_gb: number;
    used_gb: number;
    free_gb: number;
    percent: number;
  };
}

export interface HealthScoreData {
  score: number;
  grade: string;
  factors: Array<{
    name: string;
    score: number;
    weight: number;
    status: string;
  }>;
}
