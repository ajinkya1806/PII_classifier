/**
 * API client for the PII Classifier backend.
 */

const API_BASE = 'http://localhost:8000';

export interface ConnectionInfo {
  host: string;
  port: number;
  user: string;
  password: string;
  database: string;
}

export interface SchemaColumn {
  name: string;
  data_type: string;
  nullable: boolean;
}

export interface SchemaTable {
  table_name: string;
  columns: SchemaColumn[];
}

export interface ScanResult {
  id?: string;
  table: string;
  column: string;
  subtype: string;
  category: string;
  regulation: string;
  confidence: number;
  matched_by: string[];
  description: string;
  rule_confidence?: number;
  pattern_confidence?: number;
  llm_confidence?: number;
  llm_justification?: string;
}

export interface JobStatus {
  id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  total_fields: number;
  scanned_fields: number;
  created_at: string;
  updated_at: string;
  error_message?: string;
}

export interface Job {
  id: string;
  connection_info: Record<string, string>;
  status: string;
  created_at: string;
  updated_at: string;
  total_fields: number;
  scanned_fields: number;
  error_message?: string;
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Request failed: ${res.status}`);
  }
  return res.json();
}

export const api = {
  /** Test MySQL connection */
  testConnection: (conn: ConnectionInfo) =>
    request<{ success: boolean; message: string }>('/connections/test', {
      method: 'POST',
      body: JSON.stringify(conn),
    }),

  /** Get schema (tables + columns) */
  getSchema: (conn: ConnectionInfo) =>
    request<SchemaTable[]>('/connections/schema', {
      method: 'POST',
      body: JSON.stringify(conn),
    }),

  /** Start a scan */
  startScan: (conn: ConnectionInfo & { tables?: string[] }) =>
    request<{ job_id: string; message: string }>('/scan', {
      method: 'POST',
      body: JSON.stringify(conn),
    }),

  /** Get scan status */
  getScanStatus: (jobId: string) =>
    request<JobStatus>(`/scan/${jobId}`),

  /** Get scan results */
  getScanResults: (jobId: string) =>
    request<{ job_id: string; status: string; total_fields: number; results: ScanResult[] }>(
      `/scan/${jobId}/results`
    ),

  /** Export results */
  exportResults: async (jobId: string, format: 'json' | 'csv' = 'json') => {
    const res = await fetch(`${API_BASE}/scan/${jobId}/export?format=${format}`);
    if (!res.ok) throw new Error('Export failed');
    if (format === 'csv') {
      return res.text();
    }
    return res.json();
  },

  /** List all past jobs */
  listJobs: () =>
    request<{ jobs: Job[] }>('/jobs'),

  /** Health check */
  health: () =>
    request<{ status: string }>('/health'),
};
