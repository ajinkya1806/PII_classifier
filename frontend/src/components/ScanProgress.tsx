import { useEffect, useState } from 'react';
import { api } from '../api';
import type { JobStatus } from '../api';

interface Props {
  jobId: string;
  onComplete: () => void;
}

export default function ScanProgress({ jobId, onComplete }: Props) {
  const [status, setStatus] = useState<JobStatus | null>(null);
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    if (!jobId) return;

    const interval = setInterval(async () => {
      try {
        const s = await api.getScanStatus(jobId);
        setStatus(s);
        if (s.status === 'completed' || s.status === 'failed') {
          clearInterval(interval);
          if (s.status === 'completed') {
            setTimeout(onComplete, 800);
          }
        }
      } catch {
        // Ignore polling errors
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [jobId, onComplete]);

  useEffect(() => {
    const timer = setInterval(() => setElapsed((e) => e + 1), 1000);
    return () => clearInterval(timer);
  }, []);

  const progress = status
    ? status.total_fields > 0
      ? Math.round((status.scanned_fields / status.total_fields) * 100)
      : 0
    : 0;

  const formatTime = (s: number) => {
    const m = Math.floor(s / 60);
    const sec = s % 60;
    return m > 0 ? `${m}m ${sec}s` : `${sec}s`;
  };

  return (
    <div className="max-w-2xl mx-auto animate-slide-up">
      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold text-white">Scanning Database</h2>
        <p className="text-gray-400 mt-2">
          Analyzing columns for sensitive data patterns
        </p>
      </div>

      <div className="glass-card p-8">
        {/* Animated shield icon */}
        <div className="flex justify-center mb-8">
          <div className="relative">
            <div className="w-24 h-24 rounded-full bg-brand-600/10 flex items-center justify-center">
              <div className="w-16 h-16 rounded-full bg-brand-600/20 flex items-center justify-center animate-pulse-slow">
                <svg className="w-8 h-8 text-brand-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
                </svg>
              </div>
            </div>
            {status?.status === 'running' && (
              <div className="absolute inset-0 rounded-full border-2 border-brand-500/30 border-t-brand-500 animate-spin" />
            )}
          </div>
        </div>

        {/* Progress bar */}
        <div className="mb-6">
          <div className="flex justify-between text-sm mb-2">
            <span className="text-gray-400">Progress</span>
            <span className="text-white font-semibold">{progress}%</span>
          </div>
          <div className="h-3 bg-gray-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-brand-600 to-purple-500 rounded-full transition-all duration-500 ease-out relative"
              style={{ width: `${progress}%` }}
            >
              <div className="absolute inset-0 progress-shimmer rounded-full" />
            </div>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-3 gap-4">
          <div className="text-center p-3 rounded-xl bg-gray-800/40">
            <div className="text-2xl font-bold text-white">
              {status?.scanned_fields ?? 0}
            </div>
            <div className="text-xs text-gray-500 mt-1">Fields Scanned</div>
          </div>
          <div className="text-center p-3 rounded-xl bg-gray-800/40">
            <div className="text-2xl font-bold text-white">
              {status?.total_fields ?? 0}
            </div>
            <div className="text-xs text-gray-500 mt-1">Total Fields</div>
          </div>
          <div className="text-center p-3 rounded-xl bg-gray-800/40">
            <div className="text-2xl font-bold text-white">
              {formatTime(elapsed)}
            </div>
            <div className="text-xs text-gray-500 mt-1">Elapsed</div>
          </div>
        </div>

        {/* Status message */}
        {status?.status === 'failed' && (
          <div className="mt-6 p-3 rounded-xl bg-red-500/10 text-red-400 border border-red-500/20 text-sm animate-fade-in">
            ✗ Scan failed: {status.error_message || 'Unknown error'}
          </div>
        )}

        {status?.status === 'completed' && (
          <div className="mt-6 p-3 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-sm animate-fade-in">
            ✓ Scan completed! Loading results...
          </div>
        )}
      </div>
    </div>
  );
}
